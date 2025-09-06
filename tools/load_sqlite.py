#!/usr/bin/env python3
"""
Load data/glyphs_merged.json into a local SQLite database (data/glyphs.db by default).

This uses only the standard library and the normalized list-based accessors in
src/ask/merged_glyphs.py for a predictable ingestion shape.

Usage:
  python tools/load_sqlite.py --db data/glyphs.db --source data/glyphs_merged.json

If no flags are provided, defaults are used.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import typer

from ask.core.db import get_connection, create_schema, DEFAULT_DB_PATH
from ask.merged_glyphs import get_merged_glyphs

app = typer.Typer(help="Load the merged glyph dataset into SQLite.")


def _coerce_json(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


@app.command()
def load(
    db: Path = typer.Option(DEFAULT_DB_PATH, "--db", help="Path to SQLite database file"),
    source: Path = typer.Option(
        Path(__file__).resolve().parents[1] / "data" / "glyphs_merged.json",
        "--source",
        help="Path to glyphs_merged.json",
    ),
):
    """Load the dataset into SQLite (overwrites existing contents)."""
    mg = get_merged_glyphs(source)

    conn = get_connection(db)
    create_schema(conn)

    cur = conn.cursor()

    # Wipe existing data to keep idempotent and simple for now
    tables = [
        "glyph_field_tag_contexts",
        "glyph_field_tags",
        "glyph_position_prefs",
        "glyph_cluster_behaviors",
        "glyph_fields",
        "enhanced_clusters",
        "cluster_ops",
        "clusters",
        "complete_operators",
        "operators",
        "payloads",
        "vowels",
        "tag_associations",
        "named_payloads",
    ]
    for t in tables:
        cur.execute(f"DELETE FROM {t};")

    # --- Vowels ---
    vowels = mg.vowels()
    cur.executemany("INSERT OR IGNORE INTO vowels(vowel) VALUES (?);", [(v,) for v in vowels])

    # --- Payloads (typed_payload_entries preferred; falls back to payload_entries if needed) ---
    typed_entries = mg.typed_payload_entries() or []
    if typed_entries:
        payload_rows = [
            (
                e.get("vowel"),
                e.get("type"),
                e.get("tag"),
                e.get("principle"),
                e.get("confidence"),
            )
            for e in typed_entries
        ]
    else:
        payload_entries = mg.payload_entries() or []
        payload_rows = [
            (
                e.get("vowel"),
                e.get("type"),
                e.get("tag"),
                e.get("principle"),
                None,
            )
            for e in payload_entries
        ]
    cur.executemany(
        """
        INSERT INTO payloads(vowel, type, tag, principle, confidence)
        VALUES (?, ?, ?, ?, ?);
        """,
        payload_rows,
    )

    # --- Operators ---
    for e in mg.operator_entries():
        glyph = e.get("glyph")
        op = e.get("value") or e.get("op")
        # operators may be referenced by complete_operators via FK; ensure presence
        cur.execute(
            "INSERT OR REPLACE INTO operators(glyph, op) VALUES (?, ?);",
            (glyph, op),
        )

    # --- Complete operators ---
    for e in mg.complete_operator_entries():
        glyph = e.get("glyph")
        op_from_complete = e.get("op") or (e.get("value") or {}).get("op")
        principle = e.get("principle")
        confidence = e.get("confidence")
        # Ensure an operator row exists even if operator_map didn't contain this glyph
        if glyph and op_from_complete:
            cur.execute(
                "INSERT OR IGNORE INTO operators(glyph, op) VALUES (?, ?);",
                (glyph, op_from_complete),
            )
        cur.execute(
            "INSERT OR REPLACE INTO complete_operators(glyph, principle, confidence) VALUES (?, ?, ?);",
            (glyph, principle, confidence),
        )

    # --- Clusters and ops ---
    for e in mg.cluster_entries():
        cluster = e.get("cluster")
        cur.execute("INSERT INTO clusters(cluster) VALUES (?);", (cluster,))
        ops = e.get("value") or []
        for op in ops:
            cur.execute(
                "INSERT INTO cluster_ops(cluster, op) VALUES (?, ?) ON CONFLICT DO NOTHING;",
                (cluster, op),
            )

    for e in mg.enhanced_cluster_entries():
        cluster = e.get("cluster")
        gloss = e.get("gloss")
        confidence = e.get("confidence")
        # ensure cluster exists
        cur.execute("INSERT OR IGNORE INTO clusters(cluster) VALUES (?);", (cluster,))
        cur.execute(
            "INSERT OR REPLACE INTO enhanced_clusters(cluster, gloss, confidence) VALUES (?, ?, ?);",
            (cluster, gloss, confidence),
        )
        # also load ops list if present
        for op in (e.get("ops") or []):
            cur.execute(
                "INSERT INTO cluster_ops(cluster, op) VALUES (?, ?) ON CONFLICT DO NOTHING;",
                (cluster, op),
            )

    # --- Fields ---
    for e in mg.field_entries():
        glyph = e.get("glyph")
        cur.execute("INSERT INTO glyph_fields(glyph) VALUES (?);", (glyph,))

        # tags
        for t in (e.get("tags") or []):
            tag = t.get("tag")
            t_conf = t.get("confidence")
            t_evidence = t.get("evidence_count")
            contexts = t.get("contexts") or []
            cur.execute(
                "INSERT INTO glyph_field_tags(glyph, tag, confidence, evidence_count) VALUES (?, ?, ?, ?);",
                (glyph, tag, t_conf, t_evidence),
            )
            for ctx in contexts or []:
                cur.execute(
                    "INSERT INTO glyph_field_tag_contexts(glyph, tag, context) VALUES (?, ?, ?) ON CONFLICT DO NOTHING;",
                    (glyph, tag, ctx),
                )

        # position preferences
        for p in (e.get("position_preferences") or []):
            position = p.get("position")
            name = p.get("name")
            score = p.get("score")
            cur.execute(
                "INSERT INTO glyph_position_prefs(glyph, position, name, score) VALUES (?, ?, ?, ?);",
                (glyph, position, name, score),
            )

        # cluster behaviors
        for cb in (e.get("cluster_behaviors") or []):
            cluster = cb.get("cluster")
            value = cb.get("value")
            cur.execute(
                "INSERT INTO glyph_cluster_behaviors(glyph, cluster, value) VALUES (?, ?, ?) ON CONFLICT(glyph, cluster) DO UPDATE SET value=excluded.value;",
                (glyph, cluster, value),
            )

    # --- Tag associations (store as JSON text per tag) ---
    unions: Dict[str, Any] = mg.merged_union()
    ta: Dict[str, Any] = unions.get("tag_associations") or {}
    for tag, obj in ta.items():
        cur.execute(
            "INSERT OR REPLACE INTO tag_associations(tag, value) VALUES (?, ?);",
            (tag, _coerce_json(obj)),
        )

    # --- Named payloads ---
    np: Dict[str, Any] = unions.get("named_payloads") or {}
    for name, body in np.items():
        cur.execute(
            """
            INSERT OR REPLACE INTO named_payloads(name, type, tag, principle, features, confidence)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (
                name,
                body.get("type"),
                body.get("tag"),
                body.get("principle"),
                _coerce_json(body.get("features")),
                body.get("confidence"),
            ),
        )

    conn.commit()

    # Simple verification output
    summary = {}
    for (label, query) in [
        ("vowels", "SELECT COUNT(*) AS c FROM vowels"),
        ("payloads", "SELECT COUNT(*) AS c FROM payloads"),
        ("operators", "SELECT COUNT(*) AS c FROM operators"),
        ("complete_operators", "SELECT COUNT(*) AS c FROM complete_operators"),
        ("clusters", "SELECT COUNT(*) AS c FROM clusters"),
        ("cluster_ops", "SELECT COUNT(*) AS c FROM cluster_ops"),
        ("glyph_fields", "SELECT COUNT(*) AS c FROM glyph_fields"),
        ("glyph_field_tags", "SELECT COUNT(*) AS c FROM glyph_field_tags"),
        ("glyph_position_prefs", "SELECT COUNT(*) AS c FROM glyph_position_prefs"),
        ("glyph_cluster_behaviors", "SELECT COUNT(*) AS c FROM glyph_cluster_behaviors"),
        ("tag_associations", "SELECT COUNT(*) AS c FROM tag_associations"),
        ("named_payloads", "SELECT COUNT(*) AS c FROM named_payloads"),
    ]:
        row = conn.execute(query).fetchone()
        summary[label] = row["c"] if row else 0

    typer.secho("Loaded SQLite with the following counts:", fg=typer.colors.GREEN)
    for k, v in summary.items():
        typer.echo(f" - {k}: {v}")


if __name__ == "__main__":
    app()

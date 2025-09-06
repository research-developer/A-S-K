#!/usr/bin/env python3
from __future__ import annotations

"""
Materialize cache artifacts from the SQLite DB into the .cache/ directory.

- Uses the DB as the atomic source of truth
- Writes derived JSON files that UIs and tools can read quickly

Usage:
  python tools/materialize_cache.py all --db data/glyphs.db --out .cache
  python tools/materialize_cache.py merged --db data/glyphs.db --out .cache
  python tools/materialize_cache.py counts --db data/glyphs.db --out .cache
"""

import json
from pathlib import Path
from typing import Any, Dict

import typer

from ask.core.db import get_connection, DEFAULT_DB_PATH
from ask.merged_glyphs_db import get_db_merged

app = typer.Typer(help="Materialize .cache/ artifacts from SQLite DB")


def _ensure_out_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    tmp.replace(path)


@app.command()
def merged(db: Path = typer.Option(DEFAULT_DB_PATH, "--db"), out: Path = typer.Option(Path(".cache"), "--out")):
    """Export the normalized lists to <out>/merged_lists.json."""
    _ensure_out_dir(out)
    mg = get_db_merged(db)
    payload: Dict[str, Any] = {
        "vowels": mg.vowels(),
        "payload_entries": mg.payload_entries(),
        "operator_entries": mg.operator_entries(),
        "complete_operator_entries": mg.complete_operator_entries(),
        "typed_payload_entries": mg.typed_payload_entries(),
        "cluster_entries": mg.cluster_entries(),
        "enhanced_cluster_entries": mg.enhanced_cluster_entries(),
        "field_entries": mg.field_entries(),
        "tag_association_entries": mg.tag_association_entries(),
    }
    _write_json(out / "merged_lists.json", payload)
    typer.secho(f"Wrote {out / 'merged_lists.json'}", fg=typer.colors.GREEN)


@app.command()
def counts(db: Path = typer.Option(DEFAULT_DB_PATH, "--db"), out: Path = typer.Option(Path(".cache"), "--out")):
    """Export simple table counts to <out>/db_counts.json."""
    _ensure_out_dir(out)
    conn = get_connection(db)
    summary: Dict[str, int] = {}
    for (label, query) in [
        ("vowels", "SELECT COUNT(*) AS c FROM vowels"),
        ("payloads", "SELECT COUNT(*) AS c FROM payloads"),
        ("operators", "SELECT COUNT(*) AS c FROM operators"),
        ("complete_operators", "SELECT COUNT(*) AS c FROM complete_operators"),
        ("clusters", "SELECT COUNT(*) AS c FROM clusters"),
        ("cluster_ops", "SELECT COUNT(*) AS c FROM cluster_ops"),
        ("glyph_fields", "SELECT COUNT(*) AS c FROM glyph_fields"),
        ("glyph_field_tags", "SELECT COUNT(*) AS c FROM glyph_field_tags"),
        ("glyph_field_tag_contexts", "SELECT COUNT(*) AS c FROM glyph_field_tag_contexts"),
        ("glyph_position_prefs", "SELECT COUNT(*) AS c FROM glyph_position_prefs"),
        ("glyph_cluster_behaviors", "SELECT COUNT(*) AS c FROM glyph_cluster_behaviors"),
        ("tag_associations", "SELECT COUNT(*) AS c FROM tag_associations"),
        ("named_payloads", "SELECT COUNT(*) AS c FROM named_payloads"),
    ]:
        row = conn.execute(query).fetchone()
        summary[label] = int(row[0] if row else 0)
    _write_json(out / "db_counts.json", summary)
    typer.secho(f"Wrote {out / 'db_counts.json'}", fg=typer.colors.GREEN)


@app.command()
def all(db: Path = typer.Option(DEFAULT_DB_PATH, "--db"), out: Path = typer.Option(Path(".cache"), "--out")):
    """Materialize all supported cache artifacts."""
    merged(db=db, out=out)
    counts(db=db, out=out)


if __name__ == "__main__":
    app()

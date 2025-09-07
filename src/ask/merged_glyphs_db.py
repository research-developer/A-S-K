from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

# Compute default DB path without importing ask.core to avoid circular imports
_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "glyphs.db"


class DBMergedGlyphs:
    """DB-backed provider that exposes the same list-returning API as MergedGlyphs.

    It reconstructs the normalized views from the SQLite schema so the rest of the
    codebase can treat the database as the single source of truth.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row

    # --- Normalized accessors (always lists) ---
    def vowels(self) -> List[str]:
        rows = self.conn.execute("SELECT vowel FROM vowels ORDER BY vowel").fetchall()
        return [r[0] for r in rows]

    def payload_entries(self) -> List[Dict[str, Any]]:
        # Non-typed fallback: emulate shape
        # Use lightweight connection here to avoid depending on ask.core
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT vowel, type, tag, principle, confidence FROM payloads ORDER BY vowel"
        ).fetchall()
        conn.close()
        return [
            {
                "vowel": r[0],
                "type": r[1],
                "tag": r[2],
                "principle": r[3],
                "confidence": r[4],
            }
            for r in rows
        ]

    def typed_payload_entries(self) -> List[Dict[str, Any]]:
        # In this schema, payloads is already typed; same as payload_entries
        return self.payload_entries()

    def operator_entries(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT glyph, op FROM operators").fetchall()
        return [{"glyph": r[0], "value": r[1]} for r in rows]

    def complete_operator_entries(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT co.glyph, o.op, co.principle, co.confidence
            FROM complete_operators co
            LEFT JOIN operators o ON o.glyph = co.glyph
            """
        ).fetchall()
        return [
            {
                "glyph": r[0],
                "op": r[1],
                "principle": r[2],
                "confidence": r[3],
            }
            for r in rows
        ]

    def cluster_entries(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT cluster FROM clusters ORDER BY cluster").fetchall()
        out: List[Dict[str, Any]] = []
        for (cluster,) in rows:
            ops_rows = self.conn.execute(
                "SELECT op FROM cluster_ops WHERE cluster = ? ORDER BY op",
                (cluster,),
            ).fetchall()
            out.append({"cluster": cluster, "value": [r[0] for r in ops_rows]})
        return out

    def enhanced_cluster_entries(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT cluster, gloss, confidence FROM enhanced_clusters ORDER BY cluster"
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for (cluster, gloss, conf) in rows:
            ops_rows = self.conn.execute(
                "SELECT op FROM cluster_ops WHERE cluster = ? ORDER BY op",
                (cluster,),
            ).fetchall()
            out.append(
                {
                    "cluster": cluster,
                    "ops": [r[0] for r in ops_rows],
                    "gloss": gloss,
                    "confidence": conf,
                }
            )
        return out

    def field_entries(self) -> List[Dict[str, Any]]:
        glyph_rows = self.conn.execute("SELECT glyph FROM glyph_fields ORDER BY glyph").fetchall()
        out: List[Dict[str, Any]] = []
        for (glyph,) in glyph_rows:
            # tags with contexts
            tag_rows = self.conn.execute(
                """
                SELECT tag, confidence, evidence_count
                FROM glyph_field_tags WHERE glyph = ? ORDER BY tag
                """,
                (glyph,),
            ).fetchall()
            tags: List[Dict[str, Any]] = []
            for (tag, conf, evid) in tag_rows:
                ctx_rows = self.conn.execute(
                    "SELECT context FROM glyph_field_tag_contexts WHERE glyph = ? AND tag = ? ORDER BY context",
                    (glyph, tag),
                ).fetchall()
                tags.append(
                    {
                        "tag": tag,
                        "confidence": conf,
                        "evidence_count": evid,
                        "contexts": [r[0] for r in ctx_rows],
                    }
                )

            # position preferences
            pp_rows = self.conn.execute(
                """
                SELECT position, name, score
                FROM glyph_position_prefs WHERE glyph = ? ORDER BY position, name
                """,
                (glyph,),
            ).fetchall()
            position_preferences = [
                {"position": r[0], "name": r[1], "score": r[2]} for r in pp_rows
            ]

            # cluster behaviors
            cb_rows = self.conn.execute(
                "SELECT cluster, value FROM glyph_cluster_behaviors WHERE glyph = ? ORDER BY cluster",
                (glyph,),
            ).fetchall()
            cluster_behaviors = [
                {"cluster": r[0], "value": r[1]} for r in cb_rows
            ]

            out.append(
                {
                    "glyph": glyph,
                    "tags": tags,
                    "position_preferences": position_preferences,
                    "cluster_behaviors": cluster_behaviors,
                }
            )
        return out

    def tag_association_entries(self) -> List[Dict[str, Any]]:
        rows = self.conn.execute("SELECT tag, value FROM tag_associations").fetchall()
        out: List[Dict[str, Any]] = []
        for (tag, value) in rows:
            try:
                decoded = json.loads(value) if isinstance(value, str) else value
            except Exception:
                decoded = None
            out.append({"tag": tag, "value": decoded})
        return out

    # --- Union/raw getters (compat) ---
    def merged_union(self) -> Dict[str, Any]:
        # Reconstruct a union with just the pieces we need downstream
        return {
            "tag_associations": {e["tag"]: e["value"] for e in self.tag_association_entries()},
            # named_payloads are not used heavily; reconstruct if needed later
        }


def get_db_merged(db_path: Optional[Path] = None) -> DBMergedGlyphs:
    return DBMergedGlyphs(db_path)

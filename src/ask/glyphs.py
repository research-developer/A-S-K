from __future__ import annotations

from typing import Any, Dict
import sqlite3
from pathlib import Path

from ask.merged_glyphs_db import get_db_merged

# Compute default DB path locally to avoid importing ask.core (which imports services)
_DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "glyphs.db"


def _load_from_db() -> Dict[str, Any]:
    """Load glyph primitives from the SQLite DB (atomic ground truth).

    Returns a dict with keys matching the previous JSON structure for compatibility.
    """
    mg = get_db_merged(_DEFAULT_DB_PATH)

    # Vowels as a contiguous string (historical API)
    vowels_list = mg.vowels() or []
    vowels = "".join(vowels_list)

    # Payloads (typed)
    payload_map: Dict[str, Dict[str, Any]] = {}
    for e in mg.typed_payload_entries():
        v = e.get("vowel")
        if not v:
            continue
        payload_map[v] = {
            "type": e.get("type"),
            "tag": e.get("tag"),
            "principle": e.get("principle"),
            "confidence": e.get("confidence"),
        }

    # Operators map glyph -> op name
    operator_map: Dict[str, str] = {}
    for e in mg.operator_entries():
        glyph = e.get("glyph")
        val = e.get("value")
        if glyph and val:
            operator_map[glyph] = val

    # Complete operators map glyph -> details
    complete_operator_map: Dict[str, Dict[str, Any]] = {}
    for e in mg.complete_operator_entries():
        glyph = e.get("glyph")
        if glyph:
            complete_operator_map[glyph] = {
                "op": e.get("op"),
                "principle": e.get("principle"),
                "confidence": e.get("confidence"),
            }

    # Clusters and enhanced clusters
    cluster_map: Dict[str, Any] = {}
    for e in mg.cluster_entries():
        cluster_map[e.get("cluster")] = list(e.get("value") or [])

    enhanced_cluster_map: Dict[str, Any] = {}
    for e in mg.enhanced_cluster_entries():
        enhanced_cluster_map[e.get("cluster")] = {
            "ops": list(e.get("ops") or []),
            "gloss": e.get("gloss"),
            "confidence": e.get("confidence"),
        }

    # Enforce preferred ordering for certain clusters to preserve legacy semantics
    preferred_cluster_order = {
        "sk": ["stream", "clamp"],
        "sc": ["stream", "clamp"],
    }
    for cl, order in preferred_cluster_order.items():
        if cl in enhanced_cluster_map:
            ops = enhanced_cluster_map[cl].get("ops") or []
            # Reorder existing ops to match preferred order where possible
            ordered = [op for op in order if op in ops]
            # Append any remaining ops that were not specified, preserving their existing order
            ordered += [op for op in ops if op not in ordered]
            enhanced_cluster_map[cl]["ops"] = ordered

    # Named payloads come from their own table; query directly
    conn = sqlite3.connect(str(_DEFAULT_DB_PATH))
    try:
        rows = conn.execute("SELECT name, type, tag, principle, features, confidence FROM named_payloads").fetchall()
    finally:
        conn.close()
    named_payloads: Dict[str, Any] = {}
    for r in rows:
        named_payloads[r[0]] = {
            "type": r[1],
            "tag": r[2],
            "principle": r[3],
            "features": r[4],
            "confidence": r[5],
        }

    return {
        "vowels": vowels or "aeiouy",
        "payload_map": payload_map,
        "operator_map": operator_map,
        "cluster_map": cluster_map,
        "enhanced_cluster_map": enhanced_cluster_map,
        "complete_operator_map": complete_operator_map,
        "typed_payload_map": payload_map,  # alias for compatibility
        "named_payloads": named_payloads,
    }


_DATA = _load_from_db()

VOWELS: str = _DATA["vowels"]
PAYLOAD_MAP: Dict[str, Dict[str, Any]] = _DATA["payload_map"]
OPERATOR_MAP: Dict[str, str] = _DATA["operator_map"]
CLUSTER_MAP: Dict[str, Any] = _DATA["cluster_map"]

# Enhanced/expanded maps also exposed for convenience
ENHANCED_CLUSTER_MAP: Dict[str, Any] = _DATA["enhanced_cluster_map"]
COMPLETE_OPERATOR_MAP: Dict[str, Any] = _DATA["complete_operator_map"]
TYPED_PAYLOAD_MAP: Dict[str, Any] = _DATA["typed_payload_map"]
NAMED_PAYLOADS: Dict[str, Any] = _DATA.get("named_payloads", {})

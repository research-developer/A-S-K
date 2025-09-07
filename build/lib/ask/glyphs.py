from __future__ import annotations

from typing import Any, Dict
import os
import sqlite3
from pathlib import Path

from ask.merged_glyphs_db import get_db_merged
from ask.merged_glyphs import get_merged_glyphs

# Compute candidate DB paths (installed vs editable vs CWD)
_PKG_BASE = Path(__file__).resolve().parents[2]
_CANDIDATE_DB_PATHS = [
    _PKG_BASE / "data" / "glyphs.db",           # package-relative
    Path.cwd() / "data" / "glyphs.db",          # cwd-relative
]
_ENV_DB = os.getenv("ASK_DB_PATH")
if _ENV_DB:
    _CANDIDATE_DB_PATHS.insert(0, Path(_ENV_DB))


def _load_from_db(db_path: Path) -> Dict[str, Any]:
    """Load glyph primitives from the SQLite DB (atomic ground truth)."""
    mg = get_db_merged(db_path)

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
    conn = sqlite3.connect(str(db_path))
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

def _load_data() -> Dict[str, Any]:
    # 1) Try DB candidates
    for path in _CANDIDATE_DB_PATHS:
        try:
            if path.exists():
                return _load_from_db(path)
        except Exception:
            continue
    # 2) Try merged JSON provider (if available)
    try:
        mg = get_merged_glyphs()
        # Build maps from merged provider
        vowels = "".join(mg.vowels() or list("aeiouy"))
        payload_map: Dict[str, Dict[str, Any]] = {}
        for e in mg.typed_payload_entries():
            v = e.get("vowel")
            if v:
                payload_map[v] = {
                    "type": e.get("type"),
                    "tag": e.get("tag"),
                    "principle": e.get("principle"),
                    "confidence": e.get("confidence", 0.7),
                }
        operator_map = {}
        for e in mg.operator_entries():
            g = e.get("glyph"); val = e.get("value")
            if g and val:
                operator_map[g] = val
        complete_operator_map = {}
        for e in mg.complete_operator_entries():
            g = e.get("glyph")
            if g:
                complete_operator_map[g] = {
                    "op": e.get("op"),
                    "principle": e.get("principle"),
                    "confidence": e.get("confidence", 0.7),
                }
        cluster_map = {}
        for e in mg.cluster_entries():
            cluster_map[e.get("cluster")] = list(e.get("value") or [])
        enhanced_cluster_map = {}
        for e in mg.enhanced_cluster_entries():
            enhanced_cluster_map[e.get("cluster")] = {
                "ops": list(e.get("ops") or []),
                "gloss": e.get("gloss"),
                "confidence": e.get("confidence", 0.7),
            }
        # Order fix for sk/sc
        for cl in ("sk","sc"):
            if cl in enhanced_cluster_map:
                ops = enhanced_cluster_map[cl].get("ops") or []
                ordered = [op for op in ["stream","clamp"] if op in ops]
                ordered += [op for op in ops if op not in ordered]
                enhanced_cluster_map[cl]["ops"] = ordered
        return {
            "vowels": vowels,
            "payload_map": payload_map,
            "operator_map": operator_map,
            "cluster_map": cluster_map,
            "enhanced_cluster_map": enhanced_cluster_map,
            "complete_operator_map": complete_operator_map,
            "typed_payload_map": payload_map,
            "named_payloads": {},
        }
    except Exception:
        pass

    # 3) Minimal built-in defaults as last resort
    return {
        "vowels": "aeiouy",
        "payload_map": {},
        "operator_map": {},
        "cluster_map": {},
        "enhanced_cluster_map": {},
        "complete_operator_map": {},
        "typed_payload_map": {},
        "named_payloads": {},
    }


_DATA = _load_data()

VOWELS: str = _DATA["vowels"]
PAYLOAD_MAP: Dict[str, Dict[str, Any]] = _DATA["payload_map"]
OPERATOR_MAP: Dict[str, str] = _DATA["operator_map"]
CLUSTER_MAP: Dict[str, Any] = _DATA["cluster_map"]

# Enhanced/expanded maps also exposed for convenience
ENHANCED_CLUSTER_MAP: Dict[str, Any] = _DATA["enhanced_cluster_map"]
COMPLETE_OPERATOR_MAP: Dict[str, Any] = _DATA["complete_operator_map"]
TYPED_PAYLOAD_MAP: Dict[str, Any] = _DATA["typed_payload_map"]
NAMED_PAYLOADS: Dict[str, Any] = _DATA.get("named_payloads", {})

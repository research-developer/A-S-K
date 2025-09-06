#!/usr/bin/env python3
"""
Merge data/glyphs.json and data/glyph_fields.json into a single dataset without losing information.

- Preserves original structures under a combined top-level object
- Adds a "merged" union view that contains both glyph maps and field maps
- Adds a "normalized" view that exposes list-based entries for consumers that
  prefer uniform arrays (the "interface returns a list" requirement) with default
  length 1 semantics handled by consumers (singletons appear as single-element lists)
- Writes result to data/glyphs_merged.json
- Prints a verification report ensuring key sets and sizes match between inputs and merged views

Usage:
  python tools/merge_glyph_datasets.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import sys

ROOT = Path(__file__).resolve().parents[1]
GLYPHS = ROOT / "data" / "glyphs.json"
FIELDS = ROOT / "data" / "glyph_fields.json"
OUT = ROOT / "data" / "glyphs_merged.json"


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dict_to_entries(d: Dict[str, Any], key_name: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for k, v in (d or {}).items():
        item = {key_name: k}
        if isinstance(v, dict):
            item.update(v)
        else:
            item["value"] = v
        out.append(item)
    return out


def fields_to_entries(fields: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for glyph, body in (fields or {}).items():
        tags_map = (body or {}).get("tags", {}) or {}
        positions = (body or {}).get("position_preferences", {}) or {}
        clusters = (body or {}).get("cluster_behaviors", {}) or {}
        tag_list = dict_to_entries(tags_map, "tag")
        # Normalize inner tag objects to include their tag name and metrics
        for t in tag_list:
            t.setdefault("confidence", None)
            t.setdefault("evidence_count", None)
            t.setdefault("contexts", None)
        position_list: List[Dict[str, Any]] = []
        for pos, prefs in positions.items():
            for name, score in (prefs or {}).items():
                position_list.append({"position": pos, "name": name, "score": score})
        cluster_list = dict_to_entries(clusters, "cluster")
        entries.append({
            "glyph": glyph,
            "tags": tag_list,
            "position_preferences": position_list,
            "cluster_behaviors": cluster_list,
        })
    return entries


def merge() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    glyphs = read_json(GLYPHS)
    fields = read_json(FIELDS)

    merged_union: Dict[str, Any] = {
        # from glyphs.json
        "vowels": glyphs.get("vowels"),
        "payload_map": glyphs.get("payload_map"),
        "operator_map": glyphs.get("operator_map"),
        "cluster_map": glyphs.get("cluster_map"),
        "enhanced_cluster_map": glyphs.get("enhanced_cluster_map"),
        "complete_operator_map": glyphs.get("complete_operator_map"),
        "typed_payload_map": glyphs.get("typed_payload_map"),
        "named_payloads": glyphs.get("named_payloads"),
        # from glyph_fields.json
        "fields": (fields.get("fields") or {}),
        "tag_associations": fields.get("tag_associations"),
    }

    # Normalized array-based views (interface that always returns a list)
    normalized: Dict[str, Any] = {
        "vowels": list(glyphs.get("vowels", "")),
        "payload_entries": dict_to_entries(glyphs.get("payload_map", {}) or {}, "vowel"),
        "operator_entries": dict_to_entries(glyphs.get("operator_map", {}) or {}, "glyph"),
        "complete_operator_entries": dict_to_entries(glyphs.get("complete_operator_map", {}) or {}, "glyph"),
        "typed_payload_entries": dict_to_entries(glyphs.get("typed_payload_map", {}) or {}, "vowel"),
        "cluster_entries": dict_to_entries(glyphs.get("cluster_map", {}) or {}, "cluster"),
        "enhanced_cluster_entries": dict_to_entries(glyphs.get("enhanced_cluster_map", {}) or {}, "cluster"),
        "field_entries": fields_to_entries((fields.get("fields") or {})),
        "tag_association_entries": dict_to_entries(fields.get("tag_associations", {}) or {}, "tag"),
    }

    combined: Dict[str, Any] = {
        "sources": {
            "glyphs_path": str(GLYPHS),
            "glyph_fields_path": str(FIELDS),
        },
        "merged": merged_union,
        "normalized": normalized,
    }

    return combined, glyphs, fields


def verify(combined: Dict[str, Any], glyphs: Dict[str, Any], fields: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    m = combined["merged"]
    n = combined["normalized"]

    # Exact equality checks for merged union vs sources
    for key in [
        "vowels",
        "payload_map",
        "operator_map",
        "cluster_map",
        "enhanced_cluster_map",
        "complete_operator_map",
        "typed_payload_map",
        "named_payloads",
    ]:
        if m.get(key) != glyphs.get(key):
            problems.append(f"merged.{key} is not identical to source glyphs.{key}")

    if m.get("fields") != (fields.get("fields") or {}):
        problems.append("merged.fields is not identical to glyph_fields.fields")
    if m.get("tag_associations") != fields.get("tag_associations"):
        problems.append("merged.tag_associations is not identical to glyph_fields.tag_associations")

    # payload_map keys preserved
    pm = glyphs.get("payload_map", {}) or {}
    if set(pm.keys()) != {e.get("vowel") for e in n.get("payload_entries", [])}:
        problems.append("payload_map keys mismatch in normalized payload_entries")

    # operator_map keys preserved
    om = glyphs.get("operator_map", {}) or {}
    if set(om.keys()) != {e.get("glyph") for e in n.get("operator_entries", [])}:
        problems.append("operator_map keys mismatch in normalized operator_entries")

    # complete_operator_map keys preserved
    com = glyphs.get("complete_operator_map", {}) or {}
    if set(com.keys()) != {e.get("glyph") for e in n.get("complete_operator_entries", [])}:
        problems.append("complete_operator_map keys mismatch in normalized complete_operator_entries")

    # clusters preserved
    cm = glyphs.get("cluster_map", {}) or {}
    ecm = glyphs.get("enhanced_cluster_map", {}) or {}
    if set(cm.keys()) != {e.get("cluster") for e in n.get("cluster_entries", [])}:
        problems.append("cluster_map keys mismatch in normalized cluster_entries")
    if set(ecm.keys()) != {e.get("cluster") for e in n.get("enhanced_cluster_entries", [])}:
        problems.append("enhanced_cluster_map keys mismatch in normalized enhanced_cluster_entries")

    # Ensure fields were copied
    if not m.get("fields"):
        problems.append("fields missing in merged union")

    return problems


def main() -> int:
    combined, glyphs, fields = merge()

    # Write output
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        json.dump(combined, fh, indent=2, ensure_ascii=False)

    # Verify
    problems = verify(combined, glyphs, fields)
    print("Merged written to:", OUT)
    if problems:
        print("\nVerification issues:")
        for p in problems:
            print(" -", p)
        return 1
    else:
        print("Verification passed: key sets preserved and fields present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

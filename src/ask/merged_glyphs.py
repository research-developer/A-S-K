from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

MERGED_PATH = Path(__file__).resolve().parents[2] / "data" / "glyphs_merged.json"

class MergedGlyphs:
    """Loader for merged glyph datasets that always returns lists.

    Accessors expose only list-based normalized views so downstream
    callers never have to branch on dict vs list shapes.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or MERGED_PATH
        with self.path.open("r", encoding="utf-8") as fh:
            self.data: Dict[str, Any] = json.load(fh)
        self.norm: Dict[str, Any] = self.data.get("normalized", {})
        self.union: Dict[str, Any] = self.data.get("merged", {})

    # --- Normalized accessors (always lists) ---
    def vowels(self) -> List[str]:
        return list(self.norm.get("vowels") or [])

    def payload_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("payload_entries") or [])

    def operator_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("operator_entries") or [])

    def complete_operator_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("complete_operator_entries") or [])

    def typed_payload_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("typed_payload_entries") or [])

    def cluster_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("cluster_entries") or [])

    def enhanced_cluster_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("enhanced_cluster_entries") or [])

    def field_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("field_entries") or [])

    def tag_association_entries(self) -> List[Dict[str, Any]]:
        return list(self.norm.get("tag_association_entries") or [])

    # --- Union/raw getters (do not modify; for compatibility) ---
    def merged_union(self) -> Dict[str, Any]:
        return dict(self.union)


def get_merged_glyphs(path: Path | None = None) -> MergedGlyphs:
    return MergedGlyphs(path)

from __future__ import annotations

"""Core services layer for A-S-K.

This module centralizes program logic so different front-ends (CLI, Web API, MCP)
can consume the same functionality without duplicating implementation details.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ask.enhanced_factorizer import enhanced_decode_word, COMPLETE_OPERATOR_MAP, ENHANCED_CLUSTER_MAP
from ask.state_syntax import USKParser, TYPE_COLORS
from ask.glyph_fields import GlyphFieldSystem


@dataclass
class DecodeResult:
    word: str
    decoded: Dict[str, Any]


@dataclass
class SyntaxResult:
    word: str
    language: str
    syntax: str
    elements: List[Dict[str, Any]]
    overall_confidence: float
    morphology: Dict[str, Any]


class ASKServices:
    """Facade for all core A-S-K operations."""

    def __init__(self, persist: Optional[bool] = None) -> None:
        # Central glyph system instance; can be configured for persistence
        self.glyph_system = GlyphFieldSystem(persist=persist)
        self.parser = USKParser(glyph_system=self.glyph_system)

    # Enhanced decode (factorizer-centric)
    def decode(self, word: str) -> DecodeResult:
        decoded = enhanced_decode_word(word)
        return DecodeResult(word=word, decoded=decoded)

    # State-aware syntax (parser-centric)
    def syntax(self, word: str, language: str = "english") -> SyntaxResult:
        result = self.parser.parse_word(word, language=language)
        payload = {
            "word": word,
            "language": language,
            "syntax": result.to_usk_syntax(),
            "elements": [
                {
                    "surface": e.surface,
                    "semantic": e.semantic,
                    "position": e.position,
                    "confidence": e.confidence,
                    "state": str(e.state) if e.state else None,
                }
                for e in result.elements
            ],
            "overall_confidence": result.overall_confidence,
            "morphology": result.morphology or {},
        }
        return SyntaxResult(**payload)

    def list_operators(self, min_conf: float = 0.0) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for glyph, info in COMPLETE_OPERATOR_MAP.items():
            if info["confidence"] >= min_conf:
                out.append({
                    "glyph": glyph,
                    "operator": info["op"],
                    "principle": info["principle"],
                    "confidence": info["confidence"],
                })
        # Sort by confidence desc
        out.sort(key=lambda x: x["confidence"], reverse=True)
        return out

    def list_clusters(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for cluster, info in ENHANCED_CLUSTER_MAP.items():
            out.append({
                "cluster": cluster,
                "ops": info["ops"],
                "gloss": info["gloss"],
                "confidence": info["confidence"],
            })
        # sort by length desc then alpha
        out.sort(key=lambda x: (-len(x["cluster"]), x["cluster"]))
        return out

    def get_operator_info(self, operator: str) -> Optional[Dict[str, Any]]:
        """Return operator map info by operator name (reverse lookup)."""
        for glyph, info in COMPLETE_OPERATOR_MAP.items():
            if info.get("op") == operator:
                return info
        return None


def get_services(persist: Optional[bool] = None) -> ASKServices:
    return ASKServices(persist=persist)


__all__ = [
    "ASKServices",
    "get_services",
    "DecodeResult",
    "SyntaxResult",
    "TYPE_COLORS",
]

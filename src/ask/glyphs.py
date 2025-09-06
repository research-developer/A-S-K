from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_DEFAULTS = {
    "vowels": "aeiouy",
    "payload_map": {
        "a": {"type": "base_type", "tag": "base", "principle": "aperture/origin"},
        "e": {"type": "encompass", "tag": "relate", "principle": "reflexive-relational"},
        "i": {"type": "identify", "tag": "index", "principle": "minimal unit/index"},
        "o": {"type": "whole", "tag": "object", "principle": "wholeness/container"},
        "u": {"type": "union", "tag": "capacity", "principle": "root/union/channel"},
        "y": {"type": "branch", "tag": "branch", "principle": "bifurcated value"},
    },
    "operator_map": {
        "b": "bind",
        "c": "contain",
        "d": "decide",
        "f": "flow",
        "g": "grasp",
        "h": "animate",
        "j": "project",
        "k": "clamp",
        "l": "level",
        "m": "multiply",
        "n": "negate",
        "p": "present",
        "q": "query",
        "r": "relate",
        "s": "stream",
        "t": "instantiate",
        "v": "vector",
        "w": "web",
        "x": "cross",
        "z": "quantize",
    },
    "cluster_map": {
        "st": ["stream", "instantiate"],
        "tr": ["instantiate", "rotate"],
        "pl": ["present", "align"],
        "str": ["stream", "instantiate", "rotate"],
        "spr": ["stream", "present", "rotate"],
        # sk/sc family frequently signals split/scan/classify; we model as stream+clamp
        "sk": ["stream", "clamp"],
        "sc": ["stream", "clamp"],
    },
    "enhanced_cluster_map": {},
    "complete_operator_map": {},
    "typed_payload_map": {},
}


def _glyphs_path() -> Path:
    # src/ask/glyphs.py -> .../src/ask -> parent is src -> parent is project root
    return Path(__file__).resolve().parents[2] / "data" / "glyphs.json"


def load_glyphs() -> Dict[str, Any]:
    path = _glyphs_path()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return {**_DEFAULTS, **data}
    except Exception:
        return dict(_DEFAULTS)


_DATA = load_glyphs()

VOWELS: str = _DATA.get("vowels", "aeiouy")
PAYLOAD_MAP: Dict[str, Dict[str, Any]] = _DATA.get("payload_map", {})
OPERATOR_MAP: Dict[str, str] = _DATA.get("operator_map", {})
CLUSTER_MAP: Dict[str, Any] = _DATA.get("cluster_map", {})

# Enhanced/expanded maps also exposed for convenience
ENHANCED_CLUSTER_MAP: Dict[str, Any] = _DATA.get("enhanced_cluster_map", {})
COMPLETE_OPERATOR_MAP: Dict[str, Any] = _DATA.get("complete_operator_map", {})
TYPED_PAYLOAD_MAP: Dict[str, Any] = _DATA.get("typed_payload_map", {})

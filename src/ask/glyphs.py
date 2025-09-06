from __future__ import annotations

# Core maps derived from GLYPHS.md
# Vowels as typed payloads
PAYLOAD_MAP = {
    "a": {"type": "base_type", "tag": "base", "principle": "aperture/origin"},
    "e": {"type": "relation", "tag": "relational", "principle": "reflexive-relational"},
    "i": {"type": "index", "tag": "index", "principle": "minimal unit/index"},
    "o": {"type": "container", "tag": "object", "principle": "wholeness/container"},
    "u": {"type": "struct", "tag": "capacity", "principle": "root/union/channel"},
    "y": {"type": "branch", "tag": "branch", "principle": "bifurcated value"},
}

# Consonants as operators
OPERATOR_MAP = {
    "b": "bind",
    "c": "contain",
    "d": "decide",
    "f": "flow",
    "g": "grasp",
    "h": "animate",
    "j": "project",
    "k": "clamp",
    "l": "align",
    "m": "multiply",
    "n": "negate",
    "p": "present",
    "q": "query",
    "r": "rotate",
    "s": "stream",
    "t": "instantiate",
    "v": "vector",
    "w": "web",
    "x": "cross",
    "z": "quantize",
}

# Selected consonant clusters with preferred combined semantics
CLUSTER_MAP = {
    "st": ["stream", "instantiate"],
    "tr": ["instantiate", "rotate"],
    "pl": ["present", "align"],
    "str": ["stream", "instantiate", "rotate"],
    "spr": ["stream", "present", "rotate"],
    # sk/sc family frequently signals split/scan/classify; we model as stream+clamp
    "sk": ["stream", "clamp"],
    "sc": ["stream", "clamp"],
}

from __future__ import annotations

import re
from typing import List, Dict, Any

from .glyphs import OPERATOR_MAP, PAYLOAD_MAP, CLUSTER_MAP

# Regex patterns for simple English-like orthography tokenization
VOWELS = "aeiouy"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"

CLUSTER_KEYS = sorted(CLUSTER_MAP.keys(), key=len, reverse=True)


def extract_consonant_clusters(surface: str) -> List[str]:
    s = surface.lower()
    i = 0
    clusters: List[str] = []
    while i < len(s):
        # Try cluster first
        matched = False
        for ck in CLUSTER_KEYS:
            if s.startswith(ck, i):
                clusters.append(ck)
                i += len(ck)
                matched = True
                break
        if matched:
            continue
        ch = s[i]
        if ch in CONSONANTS:
            clusters.append(ch)
        i += 1
    # Filter out empty and non-consonant sequences
    clusters = [c for c in clusters if all(cc in CONSONANTS for cc in c)]
    return clusters


def extract_vowel_sequence(surface: str) -> List[str]:
    return [ch for ch in surface.lower() if ch in VOWELS]


def decode_word(surface: str) -> Dict[str, Any]:
    """Return a structured decoding of a word into operators/payloads and an AST-like form.

    This is a pragmatic MVP, not a linguistic authority.
    """
    ops_raw = extract_consonant_clusters(surface)
    payloads_raw = extract_vowel_sequence(surface)

    program_ops: List[str] = []
    for op in ops_raw:
        if op in CLUSTER_MAP:
            program_ops.extend(CLUSTER_MAP[op])
        else:
            # decompose each consonant to operator
            for ch in op:
                if ch in OPERATOR_MAP:
                    program_ops.append(OPERATOR_MAP[ch])

    typed_payloads = [PAYLOAD_MAP[v] for v in payloads_raw if v in PAYLOAD_MAP]

    return {
        "surface": surface,
        "operators": ops_raw,
        "payloads": payloads_raw,
        "program": program_ops,
        "typed_payloads": typed_payloads,
    }

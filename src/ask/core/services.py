from __future__ import annotations

"""Core services layer for A-S-K.

This module centralizes program logic so different front-ends (CLI, Web API, MCP)
can consume the same functionality without duplicating implementation details.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ask.enhanced_factorizer import enhanced_decode_word
from ask.merged_glyphs import get_merged_glyphs
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
    # Bindings of nearest payload(s) to an operator/function head
    closures: List[Dict[str, Any]] | None = None
    # Linear sequence of tokens with types and head linkage (no grouping)
    sequence: List[Dict[str, Any]] | None = None


class ASKServices:
    """Facade for all core A-S-K operations."""

    def __init__(self, persist: Optional[bool] = None) -> None:
        # Central glyph system instance; can be configured for persistence
        self.glyph_system = GlyphFieldSystem(persist=persist)
        self.parser = USKParser(glyph_system=self.glyph_system)
        self._merged = get_merged_glyphs()
        # Precompute lookup maps from merged normalized lists
        ml = self._merged
        self._typed_payload_by_vowel: Dict[str, Dict[str, Any]] = {e.get("vowel"): e for e in ml.typed_payload_entries()}
        self._complete_operator_by_glyph: Dict[str, Dict[str, Any]] = {e.get("glyph"): e for e in ml.complete_operator_entries()}
        self._operator_by_name: Dict[str, Dict[str, Any]] = {}
        for e in ml.complete_operator_entries():
            op = e.get("op")
            if op:
                self._operator_by_name[op] = e
        self._enhanced_clusters: List[Dict[str, Any]] = ml.enhanced_cluster_entries()

    # Enhanced decode (factorizer-centric)
    def decode(self, word: str) -> DecodeResult:
        decoded = enhanced_decode_word(word)
        # Build a structured 'program' view: steps and signature for UI rendering
        try:
            ops = list(decoded.get("operators", []) or [])
            payloads = list(decoded.get("payloads", []) or [])
            pairs = list(decoded.get("pairs", []) or [])

            # Steps prefer explicit pairs if present
            steps = []
            if pairs:
                for idx, pr in enumerate(pairs):
                    if isinstance(pr, (list, tuple)) and len(pr) >= 2:
                        op = pr[0]
                        pay = pr[1]
                        parts = str(pay).split("+") if isinstance(pay, str) and "+" in pay else ([pay] if pay else [])
                        # Map single-vowel payloads to human-friendly tag if available
                        payload_tag = None
                        if isinstance(pay, str) and len(pay) == 1:
                            payload_tag = (self._typed_payload_by_vowel.get(pay) or {}).get("tag")
                        payload_display = (
                            "+".join([ (self._typed_payload_by_vowel.get(p) or {}).get("tag", p) for p in parts ]) if (isinstance(pay, str) and "+" in pay)
                            else (payload_tag or pay)
                        )
                        position = (
                            "initial" if idx == 0 else ("final" if idx == len(pairs) - 1 else "medial")
                        )
                        # Map operator name to its principle using merged complete_operator_entries
                        principle = (self._operator_by_name.get(op) or {}).get("principle") if isinstance(op, str) else None
                        steps.append({
                            "index": idx,
                            "position": position,
                            "op": op,
                            "principle": principle,
                            "payload": pay,
                            "payload_tag": payload_tag,
                            "payload_display": payload_display,
                            "payload_parts": [p for p in parts if p],
                        })
            else:
                for idx, op in enumerate(ops):
                    pay = payloads[idx] if idx < len(payloads) else None
                    parts = str(pay).split("+") if isinstance(pay, str) and "+" in pay else ([pay] if pay else [])
                    payload_tag = None
                    if isinstance(pay, str) and len(pay) == 1:
                        payload_tag = (self._typed_payload_by_vowel.get(pay) or {}).get("tag")
                    payload_display = (
                        "+".join([ (self._typed_payload_by_vowel.get(p) or {}).get("tag", p) for p in parts ]) if (isinstance(pay, str) and "+" in pay)
                        else (payload_tag or pay)
                    )
                    position = (
                        "initial" if idx == 0 else ("final" if idx == len(ops) - 1 else "medial")
                    )
                    principle = (self._operator_by_name.get(op) or {}).get("principle") if isinstance(op, str) else None
                    steps.append({
                        "index": idx,
                        "position": position,
                        "op": op,
                        "principle": principle,
                        "payload": pay,
                        "payload_tag": payload_tag,
                        "payload_display": payload_display,
                        "payload_parts": [p for p in parts if p],
                    })

            # Signature resembles a programming function header
            gloss = decoded.get("gloss")
            signature = {
                "name": (gloss.split(" → ")[0] if isinstance(gloss, str) and " → " in gloss else (gloss or "function")),
                "chain": ops,
                "args": [
                    ([p for p in str(pay).split("+") if p] if isinstance(pay, str) and "+" in pay else ([pay] if pay else []))
                    for pay in payloads
                ],
                "returns": None,
                "text": gloss or (" → ".join(ops) if ops else ""),
            }

            decoded["program"] = {
                "signature": signature,
                "steps": steps,
            }

            # Expose closures: bind each operator/function step to its immediate payload
            # A closure here is a small structure capturing the operator and the payload it closes over.
            decoded["closures"] = [
                {
                    "index": s.get("index"),
                    "position": s.get("position"),
                    "operator": s.get("op"),
                    "principle": s.get("principle"),
                    # payload run (may be composite like "io")
                    "payload": s.get("payload"),
                    # single-vowel tag if applicable (e.g., 'a' -> 'base')
                    "payload_tag": s.get("payload_tag"),
                    # split parts for composites (e.g., "i+o" -> ["i","o"])
                    "payload_parts": s.get("payload_parts") or [],
                }
                for s in steps
            ]

            # Linear sequence with types and head linkage (no grouping)
            sequence: List[Dict[str, Any]] = []
            for s in steps:
                # operator token entry
                head_entry = {
                    "index": len(sequence),
                    "role": "head",
                    "type": "op",  # decode is operator-centric
                    "operator": s.get("op"),
                    "principle": s.get("principle"),
                    "position": s.get("position"),
                    "confidence": None,
                }
                head_id = head_entry["index"]
                sequence.append(head_entry)
                # payload entry if present
                pay = s.get("payload")
                if pay:
                    sequence.append({
                        "index": len(sequence),
                        "role": "payload",
                        "type": "val",
                        "surface": pay,
                        "tag": s.get("payload_tag"),
                        "parts": s.get("payload_parts") or [],
                        "head_id": head_id,
                    })
            decoded["sequence"] = sequence
        except Exception:
            # Best effort; don't break decode if program shaping fails
            pass
        return DecodeResult(word=word, decoded=decoded)

    # State-aware syntax (parser-centric)
    def syntax(self, word: str, language: str = "english") -> SyntaxResult:
        result = self.parser.parse_word(word, language=language)
        # Compute closures with strict left-to-right sequencing.
        # Rule: attach PAYLOADs to the nearest OPERATOR/FUNCTION head.
        # - If a PAYLOAD appears before any head, tentatively buffer it and
        #   attach to the next head when it appears (common case: leading vowel).
        closures: List[Dict[str, Any]] = []
        current_group: Optional[Dict[str, Any]] = None
        buffered_payloads: List[Dict[str, Any]] = []

        def flush_current_group():
            nonlocal current_group
            if current_group is not None:
                closures.append(current_group)
                current_group = None

        for idx, e in enumerate(result.elements):
            etype = getattr(e, "element_type", None)
            kind = etype.value if etype else None

            if kind in ("operator", "function"):
                # Starting a new head closes the previous one
                flush_current_group()
                current_group = {
                    "head_index": idx,
                    "head": {
                        "surface": e.surface,
                        "semantic": e.semantic,
                        "type": kind,
                        "position": e.position,
                        "confidence": e.confidence,
                    },
                    "payloads": [],
                }
                # Attach any payloads buffered before the first head
                if buffered_payloads:
                    current_group["payloads"].extend(buffered_payloads)
                    buffered_payloads = []
            elif kind == "value":
                payload_obj = {
                    "index": idx,
                    "surface": e.surface,
                    "semantic": e.semantic,
                    "is_struct": (isinstance(e.semantic, str) and ("+" in e.semantic or "," in e.semantic)),
                    "position": e.position,
                    "confidence": e.confidence,
                }
                if current_group is not None:
                    current_group["payloads"].append(payload_obj)
                else:
                    # No head yet; buffer to attach to the next head
                    buffered_payloads.append(payload_obj)
            else:
                # modifiers/state etc.: neither head nor payload; do nothing
                pass

        # Flush any open group at end
        flush_current_group()
        # If there are buffered payloads with no head at all, surface them as standalone groups
        for p in buffered_payloads:
            closures.append({
                "head_index": None,
                "head": None,
                "payloads": [p],
            })

        # Build linear sequence with types and head linkage
        # First pass: basic tokens
        seq: List[Dict[str, Any]] = []
        token_indices: List[int] = []
        for e in result.elements:
            # map element type to short type
            tmap = {
                "operator": "op",
                "function": "func",
                "value": "val",
                "modifier": "mod",
                "state": "state",
            }
            etype = getattr(e, "element_type", None)
            short_type = tmap.get(etype.value if etype else None, None)
            seq.append({
                "index": len(seq),
                "surface": e.surface,
                "semantic": e.semantic,
                "type": short_type,
                "position": e.position,
                "confidence": e.confidence,
                "state": str(e.state) if e.state else None,
            })
            token_indices.append(len(seq) - 1)

        # Second pass: assign head_id for payload tokens (strict left-to-right, attach leading payloads to next head)
        current_head_id: Optional[int] = None
        buffered_payload_ids: List[int] = []
        for tok in seq:
            if tok["type"] in ("op", "func"):
                current_head_id = tok["index"]
                if buffered_payload_ids:
                    for pid in buffered_payload_ids:
                        seq[pid]["head_id"] = current_head_id
                    buffered_payload_ids = []
            elif tok["type"] == "val":
                if current_head_id is not None:
                    tok["head_id"] = current_head_id
                else:
                    buffered_payload_ids.append(tok["index"])
            # other types: no head linkage

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
            "closures": closures,
            "sequence": seq,
        }
        return SyntaxResult(**payload)

    # Merged glyph datasets (list-only interface)
    def merged_lists(self, section: Optional[str] = None) -> Dict[str, Any]:
        """Return normalized list views from the merged glyph datasets.
        If section is provided, return only that list under {section: [...]};
        otherwise return all normalized lists.
        Sections: vowels, payload_entries, operator_entries, complete_operator_entries,
        typed_payload_entries, cluster_entries, enhanced_cluster_entries, field_entries,
        tag_association_entries.
        """
        m = self._merged
        all_lists = {
            "vowels": m.vowels(),
            "payload_entries": m.payload_entries(),
            "operator_entries": m.operator_entries(),
            "complete_operator_entries": m.complete_operator_entries(),
            "typed_payload_entries": m.typed_payload_entries(),
            "cluster_entries": m.cluster_entries(),
            "enhanced_cluster_entries": m.enhanced_cluster_entries(),
            "field_entries": m.field_entries(),
            "tag_association_entries": m.tag_association_entries(),
        }
        if section:
            if section not in all_lists:
                raise ValueError(f"unknown section: {section}")
            return {section: all_lists[section]}
        return all_lists

    def list_operators(self, min_conf: float = 0.0) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for e in self._complete_operator_by_glyph.values():
            if e.get("confidence", 0) >= min_conf:
                out.append({
                    "glyph": e.get("glyph"),
                    "operator": e.get("op"),
                    "principle": e.get("principle"),
                    "confidence": e.get("confidence"),
                })
        out.sort(key=lambda x: x["confidence"] or 0, reverse=True)
        return out

    def list_clusters(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for e in self._enhanced_clusters:
            out.append({
                "cluster": e.get("cluster"),
                "ops": e.get("ops"),
                "gloss": e.get("gloss"),
                "confidence": e.get("confidence"),
            })
        out.sort(key=lambda x: (-len(x["cluster"] or ""), x["cluster"] or ""))
        return out

    def get_operator_info(self, operator: str) -> Optional[Dict[str, Any]]:
        """Return operator info by operator name using merged lists."""
        return self._operator_by_name.get(operator)


def get_services(persist: Optional[bool] = None) -> ASKServices:
    return ASKServices(persist=persist)


__all__ = [
    "ASKServices",
    "get_services",
    "DecodeResult",
    "SyntaxResult",
    "TYPE_COLORS",
]

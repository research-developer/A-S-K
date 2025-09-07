from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator


class _ListCoercion:
    @staticmethod
    def _as_list(v: Any) -> List[Any]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]


class DecodeProgramSignature(BaseModel):
    name: Optional[str] = None
    chain: List[str] = []
    args: List[List[Any]] = []
    returns: Optional[Any] = None
    text: Optional[str] = None


class DecodeStep(_ListCoercion, BaseModel):
    index: int
    position: str
    op: Any
    principle: Optional[str] = None
    payload: Any = None
    payload_tags: List[str] = []
    payload_display: Optional[str] = None
    payload_parts: List[str] = []

    @field_validator("payload_tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v: Any) -> List[str]:
        return cls._as_list(v)

    @field_validator("payload_parts", mode="before")
    @classmethod
    def _coerce_parts(cls, v: Any) -> List[str]:
        return cls._as_list(v)


class DecodeClosure(_ListCoercion, BaseModel):
    index: Optional[int] = None
    position: Optional[str] = None
    operator: Any = None
    principle: Optional[str] = None
    payload: Any = None
    payload_tags: List[str] = []
    payload_parts: List[str] = []

    @field_validator("payload_tags", "payload_parts", mode="before")
    @classmethod
    def _coerce_lists(cls, v: Any) -> List[str]:
        return cls._as_list(v)


class SequenceToken(_ListCoercion, BaseModel):
    index: int
    role: str
    type: str
    surface: Any
    tags: List[str] = []
    parts: List[str] = []
    head_id: Optional[int] = None

    @field_validator("tags", "parts", mode="before")
    @classmethod
    def _coerce_lists(cls, v: Any) -> List[str]:
        return cls._as_list(v)


class DecodeProgram(BaseModel):
    signature: DecodeProgramSignature
    steps: List[DecodeStep] = []
    sequence: List[SequenceToken] = []


class DecodeResult(BaseModel):
    word: str
    decoded: Dict[str, Any]


class SyntaxElement(BaseModel):
    surface: Any
    semantic: Any
    position: Optional[str] = None
    confidence: Optional[float] = None
    state: Optional[str] = None


class SyntaxResult(BaseModel):
    word: str
    language: str
    syntax: str
    elements: List[Dict[str, Any]]
    overall_confidence: float
    morphology: Dict[str, Any]
    closures: Optional[List[Dict[str, Any]]] = None
    sequence: Optional[List[Dict[str, Any]]] = None


__all__ = [
    "DecodeProgramSignature",
    "DecodeStep",
    "DecodeClosure",
    "SequenceToken",
    "DecodeProgram",
    "DecodeResult",
    "SyntaxResult",
]

from __future__ import annotations

"""FastAPI web API for A-S-K using the core services layer.

Run locally:
    uvicorn ask.web.app:app --reload

Env:
    ASK_GLYPH_PERSIST=1  # to enable persistence by default
"""

import os
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

from ask.core import get_services
from ask.core.services import TYPE_COLORS


class DecodeRequest(BaseModel):
    word: str


class SyntaxRequest(BaseModel):
    word: str
    language: Optional[str] = "english"


def _persist_default() -> Optional[bool]:
    env_val = os.getenv("ASK_GLYPH_PERSIST")
    if env_val is None:
        return None
    s = env_val.strip().lower()
    return s in ("1", "true", "yes", "on")


app = FastAPI(title="A-S-K API", version="0.1.0")


@app.post("/decode")
async def decode(req: DecodeRequest, persist: Optional[bool] = Query(default=None)):
    if persist is None:
        persist = _persist_default()
    services = get_services(persist=persist)
    res = services.decode(req.word)
    return res.decoded


@app.post("/syntax")
async def syntax(req: SyntaxRequest, persist: Optional[bool] = Query(default=None)):
    if persist is None:
        persist = _persist_default()
    services = get_services(persist=persist)
    res = services.syntax(req.word, language=(req.language or "english"))
    return {
        "word": res.word,
        "language": res.language,
        "syntax": res.syntax,
        "elements": res.elements,
        "overall_confidence": res.overall_confidence,
        "morphology": res.morphology,
    }


# GET variants (simple query usage)
@app.get("/decode")
async def decode_get(word: str = Query(...), persist: Optional[bool] = Query(default=None)):
    if persist is None:
        persist = _persist_default()
    services = get_services(persist=persist)
    res = services.decode(word)
    return res.decoded


@app.get("/syntax")
async def syntax_get(
    word: str = Query(...),
    language: Optional[str] = Query("english"),
    persist: Optional[bool] = Query(default=None),
):
    if persist is None:
        persist = _persist_default()
    services = get_services(persist=persist)
    res = services.syntax(word, language=(language or "english"))
    return {
        "word": res.word,
        "language": res.language,
        "syntax": res.syntax,
        "elements": res.elements,
        "overall_confidence": res.overall_confidence,
        "morphology": res.morphology,
    }


@app.get("/operators")
async def operators(min_conf: float = Query(0.0)):
    services = get_services()
    return services.list_operators(min_conf)


@app.get("/clusters")
async def clusters():
    services = get_services()
    return services.list_clusters()


@app.get("/legend")
async def legend():
    # Return the centralized type colors so UIs can style consistently
    return TYPE_COLORS

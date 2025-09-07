from __future__ import annotations

import json
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env if present (non-fatal if absent)
load_dotenv()

DEFAULT_MODEL = "gpt-5-mini"


def build_audit_prompt(word: str, decoded: Dict[str, Any], guidelines: Optional[str] = None) -> str:
    guide = guidelines or (
        "Assess whether the operator/payload decoding aligns with GLYPHS.md axioms. "
        "Identify mismatches, propose corrected operators or payloads if needed, and cite rationale. "
        "Return JSON with fields: verdict (string: agree/partial/disagree), confidence (0-1), "
        "issues (list of strings), suggestions (object), and rationale (string)."
    )
    return (
        f"You are an expert auditor for a semantic glyph decoding framework (A-S-K).\n"
        f"Word: {word}\n"
        f"Decoded JSON (operators/payloads/program):\n{json.dumps(decoded, ensure_ascii=False, indent=2)}\n\n"
        f"Guidelines: {guide}\n"
        f"Only output a single JSON object."
    )


def audit_decoding(
    word: str,
    decoded: Dict[str, Any],
    model: str = DEFAULT_MODEL,
    guidelines: Optional[str] = None,
    temperature: Optional[float] = None,
) -> Dict[str, Any]:
    """Call OpenAI to audit a decoded word. Returns a JSON-like dict.

    Requires OPENAI_API_KEY in environment (dotenv supported).
    """
    client = OpenAI()

    prompt = build_audit_prompt(word, decoded, guidelines)

    # Request JSON-style response; models may still produce text, so parse defensively
    api_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise, critical auditor. Be concise and evidence-driven."},
            {"role": "user", "content": prompt},
        ],
    }
    # Some models do not support explicit temperature; include only if provided
    if temperature is not None:
        api_kwargs["temperature"] = temperature

    resp = client.chat.completions.create(**api_kwargs)

    content = resp.choices[0].message.content if resp and resp.choices else "{}"
    try:
        data = json.loads(content)
    except Exception:
        data = {"raw": content}
    # Attach model metadata
    data.setdefault("_meta", {})
    data["_meta"].update({
        "model": model,
        "usage": getattr(resp, "usage", None) and resp.usage.model_dump() or None,
    })
    return data


# -----------------------------
# Stage 1: Descriptor-only guessing
# -----------------------------

def build_guess_prompt(descriptors: dict, k: int) -> str:
    """Construct a prompt that contains ONLY descriptors (no surface form)
    and asks the model to output a strict JSON object with a `guesses` array
    of English words (top-k) and nothing else.
    """
    # We avoid including the surface word, README, or any answer keys.
    # Descriptors should contain minimal hints: operators, payload tags/types, gloss.
    # Model is instructed to return only JSON.
    return (
        "You will be given descriptors of an English word's sub-lexical analysis.\n"
        "Do NOT reveal analysis steps. Infer the most likely surface words (English) that match.\n"
        f"Return exactly one JSON object with a single key `guesses` as a list of the top {k} words.\n"
        "Do not include confidence scores or any other fields.\n\n"
        f"Descriptors:\n{json.dumps(descriptors, ensure_ascii=False, indent=2)}\n\n"
        "Output only JSON like: {\"guesses\":[\"word1\",\"word2\",...]}"
    )


def extract_descriptors(decoded: dict) -> dict:
    """Reduce a decoded structure to descriptor-only signals that do not leak the surface word."""
    return {
        "operators": decoded.get("operators", []),
        "payloads": [p for p in decoded.get("payloads", []) if p],
        "gloss": decoded.get("gloss", ""),
        # provide morphology categories but not literal strings that could leak the word
        "morphology": {
            "has_prefix": bool(decoded.get("morphology", {}).get("prefix")),
            "has_suffix": bool(decoded.get("morphology", {}).get("suffix")),
            "root_len": len(decoded.get("morphology", {}).get("root", "") or ""),
        },
        # adjacency shape without characters
        "pairs_shape": [
            [len(op), (len(pay) if isinstance(pay, str) else 0)] for op, pay in decoded.get("pairs", [])
        ],
    }


def audit_guess(
    decoded: dict,
    k: int = 10,
    model: str = DEFAULT_MODEL,
    temperature: Optional[float] = None,
) -> dict:
    """Stage-1 auditor: provide only descriptors and request top-k guesses.

    Returns a dict: {"guesses": ["word1", ...]}
    """
    client = OpenAI()
    desc = extract_descriptors(decoded)
    prompt = build_guess_prompt(desc, k)

    api_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only strict JSON with key 'guesses'."},
            {"role": "user", "content": prompt},
        ],
    }
    if temperature is not None:
        api_kwargs["temperature"] = temperature

    resp = client.chat.completions.create(**api_kwargs)

    content = resp.choices[0].message.content if resp and resp.choices else "{}"
    try:
        data = json.loads(content)
    except Exception:
        # Fallback: try to salvage words from lines/commas
        words = []
        for line in content.splitlines():
            line = line.strip().strip("-•* ")
            if not line:
                continue
            # split on comma for simple lists
            words.extend([w.strip() for w in line.split(",") if w.strip()])
        data = {"guesses": words[:k]}
    # Ensure format
    guesses = data.get("guesses") or []
    guesses = [str(w) for w in guesses][:k]
    return {"guesses": guesses}


async def audit_guess_async(
    decoded: dict,
    k: int = 10,
    model: str = DEFAULT_MODEL,
    temperature: Optional[float] = None,
) -> dict:
    """Async variant for batch execution using AsyncOpenAI."""
    client = AsyncOpenAI()
    desc = extract_descriptors(decoded)
    prompt = build_guess_prompt(desc, k)

    api_kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Return only strict JSON with key 'guesses'."},
            {"role": "user", "content": prompt},
        ],
    }
    if temperature is not None:
        api_kwargs["temperature"] = temperature

    resp = await client.chat.completions.create(**api_kwargs)

    content = resp.choices[0].message.content if resp and resp.choices else "{}"
    try:
        data = json.loads(content)
    except Exception:
        words = []
        for line in (content or "").splitlines():
            line = line.strip().strip("-•* ")
            if not line:
                continue
            words.extend([w.strip() for w in line.split(",") if w.strip()])
        data = {"guesses": words[:k]}
    guesses = data.get("guesses") or []
    guesses = [str(w) for w in guesses][:k]
    return {"guesses": guesses}

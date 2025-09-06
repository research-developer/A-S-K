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

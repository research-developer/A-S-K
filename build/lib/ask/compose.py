from __future__ import annotations

from typing import Dict, Any


def compose_token(decoded: Dict[str, Any]) -> Dict[str, Any]:
    """Compose a minimal AST-like structure aligned with README's sketch."""
    surface = decoded["surface"]
    ops = decoded["operators"]
    payloads = decoded["payloads"]

    features = {
        "action": " → ".join([op for op in decoded.get("program", [])]) if decoded.get("program") else None,
        "type": "word",
    }

    token = {
        "Token": {
            "surface": surface,
            "morph": {"prefix": None, "root": None, "theme": None, "suffix": None},
            "operators": ops,
            "payloads": payloads,
            "features": features,
        }
    }

    node = {
        "GraphNode": {
            "id": None,
            "label": None,
            "type": "Token",
            "evidence": [],
            "confidence": None,
            "facets": {
                "operatorPath": ops,
                "payloadSchema": payloads,
            },
        }
    }

    return {**token, **node}

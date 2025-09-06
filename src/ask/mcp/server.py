"""MCP server skeleton for A-S-K.

This module defines a basic structure to expose A-S-K core services over MCP.
It intentionally avoids framework lock-in so we can wire to a specific MCP
implementation later (e.g., FastMCP or custom JSON-RPC transport).

Usage idea (pseudo):
    from ask.mcp.server import create_mcp_server
    server = create_mcp_server()
    server.run()

For now, we expose a simple class with async handlers that call into the
core services layer. A transport (websocket/stdio) can map incoming requests
with method names "decode" and "syntax" to these handlers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ask.core import get_services


@dataclass
class MCPResponse:
    ok: bool
    data: Any = None
    error: Optional[str] = None


class ASKMCPEndpoints:
    """Endpoint handlers that call A-S-K services."""

    def __init__(self, persist: Optional[bool] = None) -> None:
        self.services = get_services(persist=persist)

    async def decode(self, params: Dict[str, Any]) -> MCPResponse:
        try:
            word = params.get("word")
            if not word:
                return MCPResponse(ok=False, error="Missing 'word' parameter")
            res = self.services.decode(word)
            seq = res.decoded.get("sequence") or []
            # Minimal linear output: only types and head linkage
            minimal = [{
                "type": tok.get("type"),
                "head_id": tok.get("head_id"),
            } for tok in seq]
            return MCPResponse(ok=True, data={"sequence": minimal})
        except Exception as e:
            return MCPResponse(ok=False, error=str(e))

    async def syntax(self, params: Dict[str, Any]) -> MCPResponse:
        try:
            word = params.get("word")
            language = (params.get("language") or "english").lower()
            if not word:
                return MCPResponse(ok=False, error="Missing 'word' parameter")
            res = self.services.syntax(word, language=language)
            seq = getattr(res, "sequence", []) or []
            minimal = [{
                "type": tok.get("type"),
                "head_id": tok.get("head_id"),
            } for tok in seq]
            return MCPResponse(ok=True, data={"sequence": minimal})
        except Exception as e:
            return MCPResponse(ok=False, error=str(e))


def create_mcp_server(persist: Optional[bool] = None) -> ASKMCPEndpoints:
    """Factory to create endpoint set; wire into desired MCP runtime externally."""
    return ASKMCPEndpoints(persist=persist)

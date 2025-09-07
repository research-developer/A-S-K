"""Core services layer for A-S-K.

This package exposes a stable, UI-agnostic API that can be consumed by:
- CLI (ask.cli)
- Web API (ask.web.app)
- MCP Server (ask.mcp.server)

Keeping logic centralized here enforces separation of concerns and simplifies expansion.
"""

from .services import ASKServices, get_services

__all__ = [
    "ASKServices",
    "get_services",
]

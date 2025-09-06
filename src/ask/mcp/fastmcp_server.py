from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

from .server import create_mcp_server


def main() -> None:
    try:
        # FastMCP is a lightweight MCP framework
        from fastmcp import FastMCP
    except Exception as e:  # ImportError or other
        msg = (
            "fastmcp is not installed.\n\n"
            "To run the A-S-K MCP server, install FastMCP first:\n"
            "  pip install fastmcp\n\n"
            "Then run:\n"
            "  ask-mcp\n"
        )
        sys.stderr.write(msg)
        if os.environ.get("ASK_MCP_DEBUG"):
            sys.stderr.write(f"\n[ASK MCP] Import error: {e}\n")
        sys.exit(1)

    # Wire A-S-K endpoint handlers
    persist_env = os.environ.get("ASK_GLYPH_PERSIST")
    persist: Optional[bool] = None
    if persist_env is not None:
        persist = persist_env.lower() in ("1", "true", "yes", "on")
    endpoints = create_mcp_server(persist=persist)

    app = FastMCP("A-S-K MCP")

    @app.tool
    async def decode(word: str) -> Dict[str, Any]:
        """Decode a word using A-S-K's services.
        Returns the decoded JSON payload with operators, payloads, gloss, etc.
        """
        res = await endpoints.decode({"word": word})
        if res.ok:
            return {"ok": True, "data": res.data}
        return {"ok": False, "error": res.error or "unknown error"}

    @app.tool
    async def syntax(word: str, language: str = "english") -> Dict[str, Any]:
        """Parse a word into USK syntax with elements and morphology.
        language: english|latin
        """
        res = await endpoints.syntax({"word": word, "language": language})
        if res.ok:
            return {"ok": True, "data": res.data}
        return {"ok": False, "error": res.error or "unknown error"}

    # --- Game tools ---
    @app.tool
    async def test_me(length: int | None = None, include: list[str] | None = None, num: int = 3) -> Dict[str, Any]:
        """Start a new guessing game.
        Optional filters: exact length and characters to include; num controls number of tags returned.
        Returns { id, tags[, warning] } on success.
        """
        params: Dict[str, Any] = {"length": length, "include": include, "num": num}
        res = await endpoints.test_me(params)
        if res.ok:
            return {"ok": True, "data": res.data}
        return {"ok": False, "error": res.error or "unknown error"}

    @app.tool
    async def guess(id: str, guesses: list[str], reveal: bool = False) -> Dict[str, Any]:
        """Submit guesses for a game id.
        When reveal=true, also returns the underlying word.
        """
        res = await endpoints.guess({"id": id, "guesses": guesses, "reveal": reveal})
        if res.ok:
            return {"ok": True, "data": res.data}
        return {"ok": False, "error": res.error or "unknown error"}

    @app.tool
    async def merged_lists(section: str | None = None) -> Dict[str, Any]:
        """Return normalized list views from the merged glyph datasets.
        Optional section filter to return only one list.
        """
        res = await endpoints.merged_lists({"section": section} if section else {})
        if res.ok:
            return {"ok": True, "data": res.data}
        return {"ok": False, "error": res.error or "unknown error"}

    # Run using FastMCP's default transport (STDIO) for MCP clients
    app.run()


if __name__ == "__main__":
    main()

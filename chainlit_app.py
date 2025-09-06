from __future__ import annotations

"""
Chainlit app for A-S-K that routes user messages to the core services layer.

Usage:
  chainlit run chainlit_app.py -w

Commands:
  - "decode <word>"
  - "syntax <word> [language]"  (language defaults to "english")
  - "persist on|off"             (toggles glyph persistence)
  - "help"                       (show help)

This app does not reinvent any logic; it calls the centralized services in
`ask.core.services` so CLI, Web API, and MCP remain consistent.
"""

import os
from typing import Optional

import chainlit as cl

from ask.core import get_services
from ask.core.services import TYPE_COLORS

DEFAULT_LANGUAGE = "english"
PERSIST_ENV_DEFAULT = os.getenv("ASK_GLYPH_PERSIST")


def _coerce_bool(val: Optional[str | bool]) -> Optional[bool]:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("1", "true", "yes", "on"):  # truthy
        return True
    if s in ("0", "false", "no", "off"):  # falsy
        return False
    return None


@cl.on_chat_start
async def on_start():
    # Initialize session settings
    persist_default = _coerce_bool(PERSIST_ENV_DEFAULT)
    cl.user_session.set("persist", persist_default)
    cl.user_session.set("language", DEFAULT_LANGUAGE)

    # Show legend
    legend = "  ".join([
        f"[{TYPE_COLORS.get('val','yellow')}]Value[/{TYPE_COLORS.get('val','yellow')}]",
        f"[{TYPE_COLORS.get('op','blue')}]Operator[/{TYPE_COLORS.get('op','blue')}]",
        f"[{TYPE_COLORS.get('func','green')}]Function[/{TYPE_COLORS.get('func','green')}]",
        f"[{TYPE_COLORS.get('struct','orange1')}]Struct[/{TYPE_COLORS.get('struct','orange1')}]",
    ])
    await cl.Message(content=f"Legend:\n\n{legend}").send()

    await cl.Message(
        content=(
            "Commands:\n"
            "- decode <word>\n"
            "- syntax <word> [language]\n"
            "- persist on|off\n"
            "- help\n"
        )
    ).send()


def _services() -> any:
    persist = cl.user_session.get("persist")
    return get_services(persist=persist)


@cl.on_message
async def on_message(message: cl.Message):
    text = (message.content or "").strip()
    if not text:
        await cl.Message(content="Please enter a command. Type 'help' for options.").send()
        return

    parts = text.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "help":
        await cl.Message(
            content=(
                "Commands:\n"
                "- decode <word>\n"
                "- syntax <word> [language]\n"
                "- persist on|off\n"
                "- help\n"
            )
        ).send()
        return

    if cmd == "persist":
        if not args:
            current = cl.user_session.get("persist")
            await cl.Message(content=f"Persist is currently: {current}").send()
            return
        val = _coerce_bool(args[0])
        if val is None:
            await cl.Message(content="Usage: persist on|off").send()
            return
        cl.user_session.set("persist", val)
        await cl.Message(content=f"Persist set to: {val}").send()
        return

    if cmd == "decode":
        if not args:
            await cl.Message(content="Usage: decode <word>").send()
            return
        word = args[0]
        services = _services()
        res = services.decode(word).decoded
        # Render compact view similar to CLI
        operators = " → ".join(res.get("operators", []) or []) or "none"
        payloads = res.get("payloads", [])
        payload_str = ", ".join([(p if isinstance(p, str) else "—") for p in payloads]) if payloads else "none"
        gloss = res.get("gloss", "")
        conf = res.get("confidence", 0.0)
        await cl.Message(
            content=(
                f"Decoding: {word}\n\n"
                f"Operators: {operators}\n"
                f"Payloads: {payload_str}\n"
                f"Function: {gloss}\n"
                f"Confidence: {conf:.1%}\n"
            )
        ).send()
        return

    if cmd == "syntax":
        if not args:
            await cl.Message(content="Usage: syntax <word> [language]").send()
            return
        word = args[0]
        language = args[1] if len(args) > 1 else (cl.user_session.get("language") or DEFAULT_LANGUAGE)
        services = _services()
        res = services.syntax(word, language=language)
        # Render with legend colors applied only inside the bracketed syntax string (already colored by services)
        await cl.Message(
            content=(
                f"USK Syntax for '{word}' (lang={language}):\n\n"
                f"{res.syntax}\n\n"
                f"Confidence: {res.overall_confidence:.1%}\n"
            )
        ).send()
        return

    await cl.Message(content="Unknown command. Type 'help' for options.").send()

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

from ask.core.services import TYPE_COLORS
from ask.mcp.server import create_mcp_server

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

    # Initialize services and MCP server once per session
    mcp_server = create_mcp_server(persist=persist_default)
    cl.user_session.set("mcp_server", mcp_server)

    # Show legend using colored square emojis for cross-platform visibility
    legend = "  ".join([
        "🟨 Value",
        "🟦 Operator",
        "🟩 Function",
        "🟧 Struct",
    ])
    await cl.Message(content=f"Legend:\n\n{legend}").send()

    # Show primary actions
    await cl.Message(
        content="Choose an action or type a command:",
        actions=[
            cl.Action(name="decode_btn", label="Decode", payload={"action": "decode"}),
            cl.Action(name="syntax_btn", label="Syntax", payload={"action": "syntax"}),
            cl.Action(name="settings_btn", label="Settings", payload={"action": "settings"}),
        ],
    ).send()


def _mcp():
    # Retrieve the server instance from the session
    mcp_server = cl.user_session.get("mcp_server")
    if not mcp_server:
        # Fallback for safety, though it should always be present
        persist = cl.user_session.get("persist")
        mcp_server = create_mcp_server(persist=persist)
        cl.user_session.set("mcp_server", mcp_server)
    return mcp_server


def _msg_content(ans):
    """Safely extract content from AskUserMessage response across Chainlit versions."""
    if ans is None:
        return None
    # Object with attribute
    if hasattr(ans, "content"):
        return getattr(ans, "content", None)
    # Dict-like
    if isinstance(ans, dict):
        return ans.get("content")
    return None


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
        mcp = _mcp()
        mcp_res = await mcp.decode({"word": word})
        if not mcp_res.ok:
            await cl.Message(content=f"Error: {mcp_res.error}").send()
            return
        res = mcp_res.data or {}
        # Render compact view similar to CLI
        operators = " → ".join(res.get("operators", []) or []) or "none"
        payloads = res.get("payloads", [])
        payload_str = ", ".join([(p if isinstance(p, str) else "—") for p in payloads]) if payloads else "none"
        gloss = res.get("gloss", "")
        conf = res.get("confidence", 0.0)
        decode_el = cl.CustomElement(
            name="ASKDecode",
            props={
                "word": word,
                "operators": res.get("operators", []),
                "payloads": res.get("payloads", []),
                "pairs": res.get("pairs", []),
                "program": res.get("program"),
                "gloss": gloss,
                "confidence": conf,
            },
        )
        await cl.Message(
            content=(
                f"Decoding: {word}\n\n"
                f"Operators: {operators}\n"
                f"Payloads: {payload_str}\n"
                f"Function: {gloss}\n"
                f"Confidence: {conf:.1%}\n"
            ),
            elements=[decode_el],
        ).send()
        return

    if cmd == "syntax":
        if not args:
            await cl.Message(content="Usage: syntax <word> [language]").send()
            return
        word = args[0]
        language = args[1] if len(args) > 1 else (cl.user_session.get("language") or DEFAULT_LANGUAGE)
        mcp = _mcp()
        mcp_res = await mcp.syntax({"word": word, "language": language})
        if not mcp_res.ok:
            await cl.Message(content=f"Error: {mcp_res.error}").send()
            return
        res = mcp_res.data or {}
        # Render with legend colors applied only inside the bracketed syntax string (already colored by services)
        syntax_el = cl.CustomElement(
            name="ASKSyntax",
            props={
                "word": word,
                "language": language,
                "syntax": res.get("syntax"),
                "elements": res.get("elements", []),
                "overall_confidence": res.get("overall_confidence", 0.0),
            },
        )
        await cl.Message(
            content=(
                f"USK Syntax for '{word}' (lang={language}):\n\n"
                f"{res.get('syntax')}\n\n"
                f"Confidence: {res.get('overall_confidence', 0.0):.1%}\n"
            ),
            elements=[syntax_el],
        ).send()
        return

    await cl.Message(content="Unknown command. Type 'help' for options.").send()


@cl.action_callback("decode_btn")
async def on_decode_btn(action: cl.Action):
    # Ask user for the word to decode
    word_msg = await cl.AskUserMessage(content="Enter a word to decode:", timeout=120).send()
    word_txt = _msg_content(word_msg)
    if not word_txt:
        await cl.Message(content="No word provided.").send()
        return
    word = word_txt.strip()
    mcp = _mcp()
    mcp_res = await mcp.decode({"word": word})
    if not mcp_res.ok:
        await cl.Message(content=f"Error: {mcp_res.error}").send()
        return
    res = mcp_res.data or {}
    operators = " → ".join(res.get("operators", []) or []) or "none"
    payloads = res.get("payloads", [])
    payload_str = ", ".join([(p if isinstance(p, str) else "—") for p in payloads]) if payloads else "none"
    gloss = res.get("gloss", "")
    conf = res.get("confidence", 0.0)
    decode_el = cl.CustomElement(
        name="ASKDecode",
        props={
            "word": word,
            "operators": res.get("operators", []),
            "payloads": res.get("payloads", []),
            "pairs": res.get("pairs", []),
            "program": res.get("program"),
            "gloss": gloss,
            "confidence": conf,
        },
    )
    await cl.Message(
        content=(
            f"Decoding: {word}\n\n"
            f"Operators: {operators}\n"
            f"Payloads: {payload_str}\n"
            f"Function: {gloss}\n"
            f"Confidence: {conf:.1%}\n"
        ),
        elements=[decode_el],
    ).send()


@cl.action_callback("syntax_btn")
async def on_syntax_btn(action: cl.Action):
    word_msg = await cl.AskUserMessage(content="Enter a word to parse (syntax):", timeout=120).send()
    word_txt = _msg_content(word_msg)
    if not word_txt:
        await cl.Message(content="No word provided.").send()
        return
    word = word_txt.strip()
    # Optional language prompt
    current_lang = cl.user_session.get("language") or DEFAULT_LANGUAGE
    lang_msg = await cl.AskUserMessage(content=f"Language? (default: {current_lang})", timeout=120).send()
    lang_txt = _msg_content(lang_msg)
    language = (lang_txt.strip() if lang_txt else current_lang)
    mcp = _mcp()
    mcp_res = await mcp.syntax({"word": word, "language": language})
    if not mcp_res.ok:
        await cl.Message(content=f"Error: {mcp_res.error}").send()
        return
    res = mcp_res.data or {}
    syntax_el = cl.CustomElement(
        name="ASKSyntax",
        props={
            "word": word,
            "language": language,
            "syntax": res.get("syntax"),
            "elements": res.get("elements", []),
            "overall_confidence": res.get("overall_confidence", 0.0),
        },
    )
    await cl.Message(
        content=(
            f"USK Syntax for '{word}' (lang={language}):\n\n"
            f"{res.get('syntax')}\n\n"
            f"Confidence: {res.get('overall_confidence', 0.0):.1%}\n"
        ),
        elements=[syntax_el],
    ).send()


@cl.action_callback("settings_btn")
async def on_settings_btn(action: cl.Action):
    # Toggle persist
    curr = cl.user_session.get("persist")
    toggled = (not curr) if isinstance(curr, bool) else True
    cl.user_session.set("persist", toggled)
    # Update language if user wants
    current_lang = cl.user_session.get("language") or DEFAULT_LANGUAGE
    lang_msg = await cl.AskUserMessage(content=f"Set language (current: {current_lang}) or leave blank:", timeout=120).send()
    lang_txt = _msg_content(lang_msg)
    if lang_txt:
        cl.user_session.set("language", lang_txt.strip())
    new_lang = cl.user_session.get("language")
    await cl.Message(content=f"Settings updated. persist={toggled}, language={new_lang}").send()

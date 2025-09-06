from __future__ import annotations

import os
import uuid
from typing import Dict, Any

import pytest

from ask.mcp.server import ASKMCPEndpoints, MCPResponse


@pytest.fixture()
def endpoints(tmp_path, monkeypatch) -> ASKMCPEndpoints:
    # Force guesses to use an isolated temp directory so tests do not touch repo state
    monkeypatch.setenv("ASK_GUESS_DIR", str(tmp_path))
    ep = ASKMCPEndpoints(persist=False)
    # Also ensure no disk writes are required by keeping it in memory if desired
    # ep.guess_dir = None
    return ep


def _make_game(ep: ASKMCPEndpoints, word: str) -> Dict[str, Any]:
    gid = str(uuid.uuid4())
    record: Dict[str, Any] = {
        "id": gid,
        "word": word,
        "created_at": "2025-01-01T00:00:00Z",
        "params": {"length": None, "include": None, "num": 3},
        "tags": [],
        "attempts": [],
    }
    ep._save_game(gid, record)
    return {"gid": gid, "record": record}


def _call_guess(ep: ASKMCPEndpoints, gid: str, guesses, reveal=False) -> MCPResponse:
    return pytest.run(async_fn=ep.guess, params={"id": gid, "guesses": guesses, "reveal": reveal})


# Helper to run async endpoint methods from pytest without an event loop plugin
class _AsyncRunner:
    @staticmethod
    def run(async_fn, **kwargs):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(async_fn(kwargs))


# Patch pytest with a tiny helper for this module
pytest.run = _AsyncRunner.run  # type: ignore[attr-defined]


def test_guess_marks_correct_if_any_guess_matches(endpoints: ASKMCPEndpoints):
    game = _make_game(endpoints, word="Matrix")  # mixed case on purpose
    gid = game["gid"]

    # Correct guess not in last position should still be recognized
    resp = pytest.run(async_fn=endpoints.guess, id=gid, guesses=["foo", "matrix", "bar"], reveal=False)
    assert resp.ok is True
    assert resp.data["correct"] is True
    assert resp.data["attempts"] == 1


def test_guess_is_case_insensitive_and_trims(endpoints: ASKMCPEndpoints):
    game = _make_game(endpoints, word="present")
    gid = game["gid"]

    # Leading/trailing whitespace and case differences are tolerated
    resp = pytest.run(async_fn=endpoints.guess, id=gid, guesses=["  PREsEnt  "])  # noqa: E201
    assert resp.ok is True
    assert resp.data["correct"] is True


def test_guess_reveal_option_returns_secret(endpoints: ASKMCPEndpoints):
    secret = "stream"
    game = _make_game(endpoints, word=secret)
    gid = game["gid"]

    resp = pytest.run(async_fn=endpoints.guess, id=gid, guesses=["wrong"], reveal=True)
    assert resp.ok is True
    assert resp.data["correct"] is False
    assert resp.data.get("reveal", {}).get("word") == secret


def test_guess_increments_attempts(endpoints: ASKMCPEndpoints):
    game = _make_game(endpoints, word="rotate")
    gid = game["gid"]

    r1 = pytest.run(async_fn=endpoints.guess, id=gid, guesses=["foo"])  # incorrect
    r2 = pytest.run(async_fn=endpoints.guess, id=gid, guesses=["rotate"])  # correct

    assert r1.ok and r2.ok
    assert r1.data["attempts"] == 1
    assert r2.data["attempts"] == 2


def test_fallback_wordlist_has_been_expanded(endpoints: ASKMCPEndpoints):
    # Ensure our hard-coded fallback includes some of the newly added words.
    # We intentionally inspect the fallback list directly, because _load_corpus
    # prefers the on-disk corpus if present (which may not include these words).
    words = endpoints._fallback_words
    assert "iterator" in words
    assert "strategy" in words
    assert "fallback" in words

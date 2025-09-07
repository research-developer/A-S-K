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
from typing import Any, Dict, Optional, List, Tuple
import os
import json
import uuid
import random
import errno
import tempfile
from datetime import datetime, timezone
from pathlib import Path

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
        # Guesses storage directory
        override = os.getenv("ASK_GUESS_DIR")
        # Default to .cache/guesses for non-atomic, derived artifacts
        self.guess_dir: Optional[Path] = Path(override) if override else Path(".cache/guesses")
        self._memory_games: Dict[str, Dict[str, Any]] = {}
        # Try to create on-disk directory; on read-only FS, fallback to temp dir; otherwise use in-memory
        try:
            self.guess_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            # Read-only or permission denied; try temp dir
            if isinstance(e, OSError) and getattr(e, 'errno', None) not in (errno.EROFS, errno.EACCES):
                # Unknown error: still try temp fallback
                pass
            try:
                tmp = Path(tempfile.gettempdir()) / "ask-guesses"
                tmp.mkdir(parents=True, exist_ok=True)
                self.guess_dir = tmp
            except Exception:
                # Final fallback: disable filesystem persistence
                self.guess_dir = None
        # Fallback wordlist (lowercase)
        self._fallback_words: List[str] = [
            "ask","matrix","present","line","rotate","transform","stream",
            "manipulation","structure","index","object","kernel","process",
            "reason","symbol","carry","convert","strict","string","strong",
            # Expanded pool for more robust gameplay
            "system","design","pattern","module","adapter","bridge","facade",
            "iterator","observer","visitor","strategy","command","factory",
            "builder","proxy","singleton","compose","compile","analyze",
            "optimize","balance","cluster","feature","payload","operator",
            "combine","segment","enhance","gloss","decode","syntax","latin",
            "english","tag","context","behavior","position","preference",
            "evidence","confidence","mapping","lookup","search","filter",
            "random","choice","select","length","include","persist",
            "storage","memory","filesystem","temporary","fallback","default",
        ]

    # -------- Utility helpers --------
    def _load_corpus(self) -> List[str]:
        """Load a word corpus, preferring .cache/decoded_words.jsonl, then data/decoded_words.jsonl; fallback to in-code list."""
        cache_jsonl = Path(".cache/decoded_words.jsonl")
        data_jsonl = Path("data/decoded_words.jsonl")
        jsonl = cache_jsonl if cache_jsonl.exists() else data_jsonl
        words: List[str] = []
        if jsonl.exists():
            try:
                with jsonl.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                            w = (rec.get("word") or rec.get("surface") or "").strip()
                            if w:
                                words.append(w.lower())
                        except Exception:
                            continue
            except Exception:
                # On any issue, return fallback
                return list(self._fallback_words)
        return words or list(self._fallback_words)

    def _filter_words(self, words: List[str], length: Optional[int], include: Optional[List[str]]) -> List[str]:
        result = [w for w in words]
        if length is not None and length > 0:
            result = [w for w in result if len(w) == int(length)]
        if include:
            inc = [c.lower() for c in include if isinstance(c, str) and c]
            if inc:
                result = [w for w in result if all(ch in w for ch in inc)]
        return result

    def _pick_word(self, length: Optional[int], include: Optional[List[str]]) -> Tuple[Optional[str], Optional[str]]:
        """Pick a word using filters. Returns (word, error)."""
        words = self._load_corpus()
        candidates = self._filter_words(words, length, include)
        if not candidates:
            return None, "No words match the given filters"
        return random.choice(candidates), None

    def _linear_tags(self, word: str) -> List[str]:
        """Build a left-to-right linear tag list from the enhanced decode.
        We interleave operator names and payload tags per step.
        """
        decoded = self.services.decode(word).decoded
        ops = list(decoded.get("operators") or [])
        pays = list(decoded.get("payloads") or [])
        tags: List[str] = []
        # Pair by index; append operator then payload tag if present
        for i, op in enumerate(ops):
            if op:
                tags.append(str(op))
            if i < len(pays) and pays[i]:
                tags.append(str(pays[i]))
        return tags

    def _save_game(self, gid: str, payload: Dict[str, Any]) -> None:
        # Prefer filesystem when available; otherwise store in memory
        if self.guess_dir is not None:
            try:
                tmp = self.guess_dir / f"{gid}.json.tmp"
                dst = self.guess_dir / f"{gid}.json"
                with tmp.open("w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2)
                tmp.replace(dst)
                return
            except Exception:
                # Fall back to memory store on any write error
                pass
        self._memory_games[gid] = payload

    def _load_game(self, gid: str) -> Dict[str, Any]:
        # Try filesystem first
        if self.guess_dir is not None:
            path = self.guess_dir / f"{gid}.json"
            if path.exists():
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
        # Fallback to memory store
        if gid in self._memory_games:
            return dict(self._memory_games[gid])
        raise FileNotFoundError(gid)

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

    async def test_me(self, params: Dict[str, Any]) -> MCPResponse:
        """Start a new guessing game.
        Params: length?: int, include?: list[str], num?: int (default 3)
        Returns: { id, tags[, warning] }
        """
        try:
            length = params.get("length")
            include = params.get("include")
            num = params.get("num", 3)

            if length is not None:
                try:
                    length = int(length)
                except Exception:
                    return MCPResponse(ok=False, error="length must be an integer")
            if include is not None and not isinstance(include, list):
                return MCPResponse(ok=False, error="include must be a list of characters")
            if not isinstance(num, int) or num < 0:
                return MCPResponse(ok=False, error="num must be a non-negative integer")

            word, err = self._pick_word(length=length, include=include)
            if err:
                return MCPResponse(ok=False, error=err)

            tags = self._linear_tags(word)
            warning = None
            if num == 0:
                out_tags: List[str] = []
            elif num > len(tags):
                out_tags = list(tags)
                warning = f"Requested num={num} exceeds available tags={len(tags)}; returning all"
            else:
                out_tags = tags[:num]

            gid = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()
            record = {
                "id": gid,
                "word": word,
                "created_at": now,
                "params": {"length": length, "include": include, "num": num},
                "tags": out_tags,
                "attempts": [],
            }
            self._save_game(gid, record)

            resp: Dict[str, Any] = {"id": gid, "tags": out_tags}
            if warning:
                resp["warning"] = warning
            return MCPResponse(ok=True, data=resp)
        except Exception as e:
            return MCPResponse(ok=False, error=str(e))

    async def guess(self, params: Dict[str, Any]) -> MCPResponse:
        """Submit guesses for an existing game id.
        Params: id: str, guesses: list[str], reveal?: bool
        Returns: { attempts, correct[, reveal: { word }] }
        """
        try:
            gid = params.get("id")
            guesses = params.get("guesses")
            reveal = bool(params.get("reveal", False))
            if not gid:
                return MCPResponse(ok=False, error="Missing 'id'")
            if not isinstance(guesses, list) or not guesses:
                return MCPResponse(ok=False, error="'guesses' must be a non-empty list")

            try:
                rec = self._load_game(gid)
            except FileNotFoundError:
                return MCPResponse(ok=False, error="Unknown game id")

            secret = str(rec.get("word", "")).strip().lower()
            # Consider any guess in the list correct if it matches the secret (case-insensitive, trimmed)
            normalized_guesses = [str(g).strip().lower() for g in guesses if g is not None]
            correct = secret in normalized_guesses if normalized_guesses else False
            now = datetime.now(timezone.utc).isoformat()
            attempt = {"at": now, "guesses": guesses, "correct": correct}
            rec.setdefault("attempts", []).append(attempt)
            self._save_game(gid, rec)

            data: Dict[str, Any] = {
                "attempts": len(rec.get("attempts", [])),
                "correct": correct,
            }
            if reveal:
                data["reveal"] = {"word": rec.get("word")}
            return MCPResponse(ok=True, data=data)
        except Exception as e:
            return MCPResponse(ok=False, error=str(e))

    async def merged_lists(self, params: Dict[str, Any]) -> MCPResponse:
        """Return normalized list views from merged glyph datasets.
        Optional params: { section?: str }
        Sections: vowels, payload_entries, operator_entries, complete_operator_entries,
        typed_payload_entries, cluster_entries, enhanced_cluster_entries, field_entries,
        tag_association_entries.
        """
        try:
            section = params.get("section") if params else None
            data = self.services.merged_lists(section=section)
            return MCPResponse(ok=True, data=data)
        except Exception as e:
            return MCPResponse(ok=False, error=str(e))


def create_mcp_server(persist: Optional[bool] = None) -> ASKMCPEndpoints:
    """Factory to create endpoint set; wire into desired MCP runtime externally."""
    return ASKMCPEndpoints(persist=persist)

from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional
import hashlib
import pathlib
from urllib.parse import urlparse

from firecrawl import Firecrawl
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables from a .env file if present
load_dotenv()


def _md_to_text(md: str) -> str:
    """Best-effort markdown -> plain text without bringing extra deps.
    - Strips code fences, links (keeps link text), images (keeps alt), emphasis, headings
    - Collapses multiple newlines
    This is intentionally lightweight; swap for a robust converter later if needed.
    """
    text = md
    # Remove code fences
    text = re.sub(r"```[\s\S]*?```", "\n", text)
    # Images ![alt](url) -> alt
    text = re.sub(r"!\[([^\]]*)\]\([^\)]*\)", r"\1", text)
    # Links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", text)
    # Inline code `code` -> code
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # Bold/italic **text** *text* __text__ _text_ -> text
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    text = re.sub(r"_([^_]+)_", r"\1", text)
    # Headings #### Title -> Title
    text = re.sub(r"^\s*#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Lists - item / * item / 1. item -> item
    text = re.sub(r"^\s*([*-]|\d+\.)\s+", "", text, flags=re.MULTILINE)
    # Blockquotes > quote -> quote
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    # Collapse excessive newlines and spaces
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def _get_client(api_key: Optional[str] = None) -> Firecrawl:
    key = api_key or os.getenv("FIRECRAWL_API_KEY")
    if not key:
        raise RuntimeError("FIRECRAWL_API_KEY is not set. Set env var or pass api_key explicitly.")
    return Firecrawl(api_key=key)


def _to_jsonable(obj: Any) -> Any:
    """Coerce Firecrawl SDK objects (e.g., DocumentMetadata) into plain dicts/lists.
    Keeps primitives as-is; falls back to str(obj) for unknown complex types.
    """
    # Primitives
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    # Dict
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    # List/Tuple
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    # Pydantic-like
    if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
        try:
            return _to_jsonable(obj.model_dump())
        except Exception:
            pass
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        try:
            return _to_jsonable(obj.dict())
        except Exception:
            pass
    # As a last resort, use __dict__ or str
    if hasattr(obj, "__dict__"):
        try:
            return _to_jsonable(vars(obj))
        except Exception:
            pass
    return str(obj)


def _safe_dirname(url: str, max_len: int = 80) -> str:
    """Create a filesystem-safe directory name from a URL.
    Format: {host}__{slug}__{short_hash}
    """
    p = urlparse(url)
    host = (p.netloc or "site").lower()
    path = p.path or "/"
    base = f"{host}__{path}"
    # replace non-alnum with '-'
    slug = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-")
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return f"{slug}__{h}"


def _write_cache(out_dir: pathlib.Path, url: str, markdown: Optional[str], text: Optional[str], metadata: Any) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "source_url.txt").write_text(url + "\n", encoding="utf-8")
    if markdown is not None:
        (out_dir / "article.md").write_text(markdown, encoding="utf-8")
    if text is not None:
        (out_dir / "article.txt").write_text(text, encoding="utf-8")
    if metadata is not None:
        import json as _json
        (out_dir / "metadata.json").write_text(_json.dumps(_to_jsonable(metadata), indent=2), encoding="utf-8")
    # Content hash for dedupe: prefer text, else markdown
    content_for_hash = (text or markdown or "").encode("utf-8")
    (out_dir / "content.sha256").write_text(hashlib.sha256(content_for_hash).hexdigest() + "\n", encoding="utf-8")


def _read_cache(cache_dir: pathlib.Path) -> Optional[Dict[str, Optional[str]]]:
    """Read cached artifacts if present. Returns dict or None if missing."""
    if not cache_dir.exists():
        return None
    url_path = cache_dir / "source_url.txt"
    text_path = cache_dir / "article.txt"
    md_path = cache_dir / "article.md"
    meta_path = cache_dir / "metadata.json"
    if not (url_path.exists() and (text_path.exists() or md_path.exists())):
        return None
    try:
        url = url_path.read_text(encoding="utf-8").strip()
        text = text_path.read_text(encoding="utf-8") if text_path.exists() else None
        markdown = md_path.read_text(encoding="utf-8") if md_path.exists() else None
        metadata = None
        if meta_path.exists():
            import json as _json
            metadata = _json.loads(meta_path.read_text(encoding="utf-8"))
        return {"url": url, "text": text, "markdown": markdown, "metadata": metadata, "cache_dir": str(cache_dir)}
    except Exception:
        return None


def extract_article(
    url: str,
    *,
    api_key: Optional[str] = None,
    save: bool = True,
    use_cache: bool = True,
    cache_root: Optional[str] = ".cache",
) -> Dict[str, Optional[str]]:
    """Extract minimalistic article content from a URL using Firecrawl.

    Returns a dict with keys:
      - url: the input URL
      - markdown: the main-content markdown (best effort)
      - text: plain text with markdown stripped
      - metadata: a subset of Firecrawl metadata if available
    """
    # Resolve cache directory for this URL
    cache_dir_str: Optional[str] = None
    cache_dir: Optional[pathlib.Path] = None
    if cache_root:
        cache_dir = pathlib.Path(cache_root) / _safe_dirname(url)
        cache_dir_str = str(cache_dir)

    # If cache is enabled and exists, return it to skip re-scraping
    if use_cache and cache_dir:
        cached = _read_cache(cache_dir)
        if cached:
            # Ensure URL matches; if not, fall through to scrape
            if cached.get("url") == url:
                return cached  # dedupe hit

    client = _get_client(api_key)

    # Request markdown and html; some sites may not yield markdown reliably
    result = client.scrape(url, formats=["markdown", "html"])  # SDK aggregates formats

    # Normalize SDK response into a dict-like structure
    data: dict = {}
    # Case 1: SDK returns object with .data dict
    if hasattr(result, "data") and isinstance(getattr(result, "data"), dict):
        data = getattr(result, "data") or {}
    # Case 2: SDK returns object with top-level attributes (markdown/html/metadata)
    elif any(hasattr(result, attr) for attr in ("markdown", "html", "metadata")):
        try:
            data = {
                "markdown": getattr(result, "markdown", None),
                "html": getattr(result, "html", None),
                "metadata": getattr(result, "metadata", None),
            }
        except Exception:
            data = {}
    # Case 3: SDK returns plain dict
    elif isinstance(result, dict):
        data = result.get("data") if "data" in result else result
    # Case 4: SDK returns list/tuple (unexpected for scrape, but handle defensively)
    elif isinstance(result, (list, tuple)) and result:
        first = result[0]
        if isinstance(first, dict):
            data = first
        elif hasattr(first, "__dict__"):
            try:
                data = vars(first)
            except Exception:
                data = {}

    markdown: Optional[str] = data.get("markdown") if isinstance(data, dict) else None
    raw_meta: Optional[Any] = data.get("metadata") if isinstance(data, dict) else None
    html: Optional[str] = data.get("html") if isinstance(data, dict) else None

    text: Optional[str] = None
    if markdown:
        text = _md_to_text(markdown)
    elif html:
        # Fallback: convert HTML to text using BeautifulSoup
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Remove non-content elements and common boilerplate containers
            for tag in soup(["script", "style", "noscript", "template"]):
                tag.decompose()
            for tag_name in ("header", "footer", "nav", "aside"):  # strip boilerplate
                for t in soup.find_all(tag_name):
                    t.decompose()
            # Prefer article/main if present
            main_region = soup.select_one("article") or soup.select_one("main")
            target = main_region or soup
            text = re.sub(r"\n{3,}", "\n\n", target.get_text(separator="\n").strip())
        except Exception:
            text = None

    metadata = _to_jsonable(raw_meta) if raw_meta is not None else None

    if save and cache_dir:
        _write_cache(cache_dir, url, markdown, text, metadata)

    return {
        "url": url,
        "markdown": markdown,
        "text": text,
        "metadata": metadata,
        "cache_dir": cache_dir_str,
    }

from __future__ import annotations

import json
from typing import Optional, List

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from .factorizer import decode_word
from .compose import compose_token
from .audit import audit_decoding
from .extractor import extract_article

app = typer.Typer(add_completion=False, help="A-S-K: A Semantic Kernel tools")
console = Console()


@app.command()
def decode(word: str, json_out: bool = typer.Option(False, help="Emit JSON only")):
    """Decode a WORD into operator/payload program and minimal AST."""
    decoded = decode_word(word)
    composed = compose_token(decoded)

    if json_out:
        typer.echo(json.dumps({"decoded": decoded, "ast": composed}, indent=2))
        raise typer.Exit()

    table = Table(title=f"Decoding: {word}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("operators", ", ".join(decoded["operators"]))
    table.add_row("payloads", ", ".join(decoded["payloads"]))
    table.add_row("program", " → ".join(decoded["program"]))
    console.print(table)

    print("\n[bold]AST (minimal):[/bold]")
    print(json.dumps(composed, indent=2))


@app.command()
def audit(
    word: str,
    model: str = typer.Option("gpt-5-mini", help="OpenAI model to use"),
    json_out: bool = typer.Option(True, help="Emit JSON (recommended)"),
    temperature: Optional[float] = typer.Option(None, help="Optional temperature; omit if model doesn't support"),
):
    """Audit a decoded WORD using an OpenAI model (requires OPENAI_API_KEY)."""
    decoded = decode_word(word)
    report = audit_decoding(word, decoded, model=model, temperature=temperature)
    if json_out:
        typer.echo(json.dumps({
            "word": word,
            "decoded": decoded,
            "audit": report,
        }, indent=2))
    else:
        console.print("[bold]Audit Report[/bold]")
        console.print(report)


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL of the article to extract"),
    json_out: bool = typer.Option(True, help="Emit JSON with markdown and text (recommended)"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Do not write cache files for this run"),
):
    """Extract minimalistic article text using Firecrawl.

    Requires FIRECRAWL_API_KEY to be set in the environment.
    """
    try:
        res = extract_article(url, save=(not no_cache))
    except Exception as e:
        typer.secho(f"Extraction failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if json_out:
        typer.echo(json.dumps(res, indent=2))
    else:
        # Print plain text only for piping into downstream tools
        text = res.get("text") or ""
        typer.echo(text)


@app.command(name="extract-batch")
def extract_batch(
    urls: List[str] = typer.Argument(None, help="One or more URLs to extract"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to a file containing URLs (one per line). Lines starting with # are ignored."),
    json_out: bool = typer.Option(True, help="Emit JSON list of results (recommended). With --no-json-out, prints plain text concatenated with separators."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Do not write cache files for this run"),
):
    """Batch extract minimalistic article text using Firecrawl.

    Accepts multiple URL arguments and/or --file with URLs per line.
    Results are cached under .cache/ per-URL.
    """
    inputs: List[str] = []
    if file:
        try:
            with open(file, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    inputs.append(line)
        except Exception as e:
            typer.secho(f"Failed to read file {file}: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    if urls:
        inputs.extend(urls)
    if not inputs:
        typer.secho("No URLs provided. Pass one or more URLs or use --file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    results: List[dict] = []
    for u in inputs:
        try:
            res = extract_article(u, save=(not no_cache))
            results.append(res)
        except Exception as e:
            results.append({"url": u, "error": str(e)})

    if json_out:
        typer.echo(json.dumps(results, indent=2))
    else:
        # Concatenate plain text with separators
        sep = "\n\n" + ("-" * 40) + "\n\n"
        texts = []
        for r in results:
            t = r.get("text") or ""
            texts.append(t)
        typer.echo(sep.join(texts))

def main():
    app()


if __name__ == "__main__":
    main()

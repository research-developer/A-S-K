from __future__ import annotations

import json
from typing import Optional, List
import asyncio

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .audit import audit_decoding, audit_guess, audit_guess_async
from .extractor import extract_article
from .enhanced_factorizer import (
    enhanced_decode_word,
    validate_ask_kernel,
    COMPLETE_OPERATOR_MAP,
    ENHANCED_CLUSTER_MAP,
)

app = typer.Typer(add_completion=False, help="A-S-K: Unified CLI (enhanced by default)")
console = Console()


@app.command()
def decode(
    word: str,
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed analysis"),
    simple: bool = typer.Option(False, "--simple", help="Minimal display (no morphology or details)"),
):
    """Decode a WORD using the enhanced factorizer.

    By default prints the enhanced view. Use --simple for a compact view, or --json for structured output.
    """
    decoded = enhanced_decode_word(word)

    if json_out:
        typer.echo(json.dumps(decoded, indent=2))
        raise typer.Exit()

    if simple:
        table = Table(title=f"Decoding: {word}")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Operators", " → ".join(decoded["operators"]) or "none")
        # Safely render payloads (None → em dash)
        payload_items = decoded.get("payloads", [])
        payload_str = ", ".join([(p if isinstance(p, str) else "—") for p in payload_items]) if payload_items else "none"
        table.add_row("Payloads", payload_str)
        table.add_row("Function", decoded.get("gloss", ""))
        conf = decoded.get("confidence", 0.0)
        conf_color = "green" if conf > 0.8 else "yellow" if conf > 0.6 else "red"
        table.add_row("Confidence", f"[{conf_color}]{conf:.1%}[/{conf_color}]")
        console.print(table)
        raise typer.Exit()

    # Enhanced default view
    table = Table(title=f"[bold cyan]Decoding: {word}[/bold cyan]")
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="white")

    morph = decoded.get("morphology", {})
    morph_str = f"prefix: {morph.get('prefix') or '—'}, root: {morph.get('root')}, suffix: {morph.get('suffix') or '—'}"
    table.add_row("Morphology", morph_str)
    table.add_row("Operators", " → ".join(decoded["operators"]) or "none")
    payload_items = decoded.get("payloads", [])
    payload_str = ", ".join([(p if isinstance(p, str) else "—") for p in payload_items]) if payload_items else "none"
    table.add_row("Payloads", payload_str)
    table.add_row("Function", decoded.get("gloss", ""))
    conf = decoded.get("confidence", 0.0)
    conf_color = "green" if conf > 0.8 else "yellow" if conf > 0.6 else "red"
    table.add_row("Confidence", f"[{conf_color}]{conf:.1%}[/{conf_color}]")
    console.print(table)

    # Validation panel
    if decoded.get("validation", {}).get("is_kernel"):
        panel = Panel(
            f"[bold green]✓ Semantic Kernel Validated[/bold green]\n{decoded['validation']['kernel_proof']}",
            title="[bold]ASK Proof[/bold]",
            border_style="green",
        )
        console.print(panel)

    if verbose:
        console.print("\n[bold]Detailed Analysis:[/bold]")
        if decoded.get("pairs"):
            console.print("[cyan]Adjacency Pairs (operator → payload):[/cyan]")
            for op, pay in decoded["pairs"]:
                console.print(f"  {op} → {pay or '—'}")

        # Operator details
        op_details = []
        for op in decoded.get("operators", []):
            for ch, info in COMPLETE_OPERATOR_MAP.items():
                if info["op"] == op:
                    op_details.append(f"  {op}: {info['principle']} [dim](conf: {info['confidence']:.0%})[/dim]")
                    break
        if op_details:
            console.print("\n[cyan]Operators:[/cyan]")
            for line in op_details:
                console.print(line)

        # Payload types
        typed = decoded.get("typed_payloads", [])
        if typed:
            console.print("\n[cyan]Payload Types:[/cyan]")
            for payload in typed:
                if not payload:
                    console.print("  — (none)")
                else:
                    console.print(f"  {payload['tag']}: {payload['principle']} [dim](type: {payload['type']})[/dim]")

        # Audit
        if decoded.get("audit"):
            a = decoded["audit"]
            status = a.get("verdict", "ok")
            color = "green" if status == "ok" else "yellow"
            console.print("\n[cyan]Audit:[/cyan]")
            console.print(f"  Verdict: [{color}]{status}[/{color}]  Confidence: {a.get('confidence', 0):.0%}")
            for issue in a.get("issues", []):
                console.print(f"  • {issue}")


@app.command()
def audit(
    word: str,
    model: str = typer.Option("gpt-5-mini", help="OpenAI model to use"),
    json_out: bool = typer.Option(True, help="Emit JSON (recommended)"),
    temperature: Optional[float] = typer.Option(None, help="Optional temperature; omit if model doesn't support"),
    guess: Optional[int] = typer.Option(
        None,
        "--guess",
        "-g",
        help="Also request top-K guesses from descriptors only. Use --guess for default K=10 or --guess 5 to set K.",
        flag_value=10,
    ),
):
    """Audit a decoded WORD using an OpenAI model (requires OPENAI_API_KEY)."""
    decoded = enhanced_decode_word(word)
    try:
        report = audit_decoding(word, decoded, model=model, temperature=temperature)
    except Exception as e:
        typer.secho(f"Audit failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    # Print the primary audit result first
    payload = {
        "word": word,
        "decoded": decoded,
        "audit": report,
    }
    if json_out:
        typer.echo(json.dumps(payload, indent=2))
    else:
        console.print("[bold]Audit Report[/bold]")
        console.print(report)

    # Optional: stage-1 guessing (descriptor-only)
    k: Optional[int] = guess  # when provided without value, Typer/Click sets flag_value=10
    if k:
        try:
            res = audit_guess(decoded, k=k, model=model, temperature=temperature)
        except Exception as e:
            typer.secho(f"Guessing failed: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        if json_out:
            # emit only the guesses array to keep stdout machine-consumable; user can combine as they like
            typer.echo(json.dumps({"guesses": res.get("guesses", [])}, indent=2))
        else:
            console.print(f"\n[bold]LLM Guesses (k={k}):[/bold]")
            for idx, g in enumerate(res.get("guesses", []), start=1):
                console.print(f"  {idx}. {g}")


@app.command(name="audit-guess")
def audit_guess_cmd(
    words: List[str] = typer.Argument(None, help="One or more words to guess (surface will NOT be sent to the model)"),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="Path to file containing words, one per line"),
    guesses: int = typer.Option(10, "--guesses", "-k", help="Top-K guesses to return"),
    model: str = typer.Option("gpt-5-mini", help="OpenAI model to use"),
    temperature: Optional[float] = typer.Option(None, help="Optional temperature; omit if model doesn't support"),
    json_out: bool = typer.Option(True, help="Emit JSON (recommended)"),
    use_async: bool = typer.Option(True, "--async", help="Use async batching when multiple inputs provided"),
):
    """Stage-1 auditor: Send ONLY descriptors to the model and request top-K surface word guesses.

    - For multiple inputs, you can pass words as arguments and/or via --file.
    - Uses async batching by default for throughput when multiple inputs are given.
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
    if words:
        inputs.extend(words)
    if not inputs:
        typer.secho("No words provided. Pass one or more words or use --file.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Do not send the surface forms to the model; only descriptors derived from the enhanced decoder
    from .enhanced_factorizer import enhanced_decode_word  # local import to avoid cycles

    # Single input: do simple sync call to avoid event loop overhead
    if len(inputs) == 1 or not use_async:
        w = inputs[0]
        decoded = enhanced_decode_word(w)
        try:
            res = audit_guess(decoded, k=guesses, model=model, temperature=temperature)
        except Exception as e:
            typer.secho(f"Audit-guess failed: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        payload = {"word": w, "guesses": res.get("guesses", [])}
        typer.echo(json.dumps(payload if json_out else res, indent=2) if json_out else ", ".join(payload["guesses"]))
        raise typer.Exit()

    # Multiple inputs: async batch
    async def _run_batch():
        tasks = []
        decodeds = []
        for w in inputs:
            d = enhanced_decode_word(w)
            decodeds.append((w, d))
            tasks.append(audit_guess_async(d, k=guesses, model=model, temperature=temperature))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out: List[dict] = []
        for (w, _), res in zip(decodeds, results):
            if isinstance(res, Exception):
                out.append({"word": w, "error": str(res)})
            else:
                out.append({"word": w, "guesses": res.get("guesses", [])})
        return out

    try:
        out = asyncio.run(_run_batch())
    except RuntimeError:
        # In case of already running loop (e.g., in notebooks), fallback to new loop
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            out = loop.run_until_complete(_run_batch())
        finally:
            loop.close()
    except Exception as e:
        typer.secho(f"Audit-guess batch failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if json_out:
        typer.echo(json.dumps(out, indent=2))
    else:
        # Print simple lines: word: g1, g2, ...
        for item in out:
            if "error" in item:
                typer.echo(f"{item['word']}: ERROR {item['error']}")
            else:
                typer.echo(f"{item['word']}: {', '.join(item.get('guesses', []))}")


@app.command()
def operators(
    confidence: float = typer.Option(0.0, "--min-confidence", "-c", help="Minimum confidence threshold"),
):
    """List all operators with their principles and confidence ratings."""
    table = Table(title="[bold cyan]Operator Map[/bold cyan]")
    table.add_column("Glyph", style="cyan", width=6)
    table.add_column("Operator", style="yellow", width=12)
    table.add_column("Principle", style="white", width=30)
    table.add_column("Confidence", justify="right", width=10)

    sorted_ops = sorted(COMPLETE_OPERATOR_MAP.items(), key=lambda x: x[1]["confidence"], reverse=True)
    for glyph, info in sorted_ops:
        if info["confidence"] >= confidence:
            conf_color = "green" if info["confidence"] > 0.85 else "yellow" if info["confidence"] > 0.75 else "red"
            table.add_row(glyph.upper(), info["op"], info["principle"], f"[{conf_color}]{info['confidence']:.0%}[/{conf_color}]")

    console.print(table)


@app.command()
def syntax(
    word: str,
    language: str = typer.Option("english", "--language", "-l", help="Language of the word (english|latin)"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    persist: bool = typer.Option(False, "--persist", help="Enable saving/loading glyph field confidence data"),
):
    """Parse a WORD into USK syntax using the state-aware parser.

    Use --persist to enable on-disk learning of glyph field confidences (overrides ASK_GLYPH_PERSIST).
    """
    # Local imports to avoid cycles
    from .state_syntax import USKParser, TYPE_COLORS
    from .glyph_fields import GlyphFieldSystem

    glyph_system = GlyphFieldSystem(persist=persist)
    parser = USKParser(glyph_system=glyph_system)
    result = parser.parse_word(word, language=language)

    if json_out:
        payload = {
            "word": word,
            "language": language,
            "usk": result.to_usk_syntax(),
            "elements": [
                {
                    "surface": e.surface,
                    "type": e.element_type.value,
                    "semantic": e.semantic,
                    "confidence": e.confidence,
                    "position": e.position,
                    "state": str(e.state) if e.state else None,
                }
                for e in result.elements
            ],
            "overall_confidence": result.overall_confidence,
            "morphology": result.morphology,
        }
        typer.echo(json.dumps(payload, indent=2))
        return

    # Legend panel
    legend_lines = []
    # Only show the four primary types as requested
    for key, label in [("val", "Value"), ("op", "Operator"), ("func", "Function"), ("struct", "Struct")]:
        color = TYPE_COLORS.get(key, "white")
        legend_lines.append(f"[{color}]{label}[/{color}]")
    legend_text = "  ".join(legend_lines)
    console.print(Panel(legend_text, title="Legend", border_style="cyan"))

    table = Table(title=f"[bold cyan]USK Syntax: {word}[/bold cyan]")
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Syntax", result.to_usk_syntax())
    table.add_row("Confidence", f"{result.overall_confidence:.1%}")
    morph = result.morphology or {}
    morph_str = f"prefix: {morph.get('prefix') or '—'}, root: {morph.get('root')}, suffix: {morph.get('suffix') or '—'}"
    table.add_row("Morphology", morph_str)
    console.print(table)

    # Brief breakdown
    if result.elements:
        console.print("\n[bold]Elements:[/bold]")
        # local mapping to shorten types for color selection
        from .state_syntax import ElementType
        type_map = {
            ElementType.OPERATOR: "op",
            ElementType.FUNCTION: "func",
            ElementType.PAYLOAD: "val",
            ElementType.MODIFIER: "mod",
            ElementType.STATE: "state",
        }
        for e in result.elements:
            short_type = type_map.get(e.element_type, "?")
            semantic = e.semantic
            if e.element_type == ElementType.PAYLOAD and isinstance(semantic, str) and semantic.startswith("struct("):
                short_type = "struct"
            color = TYPE_COLORS.get(short_type, None)
            colored_sem = f"[{color}]{semantic}[/{color}]" if color else semantic
            state_info = f" [{e.state}]" if e.state and str(e.state) != "?" else ""
            console.print(f"  {e.surface}: {colored_sem}{state_info} [dim]({e.position}, conf {e.confidence:.0%})[/dim]")

@app.command()
def clusters():
    """List all recognized consonant clusters and their operations."""
    table = Table(title="[bold cyan]Consonant Clusters[/bold cyan]")
    table.add_column("Cluster", style="cyan", width=8)
    table.add_column("Operations", style="yellow", width=30)
    table.add_column("Gloss", style="white", width=25)
    table.add_column("Confidence", justify="right", width=10)

    sorted_clusters = sorted(ENHANCED_CLUSTER_MAP.items(), key=lambda x: (-len(x[0]), x[0]))
    for cluster, info in sorted_clusters:
        conf_color = "green" if info["confidence"] > 0.85 else "yellow" if info["confidence"] > 0.70 else "red"
        table.add_row(cluster.upper(), " → ".join(info["ops"]), info["gloss"], f"[{conf_color}]{info['confidence']:.0%}[/{conf_color}]")

    console.print(table)


@app.command()
def validate():
    """Validate the ASK kernel proof and run self-tests."""
    console.print("[bold cyan]Validating the ASK Kernel...[/bold cyan]\n")
    try:
        result = validate_ask_kernel()
        if result:
            console.print("\n[bold green]✓ All validations passed![/bold green]")
        else:
            console.print("[bold red]✗ Validation failed[/bold red]")
    except Exception as e:
        console.print(f"[bold red]✗ Validation error: {e}[/bold red]")


@app.command()
def batch(
    words: str = typer.Argument(..., help="Comma-separated list of words"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Decode multiple words at once using the enhanced decoder."""
    word_list = [w.strip() for w in words.split(",")]
    results = []
    for w in word_list:
        decoded = enhanced_decode_word(w)
        if json_out:
            results.append(decoded)
        else:
            results.append({
                "word": w,
                "operators": decoded["operators"],
                "payloads": decoded["payloads"],
                "gloss": decoded["gloss"],
                "confidence": decoded["confidence"],
            })
    if json_out:
        typer.echo(json.dumps(results, indent=2))
    else:
        table = Table(title="[bold cyan]Batch Decoding[/bold cyan]")
        table.add_column("Word", style="cyan")
        table.add_column("Operators", style="yellow")
        table.add_column("Gloss", style="white")
        table.add_column("Conf", justify="right")
        for r in results:
            conf_color = "green" if r["confidence"] > 0.8 else "yellow" if r["confidence"] > 0.6 else "red"
            table.add_row(
                r["word"],
                " → ".join(r["operators"][:3]) + ("..." if len(r["operators"]) > 3 else ""),
                r["gloss"][:40] + ("..." if len(r["gloss"]) > 40 else ""),
                f"[{conf_color}]{r['confidence']:.0%}[/{conf_color}]",
            )
        console.print(table)


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

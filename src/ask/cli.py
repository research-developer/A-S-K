from __future__ import annotations

import json
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from .factorizer import decode_word
from .compose import compose_token

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


def main():
    app()


if __name__ == "__main__":
    main()

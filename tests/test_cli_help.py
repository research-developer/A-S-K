from __future__ import annotations

from typer.testing import CliRunner

from ask.CLI.main import app

runner = CliRunner()


def test_root_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "A-S-K: Unified CLI" in result.stdout


def test_syntax_help():
    result = runner.invoke(app, ["syntax", "--help"])
    assert result.exit_code == 0
    assert "Parse a WORD into USK syntax" in result.stdout

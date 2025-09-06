from __future__ import annotations

import json
from typing import Any, Dict, List

from typer.testing import CliRunner

from ask.cli import app
from ask.core import get_services

runner = CliRunner()


def _ok(result):
    assert result.exit_code == 0, f"CLI failed: {result.exit_code}\n{result.output}"


def test_decode_manipulation_json():
    result = runner.invoke(app, ["decode", "manipulation", "--json"])  # README example
    _ok(result)
    data = json.loads(result.stdout)
    assert data.get("surface") == "manipulation"
    assert isinstance(data.get("operators"), list)
    assert isinstance(data.get("payloads"), list)


def test_syntax_heaven_json():
    result = runner.invoke(app, ["syntax", "heaven", "--json"])  # README example
    _ok(result)
    data = json.loads(result.stdout)
    assert data.get("word") == "heaven"
    assert "usk" in data
    assert isinstance(data.get("elements"), list)


def test_operators_table():
    result = runner.invoke(app, ["operators"])  # README example
    _ok(result)
    # Spot-check header string
    assert "Operator Map" in result.stdout


def test_operators_filtered():
    result = runner.invoke(app, ["operators", "--min-confidence", "0.85"])  # README example
    _ok(result)
    assert "Operator Map" in result.stdout


def test_clusters_table():
    result = runner.invoke(app, ["clusters"])  # README example
    _ok(result)
    assert "Consonant Clusters" in result.stdout


def test_batch_json():
    result = runner.invoke(app, ["batch", "ask,think,understand,manipulation", "--json"])  # README example
    _ok(result)
    arr = json.loads(result.stdout)
    assert isinstance(arr, list)
    assert any(item.get("surface") == "ask" for item in arr)


def test_merged_lists_service():
    services = get_services()
    all_lists = services.merged_lists()
    # ensure keys exist and values are lists
    expected = [
        "vowels",
        "payload_entries",
        "operator_entries",
        "complete_operator_entries",
        "typed_payload_entries",
        "cluster_entries",
        "enhanced_cluster_entries",
        "field_entries",
        "tag_association_entries",
    ]
    for key in expected:
        assert key in all_lists, f"missing {key}"
        assert isinstance(all_lists[key], list), f"{key} should be a list"

    single = services.merged_lists("field_entries")
    assert list(single.keys()) == ["field_entries"]
    assert isinstance(single["field_entries"], list)

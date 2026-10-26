"""Unit tests for Agent-First Typer CLI (masar)."""

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from masar.cli import app

runner = CliRunner()


def test_cli_search_compact(mock_db_path):
    """Verify search command with --compact emits dense representation under 300 tokens."""
    result = runner.invoke(
        app,
        ["search", "--db", str(mock_db_path), "--seed", "إنما الأعمال بالنيات", "--compact"],
    )
    assert result.exit_code == 0
    output = result.stdout
    assert "bukhari" in output.lower() or "1" in output
    # Verify token thrifty length (under 1500 chars / ~300 tokens)
    assert len(output) < 1500


def test_cli_search_json_receipts(mock_db_path):
    """Verify search command with --format json --receipts returns valid structured JSON."""
    result = runner.invoke(
        app,
        [
            "search",
            "--db",
            str(mock_db_path),
            "--seed",
            "إنما الأعمال بالنيات",
            "--format",
            "json",
            "--receipts",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "receipt" in data[0]


def test_cli_inspect_and_split(mock_db_path, tmp_path):
    """Verify inspect command and adjusting split boundary via CLI."""
    curated_db = tmp_path / "masar-curated.db"
    
    # Inspect record 4
    res_inspect = runner.invoke(
        app,
        ["inspect", "--db", str(mock_db_path), "--id", "4"],
    )
    assert res_inspect.exit_code == 0
    assert "sahih_bukhari" in res_inspect.stdout

    # Split record 4
    res_split = runner.invoke(
        app,
        [
            "split",
            "--db",
            str(mock_db_path),
            "--curated-db",
            str(curated_db),
            "--id",
            "4",
            "--start",
            "149",
            "--end",
            "187",
        ],
    )
    assert res_split.exit_code == 0
    assert "149" in res_split.stdout


def test_cli_manual_add_and_session_undo(tmp_path):
    """Verify adding manual report and undoing action via CLI."""
    session_db = tmp_path / "session.db"

    # Add manual record
    raw_text = "حدثنا يحيى قال قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات"
    res_add = runner.invoke(
        app,
        [
            "add",
            "--session-db",
            str(session_db),
            "--text",
            raw_text,
            "--collection",
            "Rare MS",
            "--ref",
            "Folio 1a",
            "--family",
            "fam_test",
        ],
    )
    assert res_add.exit_code == 0
    assert "manual_" in res_add.stdout

    # Undo
    res_undo = runner.invoke(
        app,
        ["session", "undo", "--session-db", str(session_db)],
    )
    assert res_undo.exit_code == 0
    assert "Undone action: ADD" in res_undo.stdout

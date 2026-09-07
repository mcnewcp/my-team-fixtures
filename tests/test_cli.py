"""Tests for the textkit command-line interface."""

import json

import pytest

from textkit.cli import main


def test_slug_command_prints_slug(capsys):
    assert main(["slug", "Hello, World!"]) == 0
    assert capsys.readouterr().out == "hello-world\n"


@pytest.mark.parametrize("format_args", [[], ["--format", "text"]], ids=["default", "text"])
def test_stats_command_reports_counts(tmp_path, capsys, format_args):
    """Verify default and explicit text formats return the exact statistics report."""
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat sat on the mat the cat", encoding="utf-8")

    assert main(["stats", str(sample), *format_args]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == "words: 8\nchars: 30\ntop:\n  the: 3\n  cat: 2\n  mat: 1\n"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "the cat sat on the mat the cat",
            {"words": 8, "chars": 30, "top": [["the", 3], ["cat", 2], ["mat", 1]]},
        ),
        ("", {"words": 0, "chars": 0, "top": []}),
        ("Dog dog DOG cat", {"words": 4, "chars": 15, "top": [["dog", 3], ["cat", 1]]}),
        (" café\tCAFÉ\n", {"words": 2, "chars": 11, "top": [["café", 2]]}),
    ],
    ids=["sample", "empty", "mixed-case", "unicode-whitespace"],
)
def test_stats_command_reports_json(tmp_path, capsys, text, expected):
    """Verify JSON output returns ordered, typed statistics on one line."""
    sample = tmp_path / "sample.txt"
    sample.write_text(text, encoding="utf-8")

    assert main(["stats", str(sample), "--format", "json"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    decoded = json.loads(captured.out)
    assert decoded == expected
    assert list(decoded) == ["words", "chars", "top"]
    assert type(decoded["words"]) is int
    assert type(decoded["chars"]) is int
    assert isinstance(decoded["top"], list)
    for entry in decoded["top"]:
        assert isinstance(entry, list)
        assert len(entry) == 2
        assert isinstance(entry[0], str)
        assert type(entry[1]) is int
    assert captured.out.endswith("\n")
    assert captured.out.count("\n") == 1


def test_stats_command_rejects_an_invalid_format(tmp_path, capsys):
    """Verify an unsupported format returns a usage error without a report."""
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main(["stats", str(sample), "--format", "yaml"])

    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid choice" in captured.err
    assert "yaml" in captured.err


def test_stats_command_help_lists_formats(capsys):
    """Verify stats help returns the supported output formats."""
    with pytest.raises(SystemExit) as excinfo:
        main(["stats", "--help"])

    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "--format {text,json}" in captured.out


@pytest.mark.parametrize(
    "format_args",
    [[], ["--format", "text"], ["--format", "json"]],
    ids=["default", "text", "json"],
)
def test_stats_command_rejects_a_missing_file(tmp_path, capsys, format_args):
    """Verify every format returns the existing missing-file diagnostic."""
    missing_path = tmp_path / "nope.txt"
    with pytest.raises(SystemExit) as excinfo:
        main(["stats", str(missing_path), *format_args])
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"no such file: {missing_path}" in captured.err


def test_no_subcommand_is_a_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2

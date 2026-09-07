"""Tests for the textkit command-line interface."""

import pytest

from textkit.cli import main


def test_slug_command_prints_slug(capsys):
    assert main(["slug", "Hello, World!"]) == 0
    assert capsys.readouterr().out == "hello-world\n"


def test_stats_command_reports_counts(tmp_path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat sat on the mat the cat", encoding="utf-8")

    assert main(["stats", str(sample)]) == 0

    out = capsys.readouterr().out
    assert "words: 8" in out
    assert "chars: 30" in out
    assert "  the: 3" in out


def test_stats_command_rejects_a_missing_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["stats", str(tmp_path / "nope.txt")])
    assert excinfo.value.code == 2
    assert "no such file" in capsys.readouterr().err


def test_no_subcommand_is_a_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2


def test_stats_command_can_exclude_stopwords(tmp_path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat sat on the mat the cat", encoding="utf-8")

    assert main(["stats", str(sample), "--stopwords", "en"]) == 0

    out = capsys.readouterr().out
    assert out == "words: 8\nchars: 30\ntop:\n  cat: 2\n  mat: 1\n  sat: 1\n"


def test_stats_command_prints_empty_top_for_only_stopwords(tmp_path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("the of and", encoding="utf-8")

    assert main(["stats", str(sample), "--stopwords", "en"]) == 0
    assert capsys.readouterr().out == "words: 3\nchars: 10\ntop:\n"


def test_stats_command_rejects_unknown_stopword_language(tmp_path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main(["stats", str(sample), "--stopwords", "xx"])
    assert excinfo.value.code == 2
    assert "xx" in capsys.readouterr().err

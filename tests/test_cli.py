"""Tests for the textkit command-line interface."""

import pytest

from textkit.cli import main


def test_slug_command_prints_slug(capsys):
    assert main(["slug", "Hello, World!"]) == 0
    assert capsys.readouterr().out == "hello-world\n"


@pytest.mark.parametrize("options", [[], ["--language", "en"]])
def test_stats_command_reports_counts(tmp_path, capsys, options):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat sat on the mat the cat", encoding="utf-8")

    assert main(["stats", str(sample), *options]) == 0

    assert capsys.readouterr().out == "words: 4\nchars: 30\ntop:\n  cat: 2\n  mat: 1\n  sat: 1\n"


@pytest.mark.parametrize("options", [
    ["--no-stopwords"],
    ["--language", "en", "--no-stopwords"],
    ["--no-stopwords", "--language", "en"],
])
def test_stats_command_can_disable_stopwords(tmp_path, capsys, options):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat sat on the mat the cat", encoding="utf-8")

    assert main(["stats", str(sample), *options]) == 0
    assert capsys.readouterr().out == "words: 8\nchars: 30\ntop:\n  the: 3\n  cat: 2\n  mat: 1\n"


@pytest.mark.parametrize("language", ["fr", "EN", "english", "", " en "])
@pytest.mark.parametrize("options", [[], ["--no-stopwords"]])
def test_stats_command_rejects_unsupported_languages(tmp_path, capsys, language, options):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main(["stats", str(sample), "--language", language, *options])
    assert excinfo.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "--language: invalid choice" in captured.err
    assert repr(language) in captured.err
    assert "en" in captured.err


@pytest.mark.parametrize("text", ["", " \t\n ", "THE and Of"])
@pytest.mark.parametrize("options", [[], ["--language", "en"]])
def test_stats_command_prints_empty_rankings(tmp_path, capsys, text, options):
    sample = tmp_path / "sample.txt"
    sample.write_text(text, encoding="utf-8")

    assert main(["stats", str(sample), *options]) == 0
    assert capsys.readouterr().out == f"words: 0\nchars: {len(text)}\ntop:\n"


def test_stats_command_preserves_punctuation_and_whitespace(tmp_path, capsys):
    text = "THE\tCat\nand the, CAT\n"
    sample = tmp_path / "sample.txt"
    sample.write_text(text, encoding="utf-8")

    assert main(["stats", str(sample)]) == 0
    assert capsys.readouterr().out == f"words: 3\nchars: {len(text)}\ntop:\n  cat: 2\n  the,: 1\n"


def test_stats_command_limits_ranking_to_three_content_words(tmp_path, capsys):
    text = "the THE the and AND and of OF of zebra apple APPLE berry date"
    sample = tmp_path / "sample.txt"
    sample.write_text(text, encoding="utf-8")

    assert main(["stats", str(sample)]) == 0
    assert capsys.readouterr().out == (
        f"words: 5\nchars: {len(text)}\ntop:\n  apple: 2\n  berry: 1\n  date: 1\n"
    )


def test_stats_command_rejects_a_missing_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["stats", str(tmp_path / "nope.txt")])
    assert excinfo.value.code == 2
    assert "no such file" in capsys.readouterr().err


def test_no_subcommand_is_a_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code == 2

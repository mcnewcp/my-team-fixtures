"""Tests for textkit.slug."""

import pytest

from textkit import slugify


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Hello World", "hello-world"),
        ("  Trim   me  ", "trim-me"),
        ("Already-slugged", "already-slugged"),
        ("Punctuation!!! Everywhere???", "punctuation-everywhere"),
        ("Crème Brûlée", "creme-brulee"),
        ("Rev 2.0 / final", "rev-2-0-final"),
        ("snake_case_name", "snake-case-name"),
    ],
)
def test_slugify_examples(text, expected):
    assert slugify(text) == expected


def test_slugify_empty_and_symbol_only():
    assert slugify("") == ""
    assert slugify("!!! ???") == ""


def test_slugify_is_idempotent():
    once = slugify("Hello, World! 2026")
    assert slugify(once) == once


@pytest.mark.parametrize(
    ("text", "separator", "expected"),
    [
        ("Hello World", "_", "hello_world"),
        ("snake_case_name", "_", "snake_case_name"),
        ("  Trim   me  ", "_", "trim_me"),
        ("Hello, World! 2026", "", "helloworld2026"),
        ("Rev 2.0 / final", "__", "rev__2__0__final"),
    ],
)
def test_slugify_custom_separator(text, separator, expected):
    assert slugify(text, separator=separator) == expected


@pytest.mark.parametrize("separator", ["_", ""])
def test_slugify_custom_separator_is_idempotent(separator):
    once = slugify("Hello, World! 2026", separator=separator)
    assert slugify(once, separator=separator) == once


def test_slugify_max_length_defaults_to_no_cap():
    assert slugify("the quick brown fox") == "the-quick-brown-fox"
    assert len(slugify("the quick brown fox")) == 19
    assert slugify("the quick brown fox", max_length=100) == "the-quick-brown-fox"


@pytest.mark.parametrize(
    ("max_length", "expected"),
    [(10, "the-quick"), (9, "the-quick"), (8, "the")],
)
def test_slugify_max_length_cuts_back_to_whole_words(max_length, expected):
    assert slugify("the quick brown fox", max_length=max_length) == expected


def test_slugify_max_length_hard_cuts_a_single_long_word():
    assert slugify("the quick brown fox", max_length=2) == "th"


@pytest.mark.parametrize(
    ("separator", "max_length", "expected"),
    [("_", 10, "the_quick"), ("", 5, "thequ")],
)
def test_slugify_max_length_with_custom_separator(separator, max_length, expected):
    assert slugify("the quick brown fox", separator=separator, max_length=max_length) == expected


def test_slugify_truncated_output_is_stable():
    once = slugify("the quick brown fox", max_length=10)
    assert slugify(once, max_length=10) == once


def test_slugify_max_length_on_empty_and_symbol_only():
    assert slugify("", separator="_", max_length=5) == ""
    assert slugify("!!! ???", max_length=3) == ""


@pytest.mark.parametrize("separator", ["x", "1"])
def test_slugify_rejects_alphanumeric_separator(separator):
    with pytest.raises(ValueError):
        slugify("a b", separator=separator)


@pytest.mark.parametrize("max_length", [0, -1])
def test_slugify_rejects_non_positive_max_length(max_length):
    with pytest.raises(ValueError):
        slugify("a b", max_length=max_length)

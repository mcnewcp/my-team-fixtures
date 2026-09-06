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

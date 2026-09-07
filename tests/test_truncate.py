"""Tests for textkit.truncate."""

import pytest

from textkit import truncate


@pytest.mark.parametrize(
    ("text", "width"),
    [
        ("hello world", 20),
        ("hello world", 11),
        ("a", 1),
        ("  hi ", 10),
    ],
)
def test_truncate_returns_text_that_fits_unchanged(text, width):
    assert truncate(text, width) == text


@pytest.mark.parametrize(
    ("text", "width", "expected"),
    [
        ("hello world", 8, "hello…"),
        ("hello world foo", 12, "hello world…"),
        ("hello   world", 9, "hello…"),
        ("hello\nworld", 8, "hello…"),
    ],
)
def test_truncate_cuts_at_word_boundary(text, width, expected):
    assert truncate(text, width) == expected


def test_truncate_cuts_mid_word_when_no_boundary_fits():
    assert truncate("supercalifragilistic", 10) == "supercali…"


def test_truncate_accepts_custom_ellipsis():
    assert truncate("hello world", 6, ellipsis="...") == "hel..."
    assert truncate("hello world", 8, ellipsis="") == "hello"


def test_truncate_when_width_equals_ellipsis_length():
    assert truncate("a b", 1) == "…"
    assert truncate("a", 1) == "a"


@pytest.mark.parametrize(
    ("text", "width", "ellipsis"),
    [
        ("hello world", 0, "…"),
        ("hello world", 2, "..."),
        ("", 0, "…"),
    ],
)
def test_truncate_rejects_width_shorter_than_ellipsis(text, width, ellipsis):
    with pytest.raises(ValueError):
        truncate(text, width, ellipsis=ellipsis)


@pytest.mark.parametrize(
    ("text", "width", "ellipsis"),
    [
        ("hello world", 8, "…"),
        ("hello world foo", 12, "…"),
        ("supercalifragilistic", 10, "…"),
        ("a b", 1, "…"),
        ("hello world", 6, "..."),
        ("hello   world", 9, "…"),
        ("hello\nworld", 8, "…"),
        ("hello world", 8, ""),
    ],
)
def test_truncated_result_never_exceeds_width(text, width, ellipsis):
    assert len(truncate(text, width, ellipsis)) <= width

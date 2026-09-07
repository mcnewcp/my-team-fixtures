"""Tests for textkit.stopwords."""

import pytest

from textkit import stopwords_for


def test_english_list_is_lowercase_and_holds_common_function_words():
    words = stopwords_for("en")
    assert {"the", "on", "of", "and"} <= words
    assert all(word == word.lower() for word in words)


def test_unknown_language_raises_value_error_naming_it():
    with pytest.raises(ValueError, match="xx"):
        stopwords_for("xx")

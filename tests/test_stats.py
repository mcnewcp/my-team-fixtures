"""Tests for textkit.stats."""

import pytest

from textkit import char_count, top_words, word_count

SAMPLE = "the cat sat on the mat the cat"


def test_word_count_counts_whitespace_separated_tokens():
    assert word_count(SAMPLE) == 8
    assert word_count("  spaced   out \n words ") == 3


def test_word_count_of_empty_text_is_zero():
    assert word_count("") == 0
    assert word_count("   \n\t ") == 0


def test_char_count_includes_whitespace():
    assert char_count("ab c") == 4
    assert char_count("") == 0


def test_top_words_orders_by_count_then_alphabetically():
    assert top_words(SAMPLE, 3) == [("the", 3), ("cat", 2), ("mat", 1)]


def test_top_words_is_case_insensitive():
    assert top_words("Dog dog DOG cat", 1) == [("dog", 3)]


def test_top_words_edge_cases():
    assert top_words(SAMPLE, 0) == []
    assert top_words(SAMPLE, -1) == []
    assert len(top_words(SAMPLE, 99)) == 5


def test_top_words_can_exclude_english_stopwords():
    assert top_words(SAMPLE, 3, stopwords="en") == [("cat", 2), ("mat", 1), ("sat", 1)]


def test_top_words_removes_stopwords_before_truncating():
    assert len(top_words(SAMPLE, 99, stopwords="en")) == 3


def test_top_words_stopword_filter_is_case_insensitive():
    assert top_words("The THE the cat", 1, stopwords="en") == [("cat", 1)]


def test_top_words_of_only_stopwords_is_empty():
    assert top_words("the of and", 3, stopwords="en") == []


def test_top_words_rejects_unknown_stopword_language():
    with pytest.raises(ValueError, match="xx"):
        top_words(SAMPLE, 3, stopwords="xx")


def test_counts_are_not_affected_by_stopword_filtering():
    assert word_count(SAMPLE) == 8
    assert char_count(SAMPLE) == 30
    assert "the" not in dict(top_words(SAMPLE, 99, stopwords="en"))

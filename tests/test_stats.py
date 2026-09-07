"""Tests for textkit.stats."""

from textkit import char_count, top_words, word_count

SAMPLE = "the cat sat on the mat the cat"


def test_word_count_counts_whitespace_separated_tokens():
    assert word_count(SAMPLE) == 8
    assert word_count("  spaced   out \n words ") == 3


def test_word_count_ignores_non_alphanumeric_tokens():
    """Verify word counts exclude tokens without alphanumeric characters."""
    assert word_count("hello -- world") == 2
    assert word_count("one ... two") == 2
    assert word_count("* item") == 1


def test_word_count_preserves_qualifying_tokens():
    """Verify word counts retain punctuation-bearing and numeric words."""
    assert word_count("hello, world!") == 2
    assert word_count("don't stop") == 2
    assert word_count("2026 was fine") == 3


def test_word_count_of_empty_text_is_zero():
    assert word_count("") == 0
    assert word_count("   \n\t ") == 0
    assert word_count("   ") == 0
    assert word_count("-- ... !!!") == 0


def test_word_functions_accept_unicode_alphanumeric_tokens():
    """Verify word statistics retain Unicode letters and digits, excluding symbols."""
    assert word_count("é — ٣ _ 😀") == 2
    assert top_words("é — ٣ _ 😀", 5) == [("é", 1), ("٣", 1)]


def test_char_count_includes_whitespace():
    assert char_count("ab c") == 4
    assert char_count("") == 0
    assert char_count("-- ... !!!") == 10


def test_top_words_orders_by_count_then_alphabetically():
    assert top_words(SAMPLE, 3) == [("the", 3), ("cat", 2), ("mat", 1)]


def test_top_words_is_case_insensitive():
    assert top_words("Dog dog DOG cat", 1) == [("dog", 3)]
    assert top_words("Hello, HELLO, hello", 3) == [("hello,", 2), ("hello", 1)]


def test_top_words_ignores_non_alphanumeric_tokens():
    """Verify rankings exclude tokens without alphanumeric characters."""
    assert top_words("a -- a -- b", 2) == [("a", 2), ("b", 1)]
    assert top_words("", 5) == []
    assert top_words("   ", 5) == []
    assert top_words("-- ... !!!", 5) == []


def test_top_words_edge_cases():
    assert top_words(SAMPLE, 0) == []
    assert top_words(SAMPLE, -1) == []
    assert len(top_words(SAMPLE, 99)) == 5

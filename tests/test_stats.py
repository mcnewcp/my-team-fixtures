"""Tests for textkit.stats."""

import pytest

from textkit import char_count, top_words, word_count

SAMPLE = "the cat sat on the mat the cat"
ENGLISH_STOPWORDS = (
    "a an and are as at be been being but by for from had has have he her his i in is it its "
    "not of on or our she that the their them they this to was we were will with you your"
)


def test_word_count_counts_whitespace_separated_tokens():
    assert word_count(SAMPLE) == 4
    assert word_count("  spaced   out \n words ") == 3


def test_word_count_of_empty_text_is_zero():
    assert word_count("") == 0
    assert word_count("   \n\t ") == 0


def test_char_count_includes_whitespace():
    assert char_count("ab c") == 4
    assert char_count("") == 0
    assert char_count(SAMPLE) == 30


def test_top_words_orders_by_count_then_alphabetically():
    assert top_words(SAMPLE, 3) == [("cat", 2), ("mat", 1), ("sat", 1)]


def test_top_words_is_case_insensitive():
    assert top_words("THE the The Dog dog DOG cat", 1) == [("dog", 3)]


def test_top_words_edge_cases():
    assert top_words(SAMPLE, 0) == []
    assert top_words(SAMPLE, -1) == []
    assert top_words(SAMPLE, 99) == [("cat", 2), ("mat", 1), ("sat", 1)]


def test_explicit_english_filters_counts_and_ranking():
    assert word_count(SAMPLE, language="en") == 4
    assert top_words(SAMPLE, 3, language="en") == [("cat", 2), ("mat", 1), ("sat", 1)]


@pytest.mark.parametrize("stopword", ENGLISH_STOPWORDS.split())
def test_each_english_stopword_is_filtered_case_insensitively(stopword):
    text = f"{stopword} {stopword.upper()} Cat cat dog"
    assert word_count(text) == 3
    assert top_words(text, 3) == [("cat", 2), ("dog", 1)]
    assert word_count(text, language="en") == 3
    assert top_words(text, 3, language="en") == [("cat", 2), ("dog", 1)]


def test_filtering_precedes_truncation():
    text = "the THE the and AND and of OF of zebra apple APPLE berry"
    assert top_words(text, 3) == [("apple", 2), ("berry", 1), ("zebra", 1)]
    assert word_count(text) == 4


def test_disabling_filtering_restores_original_results():
    assert word_count(SAMPLE, language=None) == 8
    assert top_words(SAMPLE, 3, language=None) == [("the", 3), ("cat", 2), ("mat", 1)]
    assert top_words(SAMPLE, 99, language=None) == [
        ("the", 3), ("cat", 2), ("mat", 1), ("on", 1), ("sat", 1)
    ]
    assert word_count("THE the The", language=None) == 3
    assert top_words("THE the The", 3, language=None) == [("the", 3)]


@pytest.mark.parametrize("text", ["", " \t\n\r ", ENGLISH_STOPWORDS])
def test_empty_rankings_with_english_filtering(text):
    assert word_count(text) == 0
    assert top_words(text, 3) == []
    assert word_count(text, language="en") == 0
    assert top_words(text, 3, language="en") == []


@pytest.mark.parametrize("text", ["", " \t\n\r "])
def test_empty_input_with_filtering_disabled(text):
    assert word_count(text, language=None) == 0
    assert top_words(text, 3, language=None) == []


@pytest.mark.parametrize("language", ["en", None])
@pytest.mark.parametrize("n", [0, -1])
def test_nonpositive_limits_with_valid_configuration(language, n):
    assert top_words(SAMPLE, n, language=language) == []


def test_punctuation_remains_part_of_tokens():
    text = "the THE, the, and AND! cat."
    assert word_count(text) == 4
    assert top_words(text, 5) == [("the,", 2), ("and!", 1), ("cat.", 1)]
    assert word_count(text, language=None) == 6


def test_mixed_whitespace_preserves_token_boundaries():
    text = " \tTHE\nCat\r\nand\vcat\fDOG\u2003of "
    assert word_count(text) == 3
    assert top_words(text, 5) == [("cat", 2), ("dog", 1)]
    assert word_count(text, language=None) == 6


@pytest.mark.parametrize("language", ["fr", "EN", "english", "", " en "])
def test_word_count_rejects_unsupported_languages_even_for_empty_input(language):
    with pytest.raises(ValueError, match="[Uu]nsupported language"):
        word_count("", language=language)


@pytest.mark.parametrize("language", ["fr", "EN", "english", "", " en "])
@pytest.mark.parametrize("n", [3, 0, -1])
def test_top_words_rejects_unsupported_languages_before_early_returns(language, n):
    with pytest.raises(ValueError, match="[Uu]nsupported language"):
        top_words("", n, language=language)

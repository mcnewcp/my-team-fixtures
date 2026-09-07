"""Counting helpers for plain text."""

from __future__ import annotations

import re
from collections import Counter

_TOKEN = re.compile(r"\S+")

# Originally curated for textkit; no external corpus was used. This word-list data
# only is dedicated to the public domain under CC0-1.0.
_ENGLISH_STOPWORDS = frozenset(
    (
        "a", "an", "and", "are", "as", "at", "be", "been", "being", "but", "by", "for", "from",
        "had", "has", "have", "he", "her", "his", "i", "in", "is", "it", "its", "not", "of", "on",
        "or", "our", "she", "that", "the", "their", "them", "they", "this", "to", "was", "we",
        "were", "will", "with", "you", "your",
    )
)


def _stopwords(language: str | None) -> frozenset[str]:
    """Return the selected stopwords, raising ValueError for unsupported languages."""
    if language is None:
        return frozenset()
    if language == "en":
        return _ENGLISH_STOPWORDS
    raise ValueError(f"unsupported language {language!r}; expected 'en' or None")


def _tokens(text: str, stopwords: frozenset[str]) -> list[str]:
    """Return lowercase whitespace-separated tokens excluding the selected stopwords."""
    normalized = (token.lower() for token in _TOKEN.findall(text))
    return [token for token in normalized if token not in stopwords]


def word_count(text: str, *, language: str | None = "en") -> int:
    """Return the count of whitespace-separated words after stopword filtering.

    English (``language="en"``) is the default; ``None`` disables filtering.
    Other languages raise ValueError. Matching uses lower() and retains punctuation.
    """
    return len(_tokens(text, _stopwords(language)))


def char_count(text: str) -> int:
    """Return the number of characters in ``text``, whitespace included."""
    return len(text)


def top_words(text: str, n: int, *, language: str | None = "en") -> list[tuple[str, int]]:
    """Return up to ``n`` words after stopword filtering, most frequent first.

    English (``language="en"``) is the default; ``None`` disables filtering.
    Words use lower() normalization, retaining punctuation, with alphabetical ties.
    Unsupported languages raise ValueError even for non-positive ``n``; otherwise
    a non-positive ``n`` returns an empty list.
    """
    stopwords = _stopwords(language)
    if n <= 0:
        return []
    counts = Counter(_tokens(text, stopwords))
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]

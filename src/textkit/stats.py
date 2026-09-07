"""Counting helpers for plain text."""

from __future__ import annotations

import re
from collections import Counter

from .stopwords import stopwords_for

_TOKEN = re.compile(r"\S+")


def _tokens(text: str) -> list[str]:
    """Split ``text`` on whitespace and return the resulting tokens."""
    return _TOKEN.findall(text)


def word_count(text: str) -> int:
    """Return the number of whitespace-separated words in ``text``."""
    return len(_tokens(text))


def char_count(text: str) -> int:
    """Return the number of characters in ``text``, whitespace included."""
    return len(text)


def top_words(text: str, n: int, *, stopwords: str | None = None) -> list[tuple[str, int]]:
    """Return the ``n`` most frequent words in ``text``, most frequent first.

    Words are compared case-insensitively and ties are broken alphabetically,
    so the result is stable. A non-positive ``n`` returns an empty list. When
    ``stopwords`` is a language code (only ``"en"`` is supported), that language's
    stopwords are dropped before ranking; an unsupported code raises ``ValueError``.
    """
    excluded = stopwords_for(stopwords) if stopwords is not None else frozenset()
    if n <= 0:
        return []
    words = (token.lower() for token in _tokens(text))
    counts = Counter(word for word in words if word not in excluded)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]

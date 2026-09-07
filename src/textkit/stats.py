"""Counting helpers for plain text."""

from __future__ import annotations

import re
from collections import Counter

_TOKEN = re.compile(r"\S+")


def _tokens(text: str) -> list[str]:
    """Return whitespace-separated tokens containing at least one alphanumeric character."""
    return [token for token in _TOKEN.findall(text) if any(char.isalnum() for char in token)]


def word_count(text: str) -> int:
    """Return the count of whitespace-separated tokens with an alphanumeric character."""
    return len(_tokens(text))


def char_count(text: str) -> int:
    """Return the number of characters in ``text``, whitespace included."""
    return len(text)


def top_words(text: str, n: int) -> list[tuple[str, int]]:
    """Return the ``n`` most frequent words in ``text``, most frequent first.

    Words are whitespace-separated tokens containing at least one alphanumeric character.
    Words are compared case-insensitively and ties are broken alphabetically,
    so the result is stable. A non-positive ``n`` returns an empty list.
    """
    if n <= 0:
        return []
    counts = Counter(token.lower() for token in _tokens(text))
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]

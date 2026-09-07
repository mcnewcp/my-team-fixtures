"""Stopword lists used by :func:`textkit.stats.top_words`.

The English list below was written for this repository — it is not copied from any
third-party source — and is covered by the repository's own licence.
"""

from __future__ import annotations

_EN = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
        "will",
        "with",
    }
)

STOPWORDS: dict[str, frozenset[str]] = {"en": _EN}


def stopwords_for(language: str) -> frozenset[str]:
    """Return the lower-case stopword set for ``language`` (a code such as ``"en"``).

    Raises ``ValueError`` naming ``language`` when it is not supported.
    """
    try:
        return STOPWORDS[language]
    except KeyError:
        supported = ", ".join(sorted(STOPWORDS))
        msg = f"unsupported stopword language: {language!r} (supported: {supported})"
        raise ValueError(msg) from None

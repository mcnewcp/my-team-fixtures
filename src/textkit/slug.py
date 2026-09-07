"""URL-friendly slugs."""

from __future__ import annotations

import re
import unicodedata

_SEPARATOR_RUN = re.compile(r"[^a-z0-9]+")


def _to_ascii(text: str) -> str:
    """Fold ``text`` to ASCII, dropping accents and any character without an ASCII form."""
    decomposed = unicodedata.normalize("NFKD", text)
    return decomposed.encode("ascii", "ignore").decode("ascii")


def _validate_options(separator: str, max_length: int | None) -> None:
    """Raise ``ValueError`` for an alphanumeric ``separator`` or a ``max_length`` below 1."""
    if any(char.isascii() and char.isalnum() for char in separator):
        raise ValueError(f"separator must not contain letters or digits: {separator!r}")
    if max_length is not None and max_length < 1:
        raise ValueError(f"max_length must be at least 1, got {max_length}")


def _cut_to_whole_words(slug: str, separator: str, max_length: int) -> str:
    """Return ``slug`` cut to at most ``max_length`` characters, ending on a whole word.

    Backs up to the last ``separator`` that starts at or before ``max_length`` so the
    result never ends mid-word or with a trailing separator. Falls back to a plain
    character cut when the first word alone is longer than ``max_length`` or when
    ``separator`` is empty and there are no word boundaries to back up to.
    """
    if len(slug) <= max_length:
        return slug
    if separator:
        cut = slug.rfind(separator, 0, max_length + len(separator))
        if cut > 0:
            return slug[:cut]
    return slug[:max_length]


def slugify(text: str, separator: str = "-", max_length: int | None = None) -> str:
    """Return a lowercase ASCII slug for ``text`` with words joined by ``separator``.

    Accents are folded ("Crème" -> "creme"), every run of non-alphanumeric characters
    collapses to a single ``separator`` (default ``"-"``; ``""`` yields a compact slug with
    no separator at all), and a leading or trailing separator is removed. Text with no
    alphanumerics yields an empty string.

    When ``max_length`` is set, the slug is cut back to the last whole word that fits, so
    it is never longer than ``max_length`` characters and never ends with the separator.
    If the first word alone is longer than ``max_length``, or ``separator`` is empty so
    there are no word boundaries, the slug is hard-cut to ``max_length`` characters
    instead, so non-empty input still gives a non-empty slug.

    Raises ``ValueError`` if ``separator`` contains an ASCII letter or digit (such a
    separator cannot be told apart from word content, so re-slugifying would change the
    result) or if ``max_length`` is less than 1.
    """
    _validate_options(separator, max_length)
    slug = _SEPARATOR_RUN.sub(separator, _to_ascii(text).lower())
    slug = slug.removeprefix(separator).removesuffix(separator)
    if max_length is None:
        return slug
    return _cut_to_whole_words(slug, separator, max_length)

"""URL-friendly slugs."""

from __future__ import annotations

import re
import unicodedata

_SEPARATOR_RUN = re.compile(r"[^a-z0-9]+")


def _to_ascii(text: str) -> str:
    """Fold ``text`` to ASCII, dropping accents and any character without an ASCII form."""
    decomposed = unicodedata.normalize("NFKD", text)
    return decomposed.encode("ascii", "ignore").decode("ascii")


def slugify(text: str) -> str:
    """Return a lowercase, hyphen-separated ASCII slug for ``text``.

    Accents are folded ("Crème" -> "creme"), every run of non-alphanumeric
    characters collapses to a single hyphen, and leading and trailing hyphens
    are stripped. Text with no alphanumerics yields an empty string.
    """
    return _SEPARATOR_RUN.sub("-", _to_ascii(text).lower()).strip("-")

"""textkit — small, dependency-free helpers for working with plain text."""

from .slug import slugify
from .stats import char_count, top_words, word_count
from .truncate import truncate

__all__ = ["char_count", "slugify", "top_words", "truncate", "word_count"]
__version__ = "0.1.0"

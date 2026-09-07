"""Shorten text to a fixed width at a word boundary."""

from __future__ import annotations


def _boundary_head(text: str, room: int) -> str:
    """Return the longest prefix of ``text`` of length at most ``room`` ending at whitespace.

    Whitespace sitting exactly at index ``room`` counts as a boundary. When no
    whitespace occurs in ``text[:room + 1]`` the prefix is cut mid-word at ``room``.
    """
    for index in range(room, -1, -1):
        if text[index].isspace():
            return text[:index]
    return text[:room]


def truncate(text: str, width: int, ellipsis: str = "…") -> str:
    """Return ``text`` shortened to at most ``width`` characters.

    Returns ``text`` unchanged when it fits in ``width``. Otherwise returns the
    longest whitespace-bounded prefix that fits, with trailing whitespace
    stripped, followed by ``ellipsis``; the result's length never exceeds
    ``width``. Raises ``ValueError`` when ``width < len(ellipsis)``. Lengths are
    counted in code points.
    """
    if width < len(ellipsis):
        raise ValueError(f"width {width} is shorter than ellipsis {ellipsis!r}")
    if len(text) <= width:
        return text
    room = width - len(ellipsis)
    return _boundary_head(text, room).rstrip() + ellipsis

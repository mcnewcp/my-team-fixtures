## Problem

`textkit` exposes four public functions from `src/textkit/__init__.py`: `slugify` (`src/textkit/slug.py`) and `char_count`, `word_count`, `top_words` (`src/textkit/stats.py`). None of them shortens text. A caller who needs a string to fit a fixed column has to write `text[:width]` themselves, which cuts mid-word and gives no visible sign that anything was removed.

There is no `src/textkit/truncate.py`, no `truncate` name in `__all__`, and no `tests/test_truncate.py`. The CLI in `src/textkit/cli.py` exposes only `slug` and `stats` subcommands and is unaffected by this issue.

## Proposed outcome

A new module `src/textkit/truncate.py` defines `truncate(text: str, width: int, ellipsis: str = "…") -> str`, and `src/textkit/__init__.py` re-exports it so `from textkit import truncate` works and `"truncate"` appears in `textkit.__all__`.

Observable behaviour, with `room = width - len(ellipsis)`:

- `width < len(ellipsis)` raises `ValueError`. Assumes this check runs before the no-op check, so `truncate("", 0)` also raises, because an invalid `width` is a caller bug independent of the text.
- If `len(text) <= width`, the input string is returned unchanged (including any leading or trailing whitespace).
- Otherwise the result is `head.rstrip() + ellipsis` where `head` is the longest prefix of `text` of length at most `room` that ends at a whitespace boundary. A whitespace character sitting at index `room` itself counts as a boundary, so `truncate("hello world foo", 12)` yields `"hello world…"`, not `"hello…"`. If no whitespace occurs in `text[:room + 1]`, `head` is `text[:room]` (mid-word cut).
- Every truncated result has `len(result) <= width`; it may be shorter than `width`.
- Whitespace means any character for which `str.isspace()` is true (spaces, tabs, newlines), matching how `src/textkit/stats.py` tokenises on `\S+`.

Lengths are Python `len()` (code points), as the intent specifies. `src/textkit/cli.py` gains no subcommand.

## Affected users and systems

- `src/textkit/__init__.py` — public surface; gains the `truncate` import and `__all__` entry (currently alphabetical: `char_count`, `slugify`, `top_words`, `word_count`).
- `src/textkit/truncate.py` — new module holding the function.
- `tests/test_truncate.py` — new test module; pytest only collects `tests/` per `[tool.pytest.ini_options].testpaths` in `pyproject.toml`.
- `src/textkit/cli.py` and `tests/test_cli.py` — unchanged; `build_parser()` keeps exactly the `slug` and `stats` subparsers.
- `tests/test_slug.py`, `tests/test_stats.py` — unchanged, must keep passing.
- `pyproject.toml` — `dependencies = []` stays empty; no `uv.lock` change is needed.
- `README.md` lines 4-6 and the `description` field in `pyproject.toml` enumerate the public functions and will be stale after this change; the intent does not ask for a documentation update.
- Checks: `make test` and `make lint` (`Makefile`), also declared as `checks` in `factory.toml`.

## Constraints

- Runtime is standard library only: `pyproject.toml` declares `dependencies = []` and the intent forbids new dependencies.
- Python 3.12 or newer, from `requires-python = ">=3.12"` in `pyproject.toml`.
- Ruff line length 100, from `[tool.ruff]` in `pyproject.toml`; `make lint` runs `ruff check .` with the default rule set.
- Follow the module shape already used by `src/textkit/slug.py` and `src/textkit/stats.py`: module docstring, `from __future__ import annotations`, typed signature, private helpers prefixed with `_`.
- Tests import through the package (`from textkit import slugify` in `tests/test_slug.py`), so the new tests should import `truncate` from `textkit`, which also proves the re-export.
- `tests/test_truncate.py` must cover the six cases named in the intent: no-op, word-boundary cut, mid-word cut, custom multi-character ellipsis, `width == len(ellipsis)`, and the `ValueError`.
- Style and boundary conventions (small documented functions, no edits to `Makefile`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, no commits) come from `AGENTS.md`.

## Acceptance criteria

1. `from textkit import truncate` succeeds and `"truncate" in textkit.__all__` is true; `src/textkit/truncate.py` exists and defines the function.
2. `truncate("hello world", 20)` returns `"hello world"`.
3. `truncate("hello world", 11)` returns `"hello world"` (length equal to `width` is a no-op).
4. `truncate("hello world", 8)` returns `"hello…"`.
5. `truncate("supercalifragilistic", 10)` returns `"supercali…"`.
6. `truncate("a b", 1)` returns `"…"` (`width == len(ellipsis)`, text longer than `width`).
7. `truncate("a", 1)` returns `"a"` (`width == len(ellipsis)`, text fits).
8. `truncate("hello world", 6, ellipsis="...")` returns `"hel..."`.
9. `truncate("hello world", 0)` raises `ValueError`.
10. `truncate("hello world", 2, ellipsis="...")` raises `ValueError`.
11. `truncate("", 0)` raises `ValueError` (validation precedes the no-op check).
12. `truncate("hello world foo", 12)` returns `"hello world…"` (whitespace exactly at index `room` is a usable boundary).
13. `truncate("hello   world", 9)` returns `"hello…"` (trailing whitespace run is stripped before the ellipsis).
14. `truncate("hello\nworld", 8)` returns `"hello…"` (newline is a boundary).
15. `truncate("hello world", 8, ellipsis="")` returns `"hello"` (empty ellipsis is legal; `room == width`).
16. For every truncated result above, `len(result) <= width`.
17. `tests/test_truncate.py` exists under `tests/` and contains at least one test for each of: no-op, word-boundary cut, mid-word cut, multi-character ellipsis, `width == len(ellipsis)`, and `ValueError`; each test fails if the corresponding behaviour is removed.
18. `build_parser()` in `src/textkit/cli.py` still exposes only `slug` and `stats`; `main(["truncate", "x"])` exits with code 2.
19. `pyproject.toml` `dependencies` remains `[]` and `uv.lock` is unchanged.
20. `make test` and `make lint` both exit 0.

## Flagged concerns

- Off-by-one at the boundary: the obvious implementation `text[:room].rfind(" ")` misses a whitespace character at index `room` and returns `"hello…"` for `truncate("hello world foo", 12)`; criterion 12 exists to catch this.
- Validation order: the intent lists the `ValueError` rule after the no-op rule; this spec assumes eager validation so `truncate("", 0)` raises. If the plan chooses the other order, criterion 11 must change and the choice should be stated.
- Display width vs `len()`: the intent measures in code points, so East Asian wide characters, combining marks, and emoji sequences will not align in a real terminal column. This is accepted as specified, not a defect to fix here.
- Whitespace definition: only `str.isspace()` boundaries are used, so punctuation such as `-` or `/` is not a cut point; `truncate("foo-bar", 5)` gives `"foo-…"`. Consistent with `\S+` tokenisation in `src/textkit/stats.py`.
- A head that is all whitespace strips to empty and yields just the ellipsis, e.g. `truncate("   x", 2)` returns `"…"`. Deterministic but possibly surprising.
- Leading whitespace in a truncated head is preserved (only trailing whitespace is stripped), so `truncate("  hi there", 5)` returns `"  hi…"`.
- `README.md` and the `pyproject.toml` description enumerate the public functions and become incomplete; updating them is outside the intent's scope, so the reviewer should not require it and the implementer should not silently widen scope.
- Regression surface is small: nothing existing is modified except `src/textkit/__init__.py`, so a typo in `__all__` or the import is the only way to break `tests/test_slug.py` or `tests/test_stats.py`.
- Test quality: tests should assert on outputs, not on internal helpers, and should include at least one input where the boundary and mid-word strategies give different answers (criteria 4 and 5), otherwise a plain `text[:room] + ellipsis` implementation could pass.

## Open questions

None.

# Plan: add `truncate` to textkit (issue 5)

Adds one new public function, `truncate(text, width, ellipsis="…")`, in a new module, re-exports it from the package, and adds one new test module. Nothing else in the repository changes. No new dependencies, no `uv.lock` change, no CLI change, no documentation change.

## Files that change

- `tests/test_truncate.py` — new file. Imports `truncate` from `textkit` (proves the re-export) and holds the tests listed under Proof. Written first so `make test` fails before the implementation exists.
- `src/textkit/truncate.py` — new file. Defines the private helper `_boundary_head(text: str, room: int) -> str` and the public function `truncate(text: str, width: int, ellipsis: str = "…") -> str`. Follows the module shape of `src/textkit/slug.py`: module docstring, `from __future__ import annotations`, typed signature, `_`-prefixed helper, docstrings that say what is returned.
- `src/textkit/__init__.py` — add `from .truncate import truncate` after the existing `from .stats import ...` line and insert `"truncate"` into `__all__` keeping it alphabetical: `["char_count", "slugify", "top_words", "truncate", "word_count"]`.

No other path is touched. In particular `src/textkit/cli.py`, `tests/test_cli.py`, `tests/test_slug.py`, `tests/test_stats.py`, `pyproject.toml`, `uv.lock`, `README.md`, `Makefile`, `factory.toml`, `AGENTS.md`, `CLAUDE.md`, and `REVIEW.md` stay byte-for-byte identical.

## Design (no decisions left open)

Definitions: `room = width - len(ellipsis)`.

`truncate` body, in this exact order:

1. `if width < len(ellipsis): raise ValueError(f"width {width} is shorter than ellipsis {ellipsis!r}")`. This runs before anything else, so `truncate("", 0)` raises (spec's chosen validation order; criterion 11).
2. `if len(text) <= width: return text`. Returns the exact input object, whitespace untouched.
3. `room = width - len(ellipsis)`; `return _boundary_head(text, room).rstrip() + ellipsis`.

`_boundary_head(text, room)`: scan `index` from `room` down to `0` inclusive (`for index in range(room, -1, -1)`); if `text[index].isspace()` return `text[:index]`. If the loop finishes with no whitespace found, return `text[:room]`. Indexing `text[room]` is always safe because step 2 guarantees `len(text) > width >= room`.

Why scanning includes index `room`: a whitespace character sitting exactly at `text[room]` is a legal boundary, which is the off-by-one the spec flags. `text[:room].rfind(" ")` would miss it and would also miss tabs and newlines. Do not use `rfind(" ")`; use `str.isspace()`.

Worked results the implementation must reproduce (all with default `"…"` unless stated):

| call | room | head before rstrip | result |
|---|---|---|---|
| `truncate("hello world", 8)` | 7 | `"hello"` | `"hello…"` |
| `truncate("hello world foo", 12)` | 11 | `"hello world"` | `"hello world…"` |
| `truncate("supercalifragilistic", 10)` | 9 | `"supercali"` | `"supercali…"` |
| `truncate("a b", 1)` | 0 | `""` | `"…"` |
| `truncate("hello world", 6, ellipsis="...")` | 3 | `"hel"` | `"hel..."` |
| `truncate("hello   world", 9)` | 8 | `"hello  "` | `"hello…"` |
| `truncate("hello\nworld", 8)` | 7 | `"hello"` | `"hello…"` |
| `truncate("hello world", 8, ellipsis="")` | 8 | `"hello"` | `"hello"` |

Module docstring for `src/textkit/truncate.py`: `"""Shorten text to a fixed width at a word boundary."""`. The `truncate` docstring must state: returns `text` unchanged when it fits in `width`; otherwise the longest whitespace-bounded prefix that fits, trailing whitespace stripped, plus `ellipsis`; result length never exceeds `width`; raises `ValueError` when `width < len(ellipsis)`; lengths are code points. Keep every line under 100 characters.

## Order of work

1. Create `tests/test_truncate.py` with the module docstring `"""Tests for textkit.truncate."""`, `import pytest`, `from textkit import truncate`, and the test functions listed under Proof. Run `make test`: it must fail at collection with `ImportError: cannot import name 'truncate' from 'textkit'`. This is the failing-test-first proof for criteria 1 through 17.
2. Create `src/textkit/truncate.py` with `_boundary_head` and `truncate` exactly as described under Design.
3. Edit `src/textkit/__init__.py`: add `from .truncate import truncate` on the line after `from .stats import char_count, top_words, word_count`, and change `__all__` to `["char_count", "slugify", "top_words", "truncate", "word_count"]`. Run `make test`: every test in `tests/test_truncate.py` passes and `tests/test_slug.py`, `tests/test_stats.py`, `tests/test_cli.py` still pass.
4. Run `make lint`: exits 0 (ruff defaults are E and F; there are no unused imports because every imported name is used or listed in `__all__`).
5. Run the two CLI proof commands and the `git status --porcelain` command under Proof to confirm criteria 18 and 19 and that only the three named files are added or modified.

## Proof

Test functions the build must add in `tests/test_truncate.py` (names are exact; each imports `truncate` from `textkit`, never from `textkit.truncate`, so criterion 1 is exercised by every test):

- `test_truncate_returns_text_that_fits_unchanged` — parametrized over `("hello world", 20)`, `("hello world", 11)`, `("a", 1)`, `("  hi ", 10)`; asserts `truncate(text, width) == text`. Covers the no-op case, criteria 2, 3, 7, and the "leading/trailing whitespace preserved" rule.
- `test_truncate_cuts_at_word_boundary` — parametrized over `("hello world", 8, "hello…")`, `("hello world foo", 12, "hello world…")`, `("hello   world", 9, "hello…")`, `("hello\nworld", 8, "hello…")`. Covers criteria 4, 12, 13, 14. The `"hello world foo"` case fails on an `rfind`-style off-by-one; the newline case fails if only `" "` is treated as whitespace.
- `test_truncate_cuts_mid_word_when_no_boundary_fits` — asserts `truncate("supercalifragilistic", 10) == "supercali…"`. Criterion 5. Together with the boundary test above this rules out a plain `text[:room] + ellipsis` implementation (spec test-quality concern).
- `test_truncate_accepts_custom_ellipsis` — asserts `truncate("hello world", 6, ellipsis="...") == "hel..."` and `truncate("hello world", 8, ellipsis="") == "hello"`. Criteria 8 and 15 (multi-character and empty ellipsis).
- `test_truncate_when_width_equals_ellipsis_length` — asserts `truncate("a b", 1) == "…"` and `truncate("a", 1) == "a"`. Criteria 6 and 7.
- `test_truncate_rejects_width_shorter_than_ellipsis` — parametrized over `("hello world", 0, "…")`, `("hello world", 2, "...")`, `("", 0, "…")`; each wrapped in `pytest.raises(ValueError)`. Criteria 9, 10, 11. The empty-string case fails if the no-op check is moved before validation.
- `test_truncated_result_never_exceeds_width` — parametrized over every truncated call in the Design table (text, width, ellipsis); asserts `len(truncate(text, width, ellipsis)) <= width`. Criterion 16.

Commands, run from the repository root, and what a pass proves:

```
make test
```
Exit 0 with all tests in `tests/test_truncate.py`, `tests/test_slug.py`, `tests/test_stats.py`, and `tests/test_cli.py` passing. Proves criteria 1 through 17 and the "existing tests keep passing" rule, and half of criterion 20. Run once after step 1 to observe the `ImportError` failure, and again after step 3 to observe the pass.

```
make lint
```
Exit 0. Proves the other half of criterion 20: the new module and test file satisfy ruff defaults at line length 100.

```
uv run --frozen python -c "import textkit; assert 'truncate' in textkit.__all__; from textkit import truncate; print(truncate.__module__)"
```
Prints `textkit.truncate`. Proves criterion 1 directly: the name is in `__all__` and the function lives in `src/textkit/truncate.py`.

```
uv run --frozen python -c "from textkit.cli import build_parser; p = build_parser(); print(sorted(p._subparsers._group_actions[0].choices))"
```
Prints `['slug', 'stats']`. Proves the first half of criterion 18: no `truncate` subparser was added.

```
uv run --frozen python -c "from textkit.cli import main; main(['truncate', 'x'])"; echo "exit=$?"
```
Prints an argparse usage error on stderr and `exit=2`. Proves the second half of criterion 18.

```
git status --porcelain
```
Shows exactly `A`/`??` for `src/textkit/truncate.py` and `tests/test_truncate.py` and `M` for `src/textkit/__init__.py`, plus the pre-existing untracked `work/5/prompts/plan-1.md`. Proves criterion 19 (`pyproject.toml` and `uv.lock` untouched) and that the build stayed inside the Files-that-change list. Do not commit; the operator tooling owns commits.

## Risks

- **Off-by-one at index `room`.** The natural `text[:room].rfind(" ")` misses whitespace at `text[room]`. Mitigation: `_boundary_head` scans `range(room, -1, -1)` inclusive of `room`; `test_truncate_cuts_at_word_boundary` with `("hello world foo", 12)` catches a regression.
- **Whitespace definition too narrow.** Using `" "` instead of `str.isspace()` breaks tabs and newlines. Mitigation: the `"hello\nworld"` case in the boundary test.
- **Validation order.** If the no-op check is placed before the `ValueError` check, `truncate("", 0)` returns `""` and criterion 11 fails. Mitigation: the `("", 0, "…")` parametrized case in `test_truncate_rejects_width_shorter_than_ellipsis`. The plan adopts the spec's eager validation; criterion 11 stands unchanged.
- **`__all__` typo or missing import.** The only way to break `tests/test_slug.py` or `tests/test_stats.py`. Mitigation: `make test` runs the whole suite, and the `python -c` check on `__all__`.
- **Ruff F401 or E501.** An unused import in the new module, or a docstring line over 100 characters, fails `make lint`. Mitigation: `truncate.py` needs no imports beyond `from __future__ import annotations`; keep docstrings short.
- **Scope creep into docs or CLI.** `README.md` lines 4-6 and the `description` in `pyproject.toml` become stale. The spec explicitly excludes updating them; the build must not touch them and the reviewer must not require it. Likewise no `truncate` subcommand in `src/textkit/cli.py`.
- **Accepted behaviours the plan does not change** (from the spec's flagged concerns): lengths are code points, so wide characters and emoji will not align in a terminal; punctuation such as `-` is not a boundary (`truncate("foo-bar", 5)` gives `"foo-…"`); an all-whitespace head yields just the ellipsis (`truncate("   x", 2)` gives `"…"`); leading whitespace in a truncated head is preserved (`truncate("  hi there", 5)` gives `"  hi…"`). None are tested as requirements and none should be "fixed".
- **Protected files.** Nothing in the spec requires editing `Makefile`, `factory.toml`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, or any dotted config directory. No conflict.

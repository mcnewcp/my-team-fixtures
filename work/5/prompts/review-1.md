# Role: review (read-only)

You are the review role of an automated software factory, working on issue 5. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

Do not create, edit or delete any file. Do not run shell commands. Read files with your file-reading
tool only. The diff lives in a file inside this worktree (see "The diff under review"); read it
completely, continuing with offset/limit until the end, before you judge anything. You may also
read the repository for context around the diff.

## Review policy — apply exactly this

# Review policy

The default policy installed by `factory init`. Edit it in your repository; the reviewer applies
whatever this file says.

Review the diff, not the repository. A defect the diff does not touch is out of scope.

## Passes

Run all three, in order, and attribute every finding to one of them.

1. **bugs** — Correctness. Wrong logic, wrong boundary, unhandled error or exception path, `None`
   or empty-collection cases, off-by-one, resource or file-handle leaks, concurrency and ordering
   assumptions, a test that cannot fail, a test that asserts the implementation instead of the
   behaviour.
2. **security** — Injection (shell, SQL, path traversal), unvalidated external input, secrets or
   tokens in code, logs or error messages, credentials or environment leaking into subprocesses,
   unsafe deserialization, permissions widened, a check or sandbox weakened.
3. **compliance** — Against `spec.md` and `plan.md`. An acceptance criterion not met, behaviour
   the spec did not ask for, a file changed that the plan does not list, a proof command the plan
   promised and the build did not run, a stale plan after a deviation.

## Important vs nit

**Important** — the change is wrong, unsafe, or does not do what the spec and plan say. You can
name the failing input or condition and its consequence. It blocks the PR and a fixer will change
code for it. When in doubt between important and nit, and you cannot name the failure, it is a nit.

**nit** — everything else worth saying: clarity, a missing test for a secondary case, a comment
that no longer matches the code, a simpler equivalent. Nits never block and are never auto-fixed.

**Nit cap: 10 per round.** Exceeding it fails the round. Keep the most useful ones.

## Evidence

Every finding, important or nit, carries: the file path, the line in the new version (or `null`
when it is not tied to one line), and a quoted snippet from the diff. `detail` says what goes
wrong, under what input, with what consequence. No evidence, no finding.

Every finding already in the ledger and marked NEEDS UPDATE gets an update this round: `resolved`
with a quoted snippet from the diff that shows the fix, or `unresolved` with what is still wrong.
Never re-raise a finding recorded as resolved or dismissed; only a genuine regression visible in
this diff may be raised again, with evidence of the regression.

## Skip list

Do not report: formatting, whitespace, line length, import order; naming preferences; anything the
repository's linter, formatter, or type checker already enforces; architecture or dependency
choices the plan settled; pre-existing issues the diff does not touch; requests for more tests
when the plan's proof is satisfied; praise.

Nit cap enforced by the factory this round: 10. Exceeding it fails the round.


## The spec

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


## The plan

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


## The diff under review

The diff under review is not reproduced here. It is the file `.factory/tmp/review-1.diff`, relative to the root of this worktree: 4125 bytes, 132 lines.

Read it completely before you judge anything: start at the beginning and keep reading with offset/limit until you have seen line 132. A single read may return only the first part of the file. Do not review from a partial read.

## Check output from the last stage

$ make test
uv run --frozen pytest
.........................................                                [100%]
41 passed in 0.03s
[exit 0]
$ make lint
uv run --frozen ruff check .
All checks passed!
[exit 0]


## The ledger — findings already on record

(empty — first round)

## What to do

1. Run the policy's passes over the diff, in order: bugs, then security, then compliance against
   `spec.md` and `plan.md`. Judge the diff, not the rest of the repository: a pre-existing defect
   the diff does not touch is out of scope.
2. Give an update for EVERY finding the ledger marks NEEDS UPDATE — one entry in `updates` per id,
   no more, no fewer. `resolved` only when the diff demonstrably fixes it; cite the file, line and
   a quoted snippet from the diff that shows the fix. Otherwise `unresolved`, saying what is still
   wrong. A finding not marked NEEDS UPDATE gets no entry.
3. Raise a new finding only when you can point at it: `file` and `line` from the diff plus a
   quoted snippet in `evidence`, and a `detail` that says what goes wrong, under what input, with
   what consequence. Suspicion without a citation is not a finding.
4. Never re-raise a finding the ledger records as resolved or dismissed. An adjudicated finding
   cannot come back as new. If a resolved defect has genuinely returned in this diff, raise it as
   a new finding with the same title and evidence of the regression.

## Severity

- `important` = the change is wrong, unsafe, or does not do what the spec and plan say. It blocks
  the PR and a fixer will be asked to change code for it. Use it only when you can name the
  failure.
- `nit` = anything else worth saying. It never blocks and is never auto-fixed. Respect the nit cap
  stated in the policy: if you exceed it the round is rejected, so keep only the most useful ones.

Skip whatever the policy's skip list names. Do not report style, formatting, naming preference, or
anything a linter or formatter already enforces.

## Rules

- Burden of proof is on the finding. No finding without evidence from the diff.
- Titles are hashed to match findings across rounds: keep the title of a recurring defect
  identical in wording, short, and specific to one file.
- Do not propose patches or rewrite the code; state the defect and its consequence.
- Do not credit the build's claims that checks passed; the check output above is the record.
- An empty `new` list and every open finding resolved is a legitimate, welcome result.

## Stage note

This is review round 1 of issue 5, over the commit 0c4ed08ebc50 (0 fix round(s) so far).

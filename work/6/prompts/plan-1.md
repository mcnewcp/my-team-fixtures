# Role: plan (read-only)

You are the plan role of an automated software factory, working on issue 6. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

Do not create, edit or delete any file. Do not run shell commands. Read and search the repository as much as you need; the factory writes every file.

## The spec

## Problem

In `src/textkit/stats.py`, `_tokens` returns every match of `_TOKEN = re.compile(r"\S+")`. `word_count` counts that list, so standalone punctuation inflates results: `word_count("hello -- world")` returns `3` instead of `2`. `top_words` uses the same tokens and can rank punctuation alongside words.

In `src/textkit/cli.py`, `_format_stats` delegates to these functions, exposing incorrect values in the `words:` and `top:` sections of `textkit stats <file>`. Existing coverage in `tests/test_stats.py` and `tests/test_cli.py` does not exercise standalone punctuation.

## Proposed outcome

In `src/textkit/stats.py`, a whitespace-separated token qualifies as a word exactly when at least one of its characters satisfies `str.isalnum()`. `word_count` and `top_words` must share this qualification rule.

Qualifying tokens retain attached punctuation and internal apostrophes. Numeric and Unicode alphanumeric tokens qualify. `top_words` continues lowercasing qualifying tokens, ranking by descending frequency and then alphabetically, and respecting its existing `n` behavior. `char_count` continues counting every character, including whitespace and punctuation.

The existing delegation in `src/textkit/cli.py::_format_stats` must expose the corrected statistics while retaining the report format and three-entry maximum for `top:`.

## Affected users and systems

- Library callers: `src/textkit/stats.py::word_count` and `top_words`, including their public re-exports in `src/textkit/__init__.py`, receive corrected results.
- CLI users and output consumers: `pyproject.toml` registers `textkit.cli:main`; `src/textkit/cli.py::main` reads UTF-8 files and prints `_format_stats` output.
- Statistics tests: `tests/test_stats.py` requires regression examples and coverage preserving existing ranking, casing, whitespace, and character-count behavior.
- CLI tests: `tests/test_cli.py` requires coverage showing the corrected word count and top list through `main`.
- Documentation: descriptions in `src/textkit/stats.py::_tokens` and `word_count` must reflect qualification; `README.md` describes the public functions and plain-text CLI without specifying a conflicting token rule.
- Data and services: the affected path in `src/textkit/cli.py::main` reads a local file and prints a report; this change requires no stored-data migration, new output format, or external service.

## Constraints

- Keep the qualification rule shared within `src/textkit/stats.py`; both affected functions already consume `_tokens`. This requirement comes from `work/6/prompts/spec-1.md`.
- Preserve whitespace token boundaries and retained-token spelling apart from the existing lowercasing in `top_words`. The current behavior is established by `src/textkit/stats.py::_TOKEN`, `_tokens`, and `top_words`; the requested change only excludes tokens.
- Preserve public signatures, return types, and exports from `src/textkit/stats.py` and `src/textkit/__init__.py`.
- Preserve `top_words` frequency ordering, alphabetical tie breaks, non-positive `n` returning `[]`, and limits larger than the vocabulary returning all available entries, as implemented in `src/textkit/stats.py` and covered by `tests/test_stats.py`.
- Preserve `char_count` semantics and CLI labels, indentation, top-list limit, and successful exit status, as defined in `src/textkit/stats.py::char_count` and `src/textkit/cli.py`.
- Use the standard library and retain Python 3.12+ compatibility; `pyproject.toml` declares `dependencies = []` and `requires-python = ">=3.12"`.
- Repository conventions remain governed by `AGENTS.md`. Verification uses the existing `Makefile` targets; this specification stage does not execute checks.

## Acceptance criteria

1. In `tests/test_stats.py`, `word_count` returns `2` for `"hello -- world"`, `2` for `"one ... two"`, and `1` for `"* item"`.
2. In `tests/test_stats.py`, `word_count` returns `2` for `"hello, world!"`, `2` for `"don't stop"`, and `3` for `"2026 was fine"`.
3. In `tests/test_stats.py`, `word_count` returns `0` for each of `""`, `"   "`, and `"-- ... !!!"`; existing mixed-whitespace assertions remain valid.
4. In `tests/test_stats.py`, `top_words("a -- a -- b", 2)` returns `[("a", 2), ("b", 1)]`; empty, whitespace-only, and punctuation-only inputs return `[]` for positive `n`.
5. In `tests/test_stats.py`, `word_count("é — ٣ _ 😀")` returns `2`, and `top_words("é — ٣ _ 😀", 5)` returns `[("é", 1), ("٣", 1)]`, demonstrating Unicode alphanumeric qualification and rejection of tokens without any alphanumeric character.
6. In `tests/test_stats.py`, `top_words("Hello, HELLO, hello", 3)` returns `[("hello,", 2), ("hello", 1)]`; existing frequency, alphabetical tie-break, case-insensitivity, and `n` edge-case assertions continue passing.
7. In `tests/test_stats.py`, `char_count("-- ... !!!")` remains `10`, and existing character-count assertions continue passing.
8. In `tests/test_cli.py`, a UTF-8 file containing exactly `"a -- a -- b"` causes `main(["stats", path])` to return `0` and print exactly `"words: 3\nchars: 11\ntop:\n  a: 2\n  b: 1\n"`.
9. In `tests/test_cli.py`, a file containing exactly `"-- ... !!!"` produces `"words: 0\nchars: 10\ntop:\n"` with exit status `0`.
10. Review of `src/textkit/stats.py` confirms one shared token-qualification rule for both word functions and accurate affected docstrings. Existing assertions remain, with any expectations relying on punctuation counting corrected rather than deleted.
11. After implementation, `make test` and `make lint` both exit `0`.

## Flagged concerns

- Source verification: implementation files were inspected through GitHub’s `main` branch; their equality with the local worktree was not verified because no non-shell local reader was available. This spec assumes they match the locally listed paths and supplied issue description; the implementer should check for differences.
- Semantic breadth: the rule in `work/6/prompts/spec-1.md` excludes all tokens lacking alphanumeric characters, including standalone symbols, underscores, and emoji, even though the issue describes punctuation.
- Normalization regression: changing token boundaries or stripping attached punctuation would alter `src/textkit/stats.py::top_words` keys beyond the requested exclusion rule.
- Compatibility impact: counts and rankings from `src/textkit/stats.py` intentionally change for standalone punctuation, while `char_count` and the CLI report structure remain stable.

## Open questions

None.


## What to produce

`markdown` is an implementation plan someone who never saw this conversation can execute from,
with no further design decisions. Read the code you are planning to change before you name it.

The plan MUST contain these two headings, spelled exactly like this:

## Files that change

Every file the build will touch, listed by exact relative path from the repository root, one per
line, each with what changes in it and why. New files included. This list is a gate: the factory
rejects the build if it changes a path this section does not name verbatim, so be complete and be
literal — no globs, no directories standing in for files, no "and related tests".

## Proof

The exact commands that demonstrate the change works, and for each one what its passing output
proves. Name the test files and test functions the build must add or extend. If a bug is being
fixed, name the test that fails before the fix and passes after it. Include the repository's
check commands.

Also include, as further sections:

## Order of work
Numbered steps in the order the build should perform them. Failing test first wherever a test is
the proof. Each step small enough to be verified before the next begins.

## Risks
What could break, what is likely to be got wrong, and the mitigation or the check that catches
it. Include anything the spec flagged that the plan does not resolve.

## Rules

- Plan only what the spec asks for. Do not widen the scope, refactor for taste, or add
  dependencies the spec did not license.
- Prefer the smallest change that satisfies every acceptance criterion.
- Do not plan any edit to: `Makefile`, `factory.toml`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`,
  `.github/`, `.claude/`, `.codex/`, `.devcontainer/`, `.mcp.json`. They are protected and the
  build stage will fail on them. If the spec seems to require one, say so under Risks instead.
- Map every acceptance criterion in the spec to at least one step and one proof command.
- Conventions come from AGENTS.md. Do not restate them.
- Be concrete: function and class names, signatures, error cases, file paths. No prose that could
  describe any change.

## Stage note

(none)

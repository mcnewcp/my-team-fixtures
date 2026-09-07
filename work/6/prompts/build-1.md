# Role: build (write mode)

You are the build role of an automated software factory, working on issue 6. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

You may read, create and edit files in this worktree, and you may run `make`, `pytest`, `uv` and
`python`. Nothing else. Never run `git commit`, `git push`, `git add`, any other `git` write, or
`gh`. Never touch anything under `.github/`, `.claude/`, `.codex/`, `.devcontainer/`, and never
edit `Makefile`, `factory.toml`, `AGENTS.md`, `CLAUDE.md` or `REVIEW.md`. The factory commits,
pushes and talks to GitHub; a stage that edits a protected path is rejected and thrown away.
Under `work/` you may edit exactly one file: `work/6/plan.md`.

## The plan

## Files that change

- `src/textkit/stats.py` — Filter tokens once in `_tokens` using `str.isalnum()` and update the word-related docstrings to describe qualification.
- `tests/test_stats.py` — Add regression assertions for excluded tokens and preserve coverage of qualifying tokens, Unicode, casing, ranking, limits, whitespace, and character counts.
- `tests/test_cli.py` — Add exact-output punctuation regressions through `main` and strengthen the existing report test to verify the three-entry maximum.

## Order of work

1. **Confirm the local source before editing.** This plan inspected the files through `mcnewcp/my-team-fixtures` on GitHub’s `main` branch. Check that the local `_tokens` returns `_TOKEN.findall(text)`, both word functions consume `_tokens`, and `_format_stats` delegates to them with `TOP_WORDS_SHOWN = 3`. Confirm the existing test functions named below are present. Preserve local changes and existing assertions.

2. **Add the first failing regression.** In `tests/test_stats.py`, add `test_word_count_ignores_non_alphanumeric_tokens` with these assertions: `word_count("hello -- world") == 2`, `word_count("one ... two") == 2`, and `word_count("* item") == 1`. Run proof command P1 before changing production code; the current implementation must fail because it counts the standalone punctuation. This establishes acceptance criterion 1.

3. **Complete the library regression coverage.** Make the following changes in `tests/test_stats.py`, retaining its imports from the public `textkit` package:

   | Test function | Required assertions or preservation |
   | --- | --- |
   | Add `test_word_count_preserves_qualifying_tokens` | `word_count("hello, world!") == 2`; `word_count("don't stop") == 2`; `word_count("2026 was fine") == 3`. |
   | Extend `test_word_count_of_empty_text_is_zero` | Retain existing empty and mixed-whitespace assertions; add `word_count("   ") == 0` and `word_count("-- ... !!!") == 0`. |
   | Add `test_top_words_ignores_non_alphanumeric_tokens` | `top_words("a -- a -- b", 2) == [("a", 2), ("b", 1)]`; separately assert that `top_words` returns `[]` with `n=5` for `""`, `"   "`, and `"-- ... !!!"`. |
   | Add `test_word_functions_accept_unicode_alphanumeric_tokens` | `word_count("é — ٣ _ 😀") == 2`; `top_words("é — ٣ _ 😀", 5) == [("é", 1), ("٣", 1)]`. |
   | Extend `test_top_words_is_case_insensitive` | Retain its existing assertion; add `top_words("Hello, HELLO, hello", 3) == [("hello,", 2), ("hello", 1)]`. |
   | Extend `test_char_count_includes_whitespace` | Retain existing assertions; add `char_count("-- ... !!!") == 10`. |

   Preserve `test_word_count_counts_whitespace_separated_tokens`, `test_top_words_orders_by_count_then_alphabetically`, and `test_top_words_edge_cases`, including the existing zero, negative, and oversized `n` checks. This covers acceptance criteria 2–7 and preserves the assertions required by criterion 10.

4. **Add CLI regressions before the implementation.** In `tests/test_cli.py`, use `tmp_path` and `capsys`, writing each input with `encoding="utf-8"` and no appended newline. Both new tests must assert `main(["stats", str(sample)]) == 0` and exact captured stdout:

   | New test function | File contents | Expected stdout as a Python string literal |
   | --- | --- | --- |
   | `test_stats_command_ignores_standalone_punctuation` | `"a -- a -- b"` | `"words: 3\nchars: 11\ntop:\n  a: 2\n  b: 1\n"` |
   | `test_stats_command_with_only_punctuation` | `"-- ... !!!"` | `"words: 0\nchars: 10\ntop:\n"` |

   Extend `test_stats_command_reports_counts` by adding an exact assertion against its already captured `out`: `"words: 8\nchars: 30\ntop:\n  the: 3\n  cat: 2\n  mat: 1\n"`. Keep its existing assertions. Its five-word vocabulary makes this check verify the three-entry maximum as well as formatting. Run P2 now and confirm the new punctuation regressions fail for the intended incorrect counts or rankings. This covers acceptance criteria 8–9 and CLI compatibility.

5. **Implement the shared qualification rule.** In `src/textkit/stats.py::_tokens(text: str) -> list[str]`, replace its return expression with:

   ```python
   return [token for token in _TOKEN.findall(text) if any(char.isalnum() for char in token)]
   ```

   Update `_tokens`’s docstring to say it returns whitespace-separated tokens containing at least one alphanumeric character. Update `word_count`’s docstring to describe counting those tokens, and add that qualification definition to `top_words`’s docstring while retaining its casing, ordering, and `n` documentation. Keep the existing token regex, signatures, `word_count` delegation, `top_words` lowercasing and sorting, and `char_count` implementation. The existing CLI delegation and public exports already propagate the correction. This implements acceptance criteria 1–10.

6. **Verify the completed change.** Rerun P1 and P2, review P3, then run P4 and P5. All test and lint commands must exit zero. Confirm the patch contains only the three listed files. This completes acceptance criteria 10–11.

## Proof

Run these commands from the repository root during implementation. No tests or lint checks were executed during planning.

| ID | Exact command | Evidence |
| --- | --- | --- |
| P1 | `uv run --frozen pytest tests/test_stats.py::test_word_count_ignores_non_alphanumeric_tokens` | Must fail before the fix and pass afterward. Directly proves criterion 1 and the original bug’s correction. |
| P2 | `uv run --frozen pytest tests/test_stats.py tests/test_cli.py` | Before the fix, the new exclusion regressions must fail. Afterward, a passing summary proves criteria 1–9, public re-export behavior, preserved ranking and `n` behavior, exact CLI formatting, and the three-entry maximum. |
| P3 | `git diff -- src/textkit/stats.py tests/test_stats.py tests/test_cli.py` | Review the displayed patch to confirm criterion 10: one qualification rule in `_tokens`, both word functions still consuming it, accurate docstrings, and preserved existing assertions. Exit status alone does not prove these structural requirements. |
| P4 | `make test` | A passing pytest summary and exit status 0 prove the full repository suite passes, including unrelated slug and CLI error behavior; satisfies the test portion of criterion 11. |
| P5 | `make lint` | Ruff success and exit status 0 prove the patch satisfies the repository’s lint check; completes criterion 11. |

Acceptance mapping: criterion 1 → steps 2 and 5, P1/P2; criteria 2–7 → steps 3 and 5, P2; criteria 8–9 → steps 4 and 5, P2; criterion 10 → steps 3, 5, and 6, P3; criterion 11 → step 6, P4/P5.

## Risks

- **Local-source uncertainty remains:** source contents were inspected through GitHub’s `main` branch, and equality with the local worktree was not verified. Step 1 must resolve this before applying the change; material differences require reconciling the plan with the local source.
- **Qualification is broader than punctuation filtering:** standalone symbols, underscores, and emoji must also disappear, while Unicode letters and digits qualify. The Unicode regression catches ASCII-only rules and underscore acceptance.
- **Accidental normalization:** stripping punctuation, splitting apostrophes, or changing token boundaries would alter retained words. Filtering the existing regex matches preserves their spelling; the attached-punctuation and apostrophe assertions catch these regressions.
- **Library behavior intentionally changes:** excluded tokens lower word counts and disappear from rankings. Keep the existing lowercasing, frequency order, alphabetical ties, and `n` handling; P2 checks these contracts.
- **CLI and character-count regressions:** punctuation still contributes to character totals, and reports retain their labels, indentation, trailing newline, and top-list limit. Exact CLI assertions and the punctuation character-count assertion verify this.


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


## Checks

$ make test
uv run --frozen pytest
...................                                                      [100%]
19 passed in 0.03s
Using CPython 3.14.7
Creating virtual environment at: .venv
   Building textkit @ file:///home/mcnewcp/personal/my-team-fixtures/.factory/worktrees/6
      Built textkit @ file:///home/mcnewcp/personal/my-team-fixtures/.factory/worktrees/6
Installed 7 packages in 3ms
[exit 0]
$ make lint
uv run --frozen ruff check .
All checks passed!
[exit 0]


If that section is empty or says "(none)", the checks are `make test` and `make lint`.

## What to do

1. Implement the plan, in its stated order of work.
2. Where the plan names a test as the proof, write that test FIRST, run it, and see it fail for
   the right reason before you write the implementation.
3. Run the plan's proof commands and then the checks. Keep working until every one of them is
   green. A check you cannot make pass is a failed stage — report it in `summary` rather than
   weakening the check, deleting the test, or marking it skipped.
4. Do not commit. Leave the worktree dirty; the factory commits what you left.

## Staying inside the plan

The factory compares every path you changed against the "## Files that change" section of the
plan and rejects the build if a path is not listed there verbatim.

So if you deviate from the plan — a different file, an extra file, a different approach — update
`work/6/plan.md` in this same pass: add every new path to "## Files that change" by exact
relative path, and correct the steps and proof that changed. Then record the same deviation in
`deviations`. Deviating is allowed; leaving the plan stale is not.

## Rules

- Follow the repository's conventions from AGENTS.md. Do not restate or edit them.
- Make the smallest change that satisfies the plan. No unrequested refactors, renames,
  reformatting, dependency additions, or drive-by fixes; they enlarge the diff the reviewer must
  justify.
- Never weaken a test, an assertion, a type, or a lint rule to get to green.
- Do not fabricate results. Every command result you report must be one you actually ran.
- If the plan is wrong or impossible, implement what the spec requires, fix `plan.md`, and say so
  in `deviations`.

## Your answer

- `summary`: what you implemented, which files you changed, which tests you added, and the exact
  proof and check commands you ran with their outcome.
- `deviations`: one entry per departure from the plan (what the plan said, what you did, why), or
  an empty list if there were none.

## Stage note

The baseline checks were green before this session started.

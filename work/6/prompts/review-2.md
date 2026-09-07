# Role: review (read-only)

You are the review role of an automated software factory, working on issue 6. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

Do not create, edit or delete any file, and do not run anything that writes (tests, installs,
formatters, git commands that change state). Read with whatever read-only means your tools give
you: a file-reading/search tool if you have one, otherwise read-only shell commands such as
`cat`, `sed -n`, `grep`, `git diff`, `git log`. The diff lives in a file inside this worktree
(see "The diff under review"); read it completely before you judge anything — with a file tool,
continue with offset/limit until the end; with a shell, `cat` it, or walk it in slices with
`sed -n '1,400p'`, `sed -n '401,800p'` and so on. You may also read the repository for context
around the diff.

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


## The plan

## Files that change

- `src/textkit/stats.py` — Filter tokens once in `_tokens` using `str.isalnum()` and update the word-related docstrings to describe qualification.
- `tests/test_stats.py` — Add regression assertions for excluded tokens and preserve coverage of qualifying tokens, Unicode, casing, ranking, limits, whitespace, and character counts.
- `tests/test_cli.py` — Add exact-output punctuation regressions through `main` and strengthen the existing report test to verify the three-entry maximum.
- `work/6/plan.md` — Document the writable uv cache required by the build environment.

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

6. **Verify the completed change.** Rerun P1 and P2, review P3, then run P4 and P5. All test and lint commands must exit zero. Confirm the patch contains only the three implementation/test files and this plan update. This completes acceptance criteria 10–11.

## Proof

Run these commands from the repository root during implementation. No tests or lint checks were executed during planning.

Build environment adjustment: prefix P1, P2, P4, and P5 with
`UV_CACHE_DIR=/tmp/textkit-issue-6-uv-cache` so uv uses a writable cache. The first
unprefixed P1 attempt exited 2 before collecting tests because the default
`/home/mcnewcp/.cache/uv` cache could not acquire a lock on the read-only filesystem.
The prefixed P1 then failed as required because `word_count("hello -- world")`
returned 3 instead of 2.

| ID | Exact command | Evidence |
| --- | --- | --- |
| P1 | `uv run --frozen pytest tests/test_stats.py::test_word_count_ignores_non_alphanumeric_tokens` | Must fail before the fix and pass afterward. Directly proves criterion 1 and the original bug’s correction. |
| P2 | `uv run --frozen pytest tests/test_stats.py tests/test_cli.py` | Before the fix, the new exclusion regressions must fail. Afterward, a passing summary proves criteria 1–9, public re-export behavior, preserved ranking and `n` behavior, exact CLI formatting, and the three-entry maximum. |
| P3 | `git diff -- src/textkit/stats.py tests/test_stats.py tests/test_cli.py` | Review the displayed patch to confirm criterion 10: one qualification rule in `_tokens`, both word functions still consuming it, accurate docstrings, and preserved existing assertions. Exit status alone does not prove these structural requirements. |
| P4 | `make test` | A passing pytest summary and exit status 0 prove the full repository suite passes, including unrelated slug and CLI error behavior; satisfies the test portion of criterion 11. |
| P5 | `make lint` | Ruff success and exit status 0 prove the patch satisfies the repository’s lint check; completes criterion 11. |

Acceptance mapping: criterion 1 → steps 2 and 5, P1/P2; criteria 2–7 → steps 3 and 5, P2; criteria 8–9 → steps 4 and 5, P2; criterion 10 → steps 3, 5, and 6, P3; criterion 11 → step 6, P4/P5.

## Build deviations

- The plan specified proof/check commands without a cache override and changes to
  three files. The default uv cache was read-only, so P1, P2, P4, and P5 run with
  `UV_CACHE_DIR=/tmp/textkit-issue-6-uv-cache`; this plan is also updated to record
  that environment adjustment. The implementation and regression scope remain
  as planned.

## Risks

- **Local-source uncertainty remains:** source contents were inspected through GitHub’s `main` branch, and equality with the local worktree was not verified. Step 1 must resolve this before applying the change; material differences require reconciling the plan with the local source.
- **Qualification is broader than punctuation filtering:** standalone symbols, underscores, and emoji must also disappear, while Unicode letters and digits qualify. The Unicode regression catches ASCII-only rules and underscore acceptance.
- **Accidental normalization:** stripping punctuation, splitting apostrophes, or changing token boundaries would alter retained words. Filtering the existing regex matches preserves their spelling; the attached-punctuation and apostrophe assertions catch these regressions.
- **Library behavior intentionally changes:** excluded tokens lower word counts and disappear from rankings. Keep the existing lowercasing, frequency order, alphabetical ties, and `n` handling; P2 checks these contracts.
- **CLI and character-count regressions:** punctuation still contributes to character totals, and reports retain their labels, indentation, trailing newline, and top-list limit. Exact CLI assertions and the punctuation character-count assertion verify this.


## The diff under review

The diff under review is not reproduced here. It is the file `.factory/tmp/review-2.diff`, relative to the root of this worktree: 4521 bytes, 116 lines.

Read it completely before you judge anything: start at the beginning and keep going until you have seen line 116 — with a file-reading tool, continue with offset/limit; with a shell, `cat` the file, or walk it in slices with `sed -n '1,400p'`, `sed -n '401,800p'` and so on. A single read may return only the first part of the file. Do not review from a partial read.

## Check output from the last stage

$ make test
uv run --frozen pytest
.........................                                                [100%]
25 passed in 0.02s
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
5. Set `complete` true only when you read the whole diff and ran all three passes. If anything
   stopped you — the diff file was unreadable, a tool you needed was unavailable, you never got
   to the end of the file — set it false and say what stopped you in `summary`; the factory then
   throws the round away, because empty findings are not approval. `complete` true with an empty
   `new` list is the welcome result; `complete` false is not a way to hedge one.

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

This is review round 2 of issue 6, over the commit 21b5a8640eab (0 fix round(s) so far).

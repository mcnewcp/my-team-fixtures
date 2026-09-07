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

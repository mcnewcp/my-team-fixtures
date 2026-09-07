## Problem

`top_words()` in `src/textkit/stats.py` (lines 26–36) ranks every whitespace token in the text. Tokens come from `_tokens()` (`stats.py:11-13`), which uses the regex `\S+` (`stats.py:8`), so the only normalisation before counting is `token.lower()` on line 34. Nothing removes function words, so on any real document the highest counts belong to "the", "and", "of" and similar.

`textkit stats FILE` renders that ranking through `_format_stats()` in `src/textkit/cli.py` (lines 28–32), printing the top `TOP_WORDS_SHOWN = 3` entries (`cli.py:11`) under a `top:` heading after `words:` and `chars:` lines. The `stats` subparser (`cli.py:22-23`) takes only the `file` positional; there is no option to influence the ranking.

The repository's own sample makes the problem visible: for `"the cat sat on the mat the cat"` the top entry is `("the", 3)`, and both `tests/test_stats.py:24` and `tests/test_cli.py:22` assert exactly that. There is no stopword data anywhere under `src/textkit/`, no language concept in the public API (`src/textkit/__init__.py` exports only `char_count`, `slugify`, `top_words`, `word_count`), and `README.md` does not mention stopwords.

## Proposed outcome

- `top_words()` can be asked to exclude the stopwords of a chosen language from the ranking, and the returned list then contains only non-stopword entries, still ordered by count descending then alphabetically as today (`stats.py:35`).
- `textkit stats` exposes the same choice, and its `top:` section then omits the stopwords while keeping the existing `words:` / `chars:` / `top:` line layout from `_format_stats()`.
- The set of supported languages, where each list comes from, whether filtering is on by default or opt-in, and whether `word_count()` / the `words:` line also exclude stopwords are decided by the maintainer's answers to the appended open questions. The maintainer has explicitly said not to choose defaults for them.
- `README.md` describes the new behaviour and the supported languages.
- `make test` and `make lint` pass with the new behaviour covered by tests in `tests/test_stats.py` and `tests/test_cli.py`.

## Affected users and systems

- `src/textkit/stats.py` — `top_words()` gains language-aware filtering; `_tokens()` is what the filter sees; `word_count()` may change depending on open question 3.
- `src/textkit/cli.py` — the `stats` subparser in `build_parser()`, `_format_stats()`, and `main()` must carry the new choice through to `top_words()`.
- `src/textkit/__init__.py` — `__all__` must list any new public name (per the layout convention).
- Stopword data — a new file or module under `src/textkit/` (source and licence undecided); `pyproject.toml` `[tool.hatch.build.targets.wheel] packages = ["src/textkit"]` means anything outside that directory would not ship in the wheel.
- `tests/test_stats.py` — `test_top_words_orders_by_count_then_alphabetically` and `test_top_words_edge_cases` assert "the" is ranked and that `SAMPLE` has 5 distinct words; both are sensitive to the default-vs-opt-in answer.
- `tests/test_cli.py` — `test_stats_command_reports_counts` asserts `"  the: 3"` and `"words: 8"` in the output.
- `README.md` lines 3–8 — the feature description and CLI summary.
- Console script `textkit = "textkit.cli:main"` (`pyproject.toml:14`) — its output is documented as something users pipe into other tools (`README.md:8`), so line shape matters.
- `Makefile` `test` / `lint` targets via `uv run --frozen`, and the factory checks in `factory.toml` — must keep passing offline.

## Constraints

- No third-party runtime dependency. Source: the intent; `AGENTS.md` ("standard library only at runtime"); `pyproject.toml` `dependencies = []`; `README.md` "dependency-free".
- No bundled word list without a licence the maintainer has approved; none is approved. Source: the intent. An implementer-authored list is still a bundled list and falls under this rule.
- Python 3.12+ standard library only. Source: `pyproject.toml` `requires-python = ">=3.12"` and `AGENTS.md`.
- Public API compatibility: `top_words(text, n)` is called positionally in `cli.py:31` and in tests; any new parameter must not break `top_words(text, n)` or `word_count(text)` for existing callers. Source: `src/textkit/__init__.py` re-exports these as the public surface.
- CLI report shape: `words:`, `chars:`, `top:` then indented `  word: count` lines (`cli.py:30-31`). Existing lines should keep their meaning and format unless open question 3 changes `words:` deliberately. Source: `README.md:8` says output is piped into other tools.
- CLI error convention: invalid user input is reported through `parser.error(...)`, which exits with status 2 (`cli.py:44-45`, asserted in `tests/test_cli.py:28`). An unsupported language should follow the same path.
- Tests must run offline and deterministically: `factory.toml` `checks` run `make test`, and nothing in the repo mocks network access. A runtime download, if chosen, cannot be exercised by the test suite without stubbing.
- `uv.lock` must stay in sync with `pyproject.toml` (`AGENTS.md`); since dependencies cannot change, `uv.lock` should be untouched.
- Keep the change small and readable end to end; this is a fixture repo (`AGENTS.md`, `README.md:9-15`).

## Acceptance criteria

Criteria are written for "filtering enabled for language L" so they hold whichever way the default question is answered. Items marked (Q2) or (Q3) depend on the corresponding open question. English is assumed to be among the first-version languages because every example in the issue is English; if not, substitute an equivalent sample.

1. Given `"the cat sat on the mat the cat"` with English filtering enabled and `n=3`, `top_words()` returns `[("cat", 2), ("mat", 1), ("sat", 1)]` (assumes "the" and "on" are in the English list).
2. Given `"The THE the cat"` with English filtering enabled and `n=1`, the result is `[("cat", 1)]`: stopword matching is case-insensitive, consistent with the existing `token.lower()` in `stats.py:34`.
3. Stopwords are removed before the `n` truncation, not after: given the sample above with `n=99`, the result has 3 entries, not 5.
4. Given text made only of stopwords (for example `"the of and"`) with filtering enabled, `top_words()` returns `[]`, and `textkit stats` on a file containing that text prints `top:` with no indented lines and exits 0.
5. With filtering disabled, `top_words()` and `textkit stats` produce byte-for-byte the same results as today for every case in `tests/test_stats.py` and `tests/test_cli.py`. (Q2: if the maintainer chooses default-on, "disabled" means explicitly turned off, and the existing assertions on `"the"` are rewritten to that mode.)
6. `textkit stats FILE` with English filtering enabled on a file containing `"the cat sat on the mat the cat"` prints `chars: 30`, a `top:` section whose first entry is `  cat: 2`, and no `the` line.
7. (Q3) The `words:` line and `word_count()` for that same input either remain `8` (stopwords counted) or become `5` (stopwords excluded), matching the maintainer's answer, and the chosen behaviour has a test in both `tests/test_stats.py` and `tests/test_cli.py`.
8. `char_count()` and the `chars:` line are unchanged by filtering in every case.
9. Requesting a language that is not supported raises `ValueError` from `top_words()`, and the CLI reports it with exit status 2 and a message that names the language, following the `parser.error` convention in `cli.py:45`. (Assumes silently ignoring an unknown language is not acceptable; a no-op would hide misconfiguration.)
10. Calling `top_words(text, n)` and `word_count(text)` with the existing positional arguments only still works and returns today's values.
11. `pyproject.toml` `dependencies` is still `[]`, `uv.lock` is unchanged, and `make test` completes with no network access.
12. Any bundled word list is accompanied in the repository by its licence text or attribution, and the licence is the one the maintainer approved in answer to open question 1.
13. `README.md` names the option, the supported languages, and whether it is on by default.
14. `make test` and `make lint` both exit 0.

## Flagged concerns

- **Every list source is currently forbidden.** No third-party dependency, no bundled list without an approved licence, and a runtime download would contradict `README.md`'s "dependency-free" promise and make `make test` need the network. Implementation cannot start until the maintainer picks one; this is why the open questions block.
- **Tokenisation leaks punctuation.** `_TOKEN = re.compile(r"\S+")` (`stats.py:8`) keeps punctuation attached, so `"the,"`, `"The."` and `"(the"` are distinct tokens that will survive a filter for `"the"`. On real prose the top list will still contain stopword variants. Changing tokenisation also changes `word_count()` and is outside this intent; the reviewer should expect and accept the leak, or the maintainer should open a separate issue.
- **Existing tests assert "the" on top.** `tests/test_stats.py:24` and `tests/test_cli.py:22` break if filtering becomes the default. The opt-in answer keeps them untouched; the default-on answer rewrites them and changes CLI output for anyone piping `textkit stats` today.
- **Backward-compatible choices exist for questions 2 and 3.** Opt-in filtering and leaving `word_count()` alone are the zero-regression answers. They are not adopted here because the intent says not to choose on the maintainer's behalf, but confirming them is the lowest-risk reply.
- **`word_count()` coupling.** If stopwords are excluded from `words:`, `word_count()` needs the same language input and the `_format_stats()` signature grows; `char_count()` must not follow.
- **Short documents show fewer than 3 top lines.** With `TOP_WORDS_SHOWN = 3` and filtering on, small inputs may print zero to two entries; tests should cover the empty case rather than assume three lines.
- **Packaging of a data file.** If the list is a non-Python file it must sit under `src/textkit/` to be included by the hatch wheel target in `pyproject.toml:22-23`, and be read via `importlib.resources` rather than a relative filesystem path.
- **Lowercasing versus casefolding.** `stats.py:34` uses `str.lower()`; for non-English lists (German "ß", Turkish dotless i) `lower()` and `casefold()` differ, so the stopword list and the tokens must be normalised the same way.
- **Language identifier scheme.** The intent says "for a chosen language" but not how a language is named; the plan role should pick one scheme and reject anything else (criterion 9) rather than accept free text.

## Open questions

- Which languages must the first version of stopword filtering in textkit support, and where does each language's stopword list come from (a file bundled under src/textkit with a licence you approve, or a runtime download from a source you approve)? This blocks all implementation, because the repository forbids third-party dependencies and unapproved bundled lists, leaving no permitted source for any list.
- Should stopword filtering in top_words() and `textkit stats` be opt-in (existing results and output unchanged unless a language is requested) or on by default, and if you have a preferred parameter and flag name, what is it? This blocks the public API and CLI surface, and decides whether the existing tests asserting `the: 3` at the top of the sample are rewritten.
- When stopwords are filtered, should word_count() and the `words:` line of `textkit stats` also exclude them, or keep counting every whitespace token as today? This blocks the word_count() signature and the meaning of the CLI report.

# Role: review (read-only)

You are the review role of an automated software factory, working on issue 13. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

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

## Maintainer decisions

Answers to the three open questions, recorded by the maintainer on 2026-09-07:

1. **Languages and list source.** English only in the first version, identified by the language code `en`.
   The list is authored in this repository (a small `frozenset` of roughly 30 common English function words
   in a new module `src/textkit/stopwords.py`), not copied from any third-party source, and is covered by
   this repository's own licence. No data file, no runtime download, no new dependency. Approved.
2. **Opt-in.** Filtering is off by default so existing results and output are unchanged. `top_words()`
   gains a keyword-only parameter `stopwords: str | None = None` taking a language code (`"en"` is the only
   accepted value; anything else raises `ValueError`). The CLI exposes it as `textkit stats FILE --stopwords en`,
   and an unsupported code goes through `parser.error` (exit 2) naming the code. Existing tests that assert
   `the: 3` stay as they are and new tests cover the opt-in path.
3. **`word_count()` unchanged.** Stopwords are excluded from the ranking only. `word_count()` and the
   `words:` line keep counting every whitespace token as today, so for `"the cat sat on the mat the cat"`
   the answer to acceptance criterion 7 is `8`.

## Open questions

- None.


## The plan

# Plan: opt-in English stopword filtering for `top_words()` and `textkit stats` (issue 13)

Design fixed by the maintainer's decisions: English only, code `"en"`, list authored in-repo as a `frozenset` in `src/textkit/stopwords.py`, opt-in via keyword-only `stopwords: str | None = None` on `top_words()` and `--stopwords LANG` on `textkit stats`, unsupported code raises `ValueError` / exits 2 via `parser.error`, `word_count()` and `words:` unchanged.

## Files that change

- `src/textkit/stopwords.py` — NEW module. Holds the English stopword `frozenset`, the `STOPWORDS` registry keyed by language code, and `stopwords_for(language)` which returns the set or raises `ValueError` naming the code. Module docstring states the list was written for this repository, is not copied from any third-party source, and is covered by the repository's licence (criterion 12 attribution).
- `src/textkit/stats.py` — `top_words()` gains keyword-only `stopwords: str | None = None`; imports `stopwords_for`; validates the language before the `n <= 0` early return; drops lower-cased tokens that are in the set before counting (so before the `n` truncation). `word_count()`, `char_count()`, `_tokens()`, `_TOKEN` untouched.
- `src/textkit/cli.py` — `stats` subparser gains `--stopwords` (metavar `LANG`, default `None`); `_format_stats()` gains keyword-only `stopwords: str | None = None` and forwards it to `top_words()`; `main()` catches `ValueError` from `_format_stats()` and routes it to `parser.error(...)` (exit 2). `words:` / `chars:` / `top:` layout unchanged.
- `src/textkit/__init__.py` — re-export `stopwords_for` and add it to `__all__` (new public name per the layout convention).
- `tests/test_stats.py` — add `import pytest` and five new tests for the opt-in path (criteria 1, 2, 3, 4, 7, 8, 9); existing tests unchanged (criteria 5, 10).
- `tests/test_cli.py` — add three new tests for `--stopwords en`, the all-stopwords file, and an unsupported code (criteria 4, 6, 7, 8, 9); existing tests unchanged (criterion 5).
- `tests/test_stopwords.py` — NEW, one test file per source module (AGENTS.md layout). Two small tests on `stopwords_for`.
- `README.md` — document the option, the supported language (`en` only), that it is off by default, that counts are never filtered, and that the list lives in `src/textkit/stopwords.py` (criterion 13).

No change to `pyproject.toml`, `uv.lock`, `Makefile`, `factory.toml`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md` or anything under `.github/`.

## Exact changes

### `src/textkit/stopwords.py` (new)

```python
"""Stopword lists used by :func:`textkit.stats.top_words`.

The English list below was written for this repository — it is not copied from any
third-party source — and is covered by the repository's own licence.
"""

from __future__ import annotations

_EN = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
        "had", "has", "have", "he", "in", "is", "it", "its", "of", "on", "or",
        "that", "the", "this", "to", "was", "were", "will", "with",
    }
)

STOPWORDS: dict[str, frozenset[str]] = {"en": _EN}


def stopwords_for(language: str) -> frozenset[str]:
    """Return the lower-case stopword set for ``language`` (a code such as ``"en"``).

    Raises ``ValueError`` naming ``language`` when it is not supported.
    """
    try:
        return STOPWORDS[language]
    except KeyError:
        supported = ", ".join(sorted(STOPWORDS))
        msg = f"unsupported stopword language: {language!r} (supported: {supported})"
        raise ValueError(msg) from None
```

Requirements on the list: exactly 30 entries, all ASCII lower-case, must include `the`, `on`, `of`, `and` (criteria 1 and 4 rely on them) and must not include `cat`, `sat`, `mat`. Matching is exact-string on `language`; `"EN"` is rejected. Format the set literal however `ruff` is happy with under line length 100 (the layout above is illustrative; one word per line is fine).

### `src/textkit/stats.py`

Add `from .stopwords import stopwords_for` after the `Counter` import. Replace `top_words`:

```python
def top_words(
    text: str, n: int, *, stopwords: str | None = None
) -> list[tuple[str, int]]:
    """Return the ``n`` most frequent words in ``text``, most frequent first.

    Words are compared case-insensitively and ties are broken alphabetically,
    so the result is stable. A non-positive ``n`` returns an empty list. When
    ``stopwords`` is a language code (only ``"en"`` is supported), that language's
    stopwords are dropped before ranking; an unsupported code raises ``ValueError``.
    """
    excluded = stopwords_for(stopwords) if stopwords is not None else frozenset()
    if n <= 0:
        return []
    words = (token.lower() for token in _tokens(text))
    counts = Counter(word for word in words if word not in excluded)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]
```

Notes: validation happens before the `n <= 0` return so a bad code is never silently accepted. Tokens are lower-cased with `str.lower()` exactly as before, and the list is lower-case ASCII, so both sides use the same normalisation. With `stopwords=None` the code path is `Counter(word for word in words if word not in frozenset())`, which yields the same counts as today.

### `src/textkit/cli.py`

In `build_parser()` after the `file` positional:

```python
    stats_parser.add_argument(
        "--stopwords",
        metavar="LANG",
        help="exclude the stopwords of language LANG from the top list (supported: en)",
    )
```

`_format_stats`:

```python
def _format_stats(text: str, *, stopwords: str | None = None) -> str:
    """Render the plain-text statistics report for ``text``."""
    lines = [f"words: {word_count(text)}", f"chars: {char_count(text)}", "top:"]
    ranked = top_words(text, TOP_WORDS_SHOWN, stopwords=stopwords)
    lines += [f"  {word}: {count}" for word, count in ranked]
    return "\n".join(lines)
```

`main()`, replacing the last three lines of the stats branch:

```python
    if not args.file.is_file():
        parser.error(f"no such file: {args.file}")
    text = args.file.read_text(encoding="utf-8")
    try:
        report = _format_stats(text, stopwords=args.stopwords)
    except ValueError as exc:
        parser.error(str(exc))
    print(report)
    return 0
```

`read_text` must stay outside the `try`: `UnicodeDecodeError` is a subclass of `ValueError` and must not be reported as a usage error. `parser.error` exits with status 2 and prints the message (which contains the offending code, e.g. `'xx'`) to stderr.

### `src/textkit/__init__.py`

```python
from .slug import slugify
from .stats import char_count, top_words, word_count
from .stopwords import stopwords_for

__all__ = ["char_count", "slugify", "stopwords_for", "top_words", "word_count"]
```

### `tests/test_stats.py` (append; add `import pytest` at top)

```python
def test_top_words_can_exclude_english_stopwords():
    assert top_words(SAMPLE, 3, stopwords="en") == [("cat", 2), ("mat", 1), ("sat", 1)]


def test_top_words_removes_stopwords_before_truncating():
    assert len(top_words(SAMPLE, 99, stopwords="en")) == 3


def test_top_words_stopword_filter_is_case_insensitive():
    assert top_words("The THE the cat", 1, stopwords="en") == [("cat", 1)]


def test_top_words_of_only_stopwords_is_empty():
    assert top_words("the of and", 3, stopwords="en") == []


def test_top_words_rejects_unknown_stopword_language():
    with pytest.raises(ValueError, match="xx"):
        top_words(SAMPLE, 3, stopwords="xx")


def test_counts_are_not_affected_by_stopword_filtering():
    assert word_count(SAMPLE) == 8
    assert char_count(SAMPLE) == 30
    assert "the" not in dict(top_words(SAMPLE, 99, stopwords="en"))
```

Existing six tests stay byte-for-byte as they are.

### `tests/test_cli.py` (append)

```python
def test_stats_command_can_exclude_stopwords(tmp_path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat sat on the mat the cat", encoding="utf-8")

    assert main(["stats", str(sample), "--stopwords", "en"]) == 0

    out = capsys.readouterr().out
    assert out == "words: 8\nchars: 30\ntop:\n  cat: 2\n  mat: 1\n  sat: 1\n"


def test_stats_command_prints_empty_top_for_only_stopwords(tmp_path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("the of and", encoding="utf-8")

    assert main(["stats", str(sample), "--stopwords", "en"]) == 0
    assert capsys.readouterr().out == "words: 3\nchars: 10\ntop:\n"


def test_stats_command_rejects_unknown_stopword_language(tmp_path, capsys):
    sample = tmp_path / "sample.txt"
    sample.write_text("the cat", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main(["stats", str(sample), "--stopwords", "xx"])
    assert excinfo.value.code == 2
    assert "xx" in capsys.readouterr().err
```

Existing four tests stay byte-for-byte as they are.

### `tests/test_stopwords.py` (new)

```python
"""Tests for textkit.stopwords."""

import pytest

from textkit import stopwords_for


def test_english_list_is_lowercase_and_holds_common_function_words():
    words = stopwords_for("en")
    assert {"the", "on", "of", "and"} <= words
    assert all(word == word.lower() for word in words)


def test_unknown_language_raises_value_error_naming_it():
    with pytest.raises(ValueError, match="xx"):
        stopwords_for("xx")
```

### `README.md`

Insert a new paragraph after line 8 (the CLI sentence), before the "disposable fixture" paragraph:

> The most-frequent-words ranking can optionally drop common function words: `top_words(text, n, stopwords="en")` and `textkit stats <file> --stopwords en` exclude English stopwords ("the", "and", "of", …) from the `top:` list. Filtering is off by default, `en` (English) is the only supported language in this version, and any other code is rejected with an error (exit status 2 on the command line). The list is a short one written in this repository (`src/textkit/stopwords.py`); word and character counts are never filtered.

## Order of work

1. Create `tests/test_stopwords.py` as above. Run `uv run --frozen pytest tests/test_stopwords.py`; it fails at import (`ImportError: cannot import name 'stopwords_for'`).
2. Create `src/textkit/stopwords.py` and add the re-export to `src/textkit/__init__.py`. Re-run step 1's command; both tests pass.
3. Append the six new tests to `tests/test_stats.py` (plus `import pytest`). Run `uv run --frozen pytest tests/test_stats.py`; all six new tests (every one passes `stopwords=`) fail with `TypeError: top_words() got an unexpected keyword argument 'stopwords'`, the six existing tests still pass.
4. Change `top_words()` in `src/textkit/stats.py` as specified. Re-run step 3's command; all 12 tests pass.
5. Append the three new tests to `tests/test_cli.py`. Run `uv run --frozen pytest tests/test_cli.py`; `test_stats_command_can_exclude_stopwords` and `test_stats_command_prints_empty_top_for_only_stopwords` fail with `SystemExit` code 2 from argparse (`unrecognized arguments: --stopwords en`), the four existing tests still pass. `test_stats_command_rejects_unknown_stopword_language` already passes at this point because argparse rejects the unknown `--stopwords` option with exit 2 and echoes `xx` in the message; step 6 is what makes it pass for the intended reason (`unsupported stopword language: 'xx'`).
6. Change `build_parser()`, `_format_stats()` and `main()` in `src/textkit/cli.py` as specified. Re-run step 5's command; all 7 tests pass.
7. Update `README.md`.
8. Run `make test` and `make lint`; both must exit 0. Fix any `ruff` line-length or import-order complaints (E501, I001 are the likely ones) without changing behaviour.
9. Confirm `pyproject.toml` and `uv.lock` are untouched (`git status --porcelain -- pyproject.toml uv.lock` prints nothing). The build role cannot run `git`, so it confirms this by never opening either file; the factory's own diff is the check.

## Proof

Run from the repository root.

| Command | Passing output proves |
|---|---|
| `uv run --frozen pytest tests/test_stopwords.py` | `stopwords_for("en")` returns a lower-case set containing `the`, `on`, `of`, `and`; unknown code raises `ValueError` naming it (criterion 9, part of 12). Fails before step 2 with `ImportError`. |
| `uv run --frozen pytest tests/test_stats.py` | Criteria 1 (`test_top_words_can_exclude_english_stopwords`), 2 (`test_top_words_stopword_filter_is_case_insensitive`), 3 (`test_top_words_removes_stopwords_before_truncating`), 4 (`test_top_words_of_only_stopwords_is_empty`), 7 and 8 (`test_counts_are_not_affected_by_stopword_filtering`), 9 (`test_top_words_rejects_unknown_stopword_language`); 5 and 10 via the untouched `test_top_words_orders_by_count_then_alphabetically`, `test_top_words_edge_cases`, `test_word_count_counts_whitespace_separated_tokens`. All six new tests fail before step 4 with `TypeError`. |
| `uv run --frozen pytest tests/test_cli.py` | Criteria 6, 7, 8 (`test_stats_command_can_exclude_stopwords`, exact report string with `words: 8`, `chars: 30`, `  cat: 2` first, no `the` line), 4 (`test_stats_command_prints_empty_top_for_only_stopwords`, bare `top:` and exit 0), 9 (`test_stats_command_rejects_unknown_stopword_language`, exit 2, message contains `xx`); 5 via the untouched `test_stats_command_reports_counts` still seeing `  the: 3`. The first two new tests fail before step 6 with `SystemExit(2)` from `unrecognized arguments`; the third already passes then (argparse's unknown-option error is also exit 2 and names `xx`). |
| `make test` | Whole suite (4 test files including the untouched `tests/test_slug.py`; 19 baseline tests + 11 new = 30) exits 0 (criterion 14). |
| `make lint` | `ruff check .` exits 0 (criterion 14). |
| `uv run --frozen --offline pytest` | Suite passes with the network disabled for `uv`; no download happens at test time (criterion 11). |
| `git status --porcelain -- pyproject.toml uv.lock` | Empty output: `dependencies = []` and `uv.lock` untouched (criterion 11). Run by the factory / reviewer, not the build role, which has no `git` access. |
| `printf 'the cat sat on the mat the cat' > /tmp/tk.txt && uv run --frozen textkit stats /tmp/tk.txt --stopwords en` | Prints exactly `words: 8`, `chars: 30`, `top:`, `  cat: 2`, `  mat: 1`, `  sat: 1` (criteria 6, 7, 8 via the console script). |
| `uv run --frozen textkit stats /tmp/tk.txt` | Prints today's output ending `  the: 3`, `  cat: 2`, `  mat: 1` (criterion 5: opt-in, off by default). |
| `uv run --frozen textkit stats /tmp/tk.txt --stopwords xx; echo "exit=$?"` | stderr has `usage:` line plus `unsupported stopword language: 'xx' (supported: en)`, and `exit=2` (criterion 9). |
| `grep -n "stopwords" README.md` | Shows the paragraph naming `--stopwords en`, `en` as the only language, and "off by default" (criterion 13). |
| `head -6 src/textkit/stopwords.py` | Docstring carries the in-repo authorship / licence statement (criterion 12). |

## Risks

- **No `LICENSE` file exists in the repository.** The maintainer approved the list as "covered by this repository's own licence", but there is no licence text to point at, so criterion 12 can only be met by the attribution sentence in the `stopwords.py` module docstring. Adding a `LICENSE` file is out of this issue's scope; the reviewer should either accept the docstring attribution or ask the maintainer to add a licence in a separate change.
- **Punctuation leak (spec-flagged, not resolved here).** `_TOKEN = re.compile(r"\S+")` keeps `"the,"` and `"(the"` as distinct tokens that survive the filter. Changing tokenisation would alter `word_count()` and is outside this intent. The tests use punctuation-free samples deliberately.
- **`UnicodeDecodeError` is a `ValueError`.** If `read_text` were inside the `try` in `main()`, a non-UTF-8 file would be reported as a usage error. The plan keeps `read_text` outside the `try`; the reviewer should check that ordering.
- **Validation order in `top_words()`.** `stopwords_for()` must run before the `n <= 0` early return, otherwise `top_words(text, 0, stopwords="xx")` would silently succeed. `test_top_words_rejects_unknown_stopword_language` uses `n=3`, so add nothing further, but do not reorder the lines.
- **Existing tests must not be touched.** Criterion 5 and the maintainer's decision 2 depend on `tests/test_stats.py:24` and `tests/test_cli.py:22` staying exactly as they are. Only append.
- **Language code is case-sensitive.** `"EN"` raises `ValueError`, matching the decision that `"en"` is the only accepted value. Documented in the README paragraph; do not add `.lower()` on the code.
- **`ruff` line length 100.** The `frozenset` literal and the `ValueError` message are the lines most likely to exceed it; wrap the literal and keep the message in a `msg` variable as shown.
- **`tests/test_stopwords.py` is not named in the spec's test list.** It is added because AGENTS.md requires one `test_<module>.py` per source module; it is listed under "Files that change" so the gate accepts it. If the reviewer prefers fewer files, its two assertions are already covered by `tests/test_stats.py` and it can be dropped without losing criterion coverage.
- **`parser.error` is `NoReturn`.** `report` is only used after the `try`, which is fine for `ruff`'s default rule set; if a stricter checker complains about a possibly-unbound `report`, initialise it or return inside the `try`, but do not move `read_text` inside.


## The diff under review

The diff under review is not reproduced here. It is the file `.factory/tmp/review-1.diff`, relative to the root of this worktree: 9362 bytes, 272 lines.

Read it completely before you judge anything: start at the beginning and keep reading with offset/limit until you have seen line 272. A single read may return only the first part of the file. Do not review from a partial read.

## Check output from the last stage

$ make test
uv run --frozen pytest
..............................                                           [100%]
30 passed in 0.04s
Using CPython 3.14.7
Creating virtual environment at: .venv
Installed 7 packages in 4ms
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

This is review round 1 of issue 13, over the commit 406224d78862 (0 fix round(s) so far).

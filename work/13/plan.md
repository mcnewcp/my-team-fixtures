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
3. Append the six new tests to `tests/test_stats.py` (plus `import pytest`). Run `uv run --frozen pytest tests/test_stats.py`; the five `stopwords=` tests fail with `TypeError: top_words() got an unexpected keyword argument 'stopwords'`, the six existing tests still pass.
4. Change `top_words()` in `src/textkit/stats.py` as specified. Re-run step 3's command; all 12 tests pass.
5. Append the three new tests to `tests/test_cli.py`. Run `uv run --frozen pytest tests/test_cli.py`; the three new tests fail with `SystemExit` code 2 from argparse (`unrecognized arguments: --stopwords en`), the four existing tests still pass.
6. Change `build_parser()`, `_format_stats()` and `main()` in `src/textkit/cli.py` as specified. Re-run step 5's command; all 7 tests pass.
7. Update `README.md`.
8. Run `make test` and `make lint`; both must exit 0. Fix any `ruff` line-length or import-order complaints (E501, I001 are the likely ones) without changing behaviour.
9. Run `git status --porcelain -- pyproject.toml uv.lock` and confirm it prints nothing.

## Proof

Run from the repository root.

| Command | Passing output proves |
|---|---|
| `uv run --frozen pytest tests/test_stopwords.py` | `stopwords_for("en")` returns a lower-case set containing `the`, `on`, `of`, `and`; unknown code raises `ValueError` naming it (criterion 9, part of 12). Fails before step 2 with `ImportError`. |
| `uv run --frozen pytest tests/test_stats.py` | Criteria 1 (`test_top_words_can_exclude_english_stopwords`), 2 (`test_top_words_stopword_filter_is_case_insensitive`), 3 (`test_top_words_removes_stopwords_before_truncating`), 4 (`test_top_words_of_only_stopwords_is_empty`), 7 and 8 (`test_counts_are_not_affected_by_stopword_filtering`), 9 (`test_top_words_rejects_unknown_stopword_language`); 5 and 10 via the untouched `test_top_words_orders_by_count_then_alphabetically`, `test_top_words_edge_cases`, `test_word_count_counts_whitespace_separated_tokens`. The five new `stopwords=` tests fail before step 4 with `TypeError`. |
| `uv run --frozen pytest tests/test_cli.py` | Criteria 6, 7, 8 (`test_stats_command_can_exclude_stopwords`, exact report string with `words: 8`, `chars: 30`, `  cat: 2` first, no `the` line), 4 (`test_stats_command_prints_empty_top_for_only_stopwords`, bare `top:` and exit 0), 9 (`test_stats_command_rejects_unknown_stopword_language`, exit 2, message contains `xx`); 5 via the untouched `test_stats_command_reports_counts` still seeing `  the: 3`. The three new tests fail before step 6 with `SystemExit(2)` from `unrecognized arguments`. |
| `make test` | Whole suite (3 test files, 22 tests) exits 0 (criterion 14). |
| `make lint` | `ruff check .` exits 0 (criterion 14). |
| `uv run --frozen --offline pytest` | Suite passes with the network disabled for `uv`; no download happens at test time (criterion 11). |
| `git status --porcelain -- pyproject.toml uv.lock` | Empty output: `dependencies = []` and `uv.lock` untouched (criterion 11). |
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

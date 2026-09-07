# Plan: `slugify` gains `separator` and `max_length`; `textkit slug` gains `--separator` and `--max-length` (issue 8)

Default behavior is frozen: `slugify(text)` returns exactly what it returns today. Two keyword arguments are added to the one function, two small helpers land beside it in `src/textkit/slug.py`, and the CLI forwards two options. Four files change; nothing else.

## Files that change

- `src/textkit/slug.py` — `slugify(text)` becomes `slugify(text, separator="-", max_length=None)`; add helper `_validate_options(separator, max_length)` (raises `ValueError`) and helper `_cut_to_whole_words(slug, separator, max_length)` (word-boundary truncation); rewrite the `slugify` docstring so it describes both parameters, the whole-word cut, the single-long-word hard cut, the empty-separator hard cut and both `ValueError` conditions, and no longer calls the output "hyphen-separated". `_SEPARATOR_RUN` and `_to_ascii` are unchanged.
- `src/textkit/cli.py` — add `--separator` (default `"-"`) and `--max-length` (type `_positive_int`, default `None`, metavar `N`) to the `slug` subparser; add helper `_positive_int(value)` that raises `argparse.ArgumentTypeError`; forward both options in the `slug` dispatch and route a `ValueError` from `slugify` through `parser.error`; update the module docstring usage form to `textkit slug [options] <text>`.
- `tests/test_slug.py` — append new test functions for acceptance criteria 3–16 below the existing three tests. Lines 1–31 stay byte-for-byte identical.
- `tests/test_cli.py` — append new test functions for acceptance criteria 18–21 below the existing four tests. Lines 1–35 stay byte-for-byte identical.

Not touched: `src/textkit/__init__.py` (re-export is already by name), `README.md` (prose only, no options listed), `pyproject.toml`, `uv.lock` (no dependency change), `Makefile`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, `factory.toml`.

## Design (no decisions left to the build)

### `src/textkit/slug.py`

Replace lines 17–24 with the following three functions. Keep `from __future__ import annotations`, `re`, `unicodedata`, `_SEPARATOR_RUN`, `_to_ascii` as they are.

```python
def _validate_options(separator: str, max_length: int | None) -> None:
    """Raise ``ValueError`` if ``separator`` holds an ASCII letter or digit or ``max_length`` < 1."""
    if any(char.isascii() and char.isalnum() for char in separator):
        raise ValueError(f"separator must not contain letters or digits: {separator!r}")
    if max_length is not None and max_length < 1:
        raise ValueError(f"max_length must be at least 1, got {max_length}")


def _cut_to_whole_words(slug: str, separator: str, max_length: int) -> str:
    """Return ``slug`` cut to at most ``max_length`` characters, ending on a whole word.

    Backs up to the last ``separator`` that starts at or before ``max_length`` so the
    result never ends mid-word or with a trailing separator. Falls back to a plain
    character cut when the first word alone is longer than ``max_length`` or when
    ``separator`` is empty and there are no word boundaries to back up to.
    """
    if len(slug) <= max_length:
        return slug
    if separator:
        cut = slug.rfind(separator, 0, max_length + len(separator))
        if cut > 0:
            return slug[:cut]
    return slug[:max_length]


def slugify(text: str, separator: str = "-", max_length: int | None = None) -> str:
    """Return a lowercase ASCII slug for ``text`` with words joined by ``separator``.

    Accents are folded ("Crème" -> "creme"), every run of non-alphanumeric characters
    collapses to a single ``separator`` (default ``"-"``; ``""`` yields a compact slug with
    no separator at all), and a leading or trailing separator is removed. Text with no
    alphanumerics yields an empty string.

    When ``max_length`` is set, the slug is cut back to the last whole word that fits, so
    it is never longer than ``max_length`` characters and never ends with the separator.
    If the first word alone is longer than ``max_length``, or ``separator`` is empty so
    there are no word boundaries, the slug is hard-cut to ``max_length`` characters
    instead, so non-empty input still gives a non-empty slug.

    Raises ``ValueError`` if ``separator`` contains an ASCII letter or digit (such a
    separator cannot be told apart from word content, so re-slugifying would change the
    result) or if ``max_length`` is less than 1.
    """
    _validate_options(separator, max_length)
    slug = _SEPARATOR_RUN.sub(separator, _to_ascii(text).lower())
    slug = slug.removeprefix(separator).removesuffix(separator)
    if max_length is None:
        return slug
    return _cut_to_whole_words(slug, separator, max_length)
```

Why these exact choices:

- `removeprefix`/`removesuffix` instead of `strip(separator)`: after `_SEPARATOR_RUN.sub`, the string has at most one separator at each end (runs collapse), so both give identical results for the default `"-"` (default output frozen), but `removeprefix` is exact for multi-character separators and is a no-op for `""`, so no `if separator:` branch is needed.
- `rfind(separator, 0, max_length + len(separator))` finds the last separator whose *start* index is `<= max_length`, i.e. the last one where `slug[:cut]` has length `<= max_length`. Worked check on `"the-quick-brown-fox"`: `max_length=10` searches `"the-quick-b"`, finds `-` at 9, returns `"the-quick"`; `9` searches `"the-quick-"`, finds 9, returns `"the-quick"`; `8` searches `"the-quick"`, finds 3, returns `"the"`; `2` searches `"the"`, finds nothing, hard-cuts to `"th"`. Multi-char check: `"rev__2__0__final"`, `separator="__"`, `max_length=6` searches `"rev__2__"`, finds `__` at 6, returns `"rev__2"`.
- `cut > 0` (not `!= -1`) guarantees a non-empty result; after stripping, index 0 is never a separator anyway.
- Validation uses `char.isascii() and char.isalnum()` so uppercase letters are rejected too (an uppercase separator would be lowercased on re-slugify and break idempotence), while non-ASCII punctuation such as `"·"` is allowed, matching the spec's "ASCII letter or digit" rule.

### `src/textkit/cli.py`

Line 1 becomes:

```python
"""Command-line interface: ``textkit slug [options] <text>`` and ``textkit stats <file>``."""
```

Add after `TOP_WORDS_SHOWN = 3` (before `build_parser`):

```python
def _positive_int(value: str) -> int:
    """Return ``value`` parsed as an int of at least 1, or raise ``argparse.ArgumentTypeError``."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError(f"expected a value of at least 1, got {value!r}")
    return number
```

Raising `ArgumentTypeError` for both failures (rather than letting `int()`'s `ValueError` propagate) keeps argparse's message readable; otherwise it prints `invalid _positive_int value`. Either way argparse calls `parser.error`, prints usage to stderr and exits 2, which is what criterion 20 needs.

In `build_parser`, after `slug_parser.add_argument("text", help="text to slugify")` add:

```python
    slug_parser.add_argument(
        "--separator",
        default="-",
        help="text placed between words (default: %(default)r)",
    )
    slug_parser.add_argument(
        "--max-length",
        type=_positive_int,
        default=None,
        metavar="N",
        help="max slug length in characters (default: no limit)",
    )
```

Keep both help strings under ~50 characters so argparse does not wrap them and the `--help` test can match `default: '-'` and `no limit` as contiguous substrings. `%(default)r` renders `'-'`. Do **not** use `default=None` plus `args.separator or "-"` anywhere: `--separator ""` must reach `slugify` as `""`.

In `main`, replace the `slug` branch (current lines 40–42) with:

```python
    if args.command == "slug":
        try:
            print(slugify(args.text, separator=args.separator, max_length=args.max_length))
        except ValueError as exc:
            parser.error(str(exc))
        return 0
```

The `try` routes an alphanumeric `--separator` (the only `ValueError` argparse cannot catch itself, since `--max-length` is validated by `_positive_int`) through `parser.error`, satisfying the constraint that CLI argument errors exit 2 via argparse instead of a traceback. The `stats` branch is untouched.

### `tests/test_slug.py` — new tests appended after line 31

```python
@pytest.mark.parametrize(
    ("text", "separator", "expected"),
    [
        ("Hello World", "_", "hello_world"),
        ("snake_case_name", "_", "snake_case_name"),
        ("  Trim   me  ", "_", "trim_me"),
        ("Hello, World! 2026", "", "helloworld2026"),
        ("Rev 2.0 / final", "__", "rev__2__0__final"),
    ],
)
def test_slugify_custom_separator(text, separator, expected):
    assert slugify(text, separator=separator) == expected


@pytest.mark.parametrize("separator", ["_", ""])
def test_slugify_custom_separator_is_idempotent(separator):
    once = slugify("Hello, World! 2026", separator=separator)
    assert slugify(once, separator=separator) == once


def test_slugify_max_length_defaults_to_no_cap():
    assert slugify("the quick brown fox") == "the-quick-brown-fox"
    assert len(slugify("the quick brown fox")) == 19
    assert slugify("the quick brown fox", max_length=100) == "the-quick-brown-fox"


@pytest.mark.parametrize(
    ("max_length", "expected"),
    [(10, "the-quick"), (9, "the-quick"), (8, "the")],
)
def test_slugify_max_length_cuts_back_to_whole_words(max_length, expected):
    assert slugify("the quick brown fox", max_length=max_length) == expected


def test_slugify_max_length_hard_cuts_a_single_long_word():
    assert slugify("the quick brown fox", max_length=2) == "th"


@pytest.mark.parametrize(
    ("separator", "max_length", "expected"),
    [("_", 10, "the_quick"), ("", 5, "thequ")],
)
def test_slugify_max_length_with_custom_separator(separator, max_length, expected):
    assert slugify("the quick brown fox", separator=separator, max_length=max_length) == expected


def test_slugify_truncated_output_is_stable():
    once = slugify("the quick brown fox", max_length=10)
    assert slugify(once, max_length=10) == once


def test_slugify_max_length_on_empty_and_symbol_only():
    assert slugify("", separator="_", max_length=5) == ""
    assert slugify("!!! ???", max_length=3) == ""


@pytest.mark.parametrize("separator", ["x", "1"])
def test_slugify_rejects_alphanumeric_separator(separator):
    with pytest.raises(ValueError):
        slugify("a b", separator=separator)


@pytest.mark.parametrize("max_length", [0, -1])
def test_slugify_rejects_non_positive_max_length(max_length):
    with pytest.raises(ValueError):
        slugify("a b", max_length=max_length)
```

Criterion map: 3 & 4 & 5 & 6 → `test_slugify_custom_separator`; 7 → `test_slugify_custom_separator_is_idempotent`; 8 & 9 → `test_slugify_max_length_defaults_to_no_cap`; 10 → `test_slugify_max_length_cuts_back_to_whole_words`; 11 → `test_slugify_max_length_hard_cuts_a_single_long_word`; 12 → `test_slugify_max_length_with_custom_separator`; 13 → `test_slugify_truncated_output_is_stable`; 14 → `test_slugify_max_length_on_empty_and_symbol_only`; 15 → `test_slugify_rejects_alphanumeric_separator`; 16 → `test_slugify_rejects_non_positive_max_length`. Criterion 2 is already covered by the untouched `test_slugify_examples` and `test_slugify_empty_and_symbol_only`.

### `tests/test_cli.py` — new tests appended after line 35

```python
def test_slug_command_accepts_separator(capsys):
    assert main(["slug", "--separator", "_", "Hello, World!"]) == 0
    assert capsys.readouterr().out == "hello_world\n"


def test_slug_command_accepts_max_length(capsys):
    assert main(["slug", "--max-length", "5", "Hello, World! 2026"]) == 0
    assert capsys.readouterr().out == "hello\n"


@pytest.mark.parametrize("value", ["abc", "0"])
def test_slug_command_rejects_a_bad_max_length(value, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["slug", "--max-length", value, "Hello"])
    assert excinfo.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_slug_command_rejects_an_alphanumeric_separator(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["slug", "--separator", "x", "Hello"])
    assert excinfo.value.code == 2
    assert "usage:" in capsys.readouterr().err


def test_slug_help_lists_both_options(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["slug", "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "--separator" in out
    assert "default: '-'" in out
    assert "--max-length" in out
    assert "no limit" in out
```

Criterion map: 17 → existing `test_slug_command_prints_slug` (untouched); 18 → `test_slug_command_accepts_separator`; 19 → `test_slug_command_accepts_max_length`; 20 → `test_slug_command_rejects_a_bad_max_length`; 21 → `test_slug_help_lists_both_options`; the constraint "CLI argument errors go through argparse" → `test_slug_command_rejects_an_alphanumeric_separator`.

## Order of work

1. Append the ten new test functions above to `tests/test_slug.py`. Do not edit lines 1–31. Run `make test`: the existing tests stay green; every new slug test fails with `TypeError: slugify() got an unexpected keyword argument` (this is the failing-first proof for criteria 3–16).
2. Edit `src/textkit/slug.py`: add `_validate_options` and `_cut_to_whole_words`, replace `slugify` with the new signature, body and docstring exactly as written above. Run `make test`: all slug tests pass, including the three untouched ones (proves criterion 2 and the frozen default).
3. Append the five new test functions above to `tests/test_cli.py`. Do not edit lines 1–35. Run `make test`: `test_slug_command_accepts_separator`, `test_slug_command_accepts_max_length` and `test_slug_help_lists_both_options` fail (argparse rejects the unknown options with exit 2, or `--help` output lacks them). Note: `test_slug_command_rejects_a_bad_max_length` and `test_slug_command_rejects_an_alphanumeric_separator` already pass at this point, because argparse rejects unknown options with exit 2 too; the positive tests are the ones that prove the CLI change.
4. Edit `src/textkit/cli.py`: update the module docstring, add `_positive_int`, add the two `add_argument` calls, replace the `slug` branch in `main`. Run `make test`: everything passes.
5. Run `make lint`; fix anything reported (none expected).
6. Run the manual proof commands below (`--help` output and the `python -c` one-liners) and the `git diff` checks confirming the existing tests were only appended to.

## Proof

Repository checks (both must exit 0):

```bash
make test
make lint
```

`make test` passing proves criteria 1 (existing tests green), 2–21 and 24 via the named tests; `make lint` passing proves criterion 23's lint half. Together they are criterion 23.

Existing tests unchanged (criterion 1, and the spec's "byte-for-byte untouched" constraint). Each command must print nothing; a diff with only `+` lines has no removed or altered lines:

```bash
git diff main -- tests/test_slug.py | grep '^-[^-]'
git diff main -- tests/test_cli.py | grep '^-[^-]'
```

Failing-before / passing-after tests:

- Before step 2, `uv run --frozen pytest tests/test_slug.py -k "separator or max_length"` fails every new test with `TypeError`; after step 2 it passes.
- Before step 4, `uv run --frozen pytest tests/test_cli.py -k "accepts or help"` fails `test_slug_command_accepts_separator`, `test_slug_command_accepts_max_length`, `test_slug_help_lists_both_options`; after step 4 it passes.

Criterion 21 (help lists both options with defaults), also checked by `test_slug_help_lists_both_options`:

```bash
uv run --frozen textkit slug --help
```

Output must contain a `--separator SEPARATOR` line ending `(default: '-')` and a `--max-length N` line ending `(default: no limit)`.

Criterion 22 (docstring content) is a read check: open `src/textkit/slug.py` and confirm the `slugify` docstring mentions `separator`, `max_length`, the whole-word cut, the single-long-word hard cut, both `ValueError` cases, and that the word "hyphen" no longer appears in it. `grep -n hyphen src/textkit/slug.py` must print nothing.

Spot checks of the library from the shell (each prints the expected value; these mirror criteria 3, 5, 10, 11, 12, 15, 16):

```bash
uv run --frozen python -c "from textkit import slugify; print(slugify('Hello World', separator='_'))"          # hello_world
uv run --frozen python -c "from textkit import slugify; print(slugify('Hello, World! 2026', separator=''))"   # helloworld2026
uv run --frozen python -c "from textkit import slugify; print([slugify('the quick brown fox', max_length=n) for n in (10, 9, 8, 2)])"  # ['the-quick', 'the-quick', 'the', 'th']
uv run --frozen python -c "from textkit import slugify; print(slugify('the quick brown fox', separator='', max_length=5))"  # thequ
uv run --frozen python -c "from textkit import slugify; slugify('a b', separator='x')"      # ValueError
uv run --frozen python -c "from textkit import slugify; slugify('a b', max_length=0)"       # ValueError
```

CLI spot checks (criteria 17–20):

```bash
uv run --frozen textkit slug "Hello, World!"                          # hello-world
uv run --frozen textkit slug --separator _ "Hello, World!"            # hello_world
uv run --frozen textkit slug --max-length 5 "Hello, World! 2026"      # hello
uv run --frozen textkit slug --max-length abc Hello; echo $?          # usage message on stderr, then 2
uv run --frozen textkit slug --max-length 0 Hello; echo $?            # usage message on stderr, then 2
```

## Risks

- **Spec criterion 1 vs 24 conflict.** Criterion 1 says `tests/test_slug.py` and `tests/test_cli.py` are "unchanged from `main`", while criterion 24 says new tests exist in those same files and the "Affected systems" section says "new tests are added alongside". This plan reads criterion 1 as "the existing tests are unchanged" and appends new tests below them. The `git diff ... | grep '^-[^-]'` proof shows no existing line was altered or removed. If the reviewer reads criterion 1 literally, the new tests cannot go anywhere else without violating the one-test-file-per-module layout rule, so the reviewer must pick one; this plan picks append.
- **Off-by-one in the word cut.** The `rfind` upper bound must be `max_length + len(separator)`, not `max_length`; with `max_length` alone, `max_length=9` on `"the-quick-brown-fox"` would miss the separator at index 9 and return `"the"` instead of `"the-quick"`. The parametrized case `(9, "the-quick")` in `test_slugify_max_length_cuts_back_to_whole_words` catches this, as does `(10, "the-quick")` for the opposite mistake of allowing a trailing separator.
- **Do not `rstrip` after slicing.** The spec's flagged concern: slicing then stripping leaks partial words (`"the-quick-br"`). The helper never slices at `max_length` unless no separator was found, so this cannot happen; the `(8, "the")` case would fail if someone "simplified" the helper to slice-then-strip.
- **Frozen default output.** Switching `strip("-")` to `removeprefix`/`removesuffix` is behavior-identical because collapsed runs leave at most one separator per end. The seven untouched parametrized examples plus `test_slugify_empty_and_symbol_only` (which hits the all-separator `"-"` → `""` path) verify this. If a reviewer prefers the smaller diff, `.strip(separator)` is also correct (set semantics coincide here, and `strip("")` is a no-op); either satisfies the tests.
- **argparse and `--separator ""`.** The `default="-"` on the argument is the only place the default lives; there must be no `or "-"` fallback in `main`, or the compact-slug case silently reverts to hyphens. Not directly covered by a required criterion; the build can spot-check with `uv run --frozen textkit slug --separator "" "Hello, World!"` → `helloworld`.
- **`--help` test brittleness.** `test_slug_help_lists_both_options` matches `default: '-'` and `no limit` as substrings; argparse wraps long help text at roughly 54 columns of help width, which could split those phrases. The help strings specified above are 41 and 49 characters, so they do not wrap. If the build changes the wording, keep each help string under about 50 characters.
- **Ruff does not enforce line length by default.** The spec says `make lint` enforces line length 100, but ruff's default rule set (E4, E7, E9, F) does not include E501, so `ruff check .` will not flag a 101-character line. The build must keep lines under 100 by inspection; the longest specified lines (the `slugify` signature call in `main`, the docstring lines) are under 100 as written.
- **Single-long-word hard cut and empty-separator hard cut** (spec flagged concerns) are implemented as specified and documented in the docstring, so `"th"` and `"thequ"` are by design. Not resolved further; the reviewer confirms the trade-off.
- **CLI `ValueError` routing is a small inferred addition.** Wrapping the `slugify` call in `try/except ValueError → parser.error` is not an enumerated criterion but follows the constraint "CLI argument errors go through argparse ... rather than with a traceback". Dropping it removes only `test_slug_command_rejects_an_alphanumeric_separator`; no enumerated criterion depends on it.
- **CLI scope.** The spec notes the CLI flags are an inferred reading of "affected systems". If the reviewer strikes them, drop the `src/textkit/cli.py` and `tests/test_cli.py` changes; nothing in `slug.py` or `tests/test_slug.py` depends on them.
- **Protected files.** No step edits `Makefile`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md`, `factory.toml`, `README.md`, `pyproject.toml` or `uv.lock`. `uv run --frozen` will fail if `uv.lock` drifts; no dependency changes, so it will not.

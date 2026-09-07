# Role: plan (read-only)

You are the plan role of an automated software factory, working on issue 8. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

Do not create, edit or delete any file. Do not run shell commands. Read and search the repository as much as you need; the factory writes every file.

## The spec

## Problem

`slugify` in `src/textkit/slug.py:17-24` is a single expression: it folds `text` to ASCII via `_to_ascii` (`slug.py:11`), lowercases it, replaces every run matched by `_SEPARATOR_RUN` (`slug.py:8`, `[^a-z0-9]+`) with a literal `"-"`, and strips leading and trailing `"-"`. The hyphen is hard-coded twice (the `sub` replacement and the `strip` argument) and there is no way to bound the result's length. The function takes exactly one parameter, `text`.

Consequences callers see today:

- A caller who wants `hello_world` or `helloworld` has to post-process the returned string with `str.replace("-", ...)`, which also rewrites hyphens that came from the input. `tests/test_slug.py:13` shows the case: `"Already-slugged"` slugifies to `"already-slugged"`, and a caller cannot tell that hyphen apart from a word-joining one.
- A caller who needs a slug of at most N characters slices the result, which can leave a trailing hyphen (`"the-quick-"[:10]`) or a partial word (`"the-quick-brown"[:12]` → `"the-quick-br"`).

The CLI subcommand `textkit slug` (`src/textkit/cli.py:19-20`, dispatched at `cli.py:40-41`) exposes only the single-argument form, so command-line users have the same limitation. The public export in `src/textkit/__init__.py:3` re-exports `slugify` unchanged.

## Proposed outcome

`slugify` accepts two optional settings in addition to `text`, and every existing call site keeps working unchanged:

- **`separator`**, a string, default `"-"`. It replaces every run of non-alphanumeric characters and is removed from both ends of the result. The empty string is allowed and yields a compact slug with no separator.
- **`max_length`**, an `int` or `None`, default `None`. `None` means no cap (today's behavior). When set, the returned slug is never longer than `max_length` characters, never ends with the separator, and is cut back to the last whole word that fits. If the first word alone is longer than `max_length`, the slug is that word hard-cut to `max_length` characters so a caller still gets a non-empty result for non-empty input.

Assumptions taken in place of the intent's open questions, so implementation is not blocked:

- **API shape: keyword arguments on `slugify`**, not an options object or second function. Two knobs on a one-line function do not justify a new type, and `AGENTS.md` asks for the repo to stay small and readable end to end. `tests/test_slug.py` and `tests/test_cli.py` continue to call the one-argument form and must pass untouched.
- **Cap semantics: whole-word cut, default `None`.** The intent's stated pain is trailing separators and half words, so the library removes exactly that. A concrete default number would silently change output for existing callers, which the intent forbids.
- **Validation is minimal.** A `separator` containing an ASCII letter or digit raises `ValueError`, because such a separator is indistinguishable from word content and breaks re-slugifying a slug (the idempotence property `tests/test_slug.py:29-31` guarantees). A `max_length` below 1 raises `ValueError`, because 0 or a negative cap cannot produce a meaningful slug. Assumes callers pass correct types; no type checking beyond that.
- **The CLI mirrors the library.** `textkit slug` gains `--separator` and `--max-length` options that forward to the two keyword arguments. The intent lists `textkit slug` under affected systems, and `README.md:6-7` states the CLI exposes "the same functions"; leaving the CLI on the old form would make it the one caller that cannot use the new behavior. If the reviewer judges this out of scope, dropping it does not affect any library criterion below.

Truncation is applied to the fully built slug: fold, lowercase, join with the separator, strip, then cap. When `separator` is `""` there are no word boundaries, so the cap is a plain character cut.

## Affected users and systems

- Library callers of `textkit.slugify` — `src/textkit/__init__.py:3` re-export; signature gains two optional keyword arguments, no rename.
- `slugify` implementation and docstring — `src/textkit/slug.py:17-24`; docstring currently says "hyphen-separated" and must describe both parameters.
- Module regex `_SEPARATOR_RUN` — `src/textkit/slug.py:8`; it matches non-alphanumeric runs independent of the output separator, so it may stay as is.
- CLI subcommand `slug` — `src/textkit/cli.py:19-20` (parser) and `cli.py:40-41` (dispatch); gains `--separator` and `--max-length`.
- CLI module docstring — `src/textkit/cli.py:1` names the `slug` usage form.
- Existing slug tests — `tests/test_slug.py`; must stay byte-for-byte untouched and green; new tests are added alongside.
- Existing CLI tests — `tests/test_cli.py:8-10`; `main(["slug", "Hello, World!"])` output must stay `"hello-world\n"`.
- Console script — `pyproject.toml:13-14` maps `textkit` to `textkit.cli:main`; unchanged.
- README — `README.md:4-8`; describes `slugify` and `textkit slug <text>` only in prose and does not enumerate options, so no change is required.
- No stored data, file formats, or external services are involved.

## Constraints

- **Default output is frozen.** `slugify(text)` with no other arguments must return exactly what it returns today for every input; source: intent, and the parametrized cases in `tests/test_slug.py:8-31` which must pass unmodified.
- **Standard library only, Python 3.12+.** `pyproject.toml:10-11` declares `requires-python = ">=3.12"` and `dependencies = []`; `AGENTS.md` repeats it. No new runtime dependency, so `uv.lock` need not change.
- **Helpers stay in `slug.py`.** Source: intent constraints. `AGENTS.md` layout rule is one module per concern.
- **Function size and docstrings.** `AGENTS.md` style section; `slugify` must stay small, so word-boundary truncation belongs in a documented helper in `slug.py` rather than inlined.
- **Line length 100.** `pyproject.toml:29-30` (`[tool.ruff] line-length = 100`), enforced by `make lint` (`Makefile:6-7`).
- **Checks.** `make test` (`Makefile:3-4`, `uv run --frozen pytest`) and `make lint` must both exit 0.
- **Tests per module.** `AGENTS.md` layout: new slug tests go in `tests/test_slug.py`, new CLI tests in `tests/test_cli.py`.
- **Idempotence must survive the new options.** `tests/test_slug.py:29-31` asserts `slugify(slugify(x)) == slugify(x)`; the same must hold when the same `separator` and `max_length` are passed on both calls, which is why alphanumeric separators are rejected.
- **CLI argument errors go through argparse.** `cli.py:44-45` uses `parser.error` and `tests/test_cli.py:25-35` assert exit code 2 for usage errors; a bad `--max-length` must fail the same way rather than with a traceback.
- **Boundaries.** `Makefile`, `AGENTS.md`, `CLAUDE.md`, `REVIEW.md` are not to be edited (`AGENTS.md` boundaries section).

## Acceptance criteria

1. `tests/test_slug.py` and `tests/test_cli.py` are unchanged from `main` and every test in them passes.
2. `slugify("Hello World")` returns `"hello-world"`; `slugify("snake_case_name")` returns `"snake-case-name"`; `slugify("")` and `slugify("!!! ???")` return `""` (default behavior unchanged).
3. `slugify("Hello World", separator="_")` returns `"hello_world"`, and `slugify("snake_case_name", separator="_")` returns `"snake_case_name"`.
4. `slugify("  Trim   me  ", separator="_")` returns `"trim_me"` (separator is collapsed and stripped from both ends).
5. `slugify("Hello, World! 2026", separator="")` returns `"helloworld2026"`.
6. `slugify("Rev 2.0 / final", separator="__")` returns `"rev__2__0__final"` (multi-character separators work).
7. For `s = slugify("Hello, World! 2026", separator="_")`, `slugify(s, separator="_")` returns `s`; the same holds with `separator=""`.
8. `slugify("the quick brown fox")` returns `"the-quick-brown-fox"` (19 characters), confirming `max_length` defaults to no cap.
9. `slugify("the quick brown fox", max_length=100)` returns `"the-quick-brown-fox"` (cap larger than slug is a no-op).
10. `slugify("the quick brown fox", max_length=10)` returns `"the-quick"`; with `max_length=9` returns `"the-quick"`; with `max_length=8` returns `"the"` (cut back to the last whole word, never a trailing separator).
11. `slugify("the quick brown fox", max_length=2)` returns `"th"` (first word longer than the cap is hard-cut so the result is non-empty).
12. `slugify("the quick brown fox", separator="_", max_length=10)` returns `"the_quick"`; `slugify("the quick brown fox", separator="", max_length=5)` returns `"thequ"`.
13. For `t = slugify("the quick brown fox", max_length=10)`, `slugify(t, max_length=10)` returns `t` (truncated output is stable under the same options).
14. `slugify("", separator="_", max_length=5)` and `slugify("!!! ???", max_length=3)` return `""`.
15. `slugify("a b", separator="x")` raises `ValueError`; `slugify("a b", separator="1")` raises `ValueError`.
16. `slugify("a b", max_length=0)` raises `ValueError`; `slugify("a b", max_length=-1)` raises `ValueError`.
17. `main(["slug", "Hello, World!"])` returns 0 and prints `"hello-world\n"` (unchanged).
18. `main(["slug", "--separator", "_", "Hello, World!"])` returns 0 and prints `"hello_world\n"`.
19. `main(["slug", "--max-length", "5", "Hello, World! 2026"])` returns 0 and prints `"hello\n"`.
20. `main(["slug", "--max-length", "abc", "Hello"])` and `main(["slug", "--max-length", "0", "Hello"])` raise `SystemExit` with code 2 and write a usage message to stderr.
21. `textkit slug --help` lists both `--separator` and `--max-length` with their defaults.
22. The `slugify` docstring in `src/textkit/slug.py` describes `separator`, `max_length`, the whole-word cut rule, the single-long-word fallback, and the two `ValueError` conditions; the word "hyphen" no longer describes the output unconditionally.
23. `make test` exits 0 and `make lint` exits 0.
24. New tests covering criteria 3 through 16 exist in `tests/test_slug.py` and covering 18 through 20 in `tests/test_cli.py`.

## Flagged concerns

- **Single-long-word fallback contradicts "never mid-word."** Criterion 11 hard-cuts when no whole word fits; the alternative is returning `""`, which loses the whole slug for a filename or column. Reviewer should confirm this trade-off is acceptable.
- **Truncation must not strip after cutting.** Cutting `"the-quick-brown"` at 10 gives `"the-quick-"`; the implementation must back up to the last separator before position `max_length`, not just `rstrip` the result, or a partial word like `"the-quick-br"` can leak through at other lengths.
- **Separator validation is the only new failure path.** Rejecting alphanumeric separators is a judgment call; without it, `separator="x"` would turn `"a b"` into `"axb"` and idempotence would silently break. If the reviewer prefers no validation, criterion 15 is the only one to drop.
- **Empty separator makes the cap a hard cut.** With `separator=""` there are no boundaries, so criterion 12's `"thequ"` ends mid-word by design. Document it so it is not reported as a bug.
- **CLI options are an inferred scope.** The intent names `textkit slug` as affected but never says "add flags." Criteria 17 through 21 depend on that reading; striking them leaves the library change intact.
- **argparse and an empty `--separator`.** `--separator ""` must reach `slugify` as the empty string; a `default`/`or` idiom that treats `""` as unset would break the compact-ID use case.
- **`max_length` counts characters of the ASCII result.** After `_to_ascii` the slug is pure ASCII, so characters equal bytes; input length is irrelevant to the cap.
- **Existing docstring is now partly wrong.** `slug.py:18-22` says "hyphen-separated" and "collapses to a single hyphen"; `REVIEW.md` compliance pass will flag a stale docstring, so criterion 22 is not optional.
- **`_SEPARATOR_RUN` name may mislead.** It matches the input runs, not the output separator; renaming is not required but a reviewer may ask why a hyphen-free slug is produced by something called a separator run.

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

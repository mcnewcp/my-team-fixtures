# Role: plan (read-only)

You are the plan role of an automated software factory, working on issue 7. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

Do not create, edit or delete any file, and do not run anything that writes (tests, installs,
formatters, git commands that change state). Read with whatever read-only means your tools give
you: a file-reading/search tool if you have one, otherwise read-only shell commands such as
`cat`, `sed -n`, `grep`, `git diff`, `git log`. Read and search the repository as much as you
need; the factory writes every file.

## The spec

## Problem

`src/textkit/cli.py::build_parser` accepts only a file argument for `stats`. `main` reads that file as UTF-8 and prints `_format_stats(text)`, so scripts must parse the human-readable report. The installed command resolves to `textkit.cli:main` through `pyproject.toml`.

`tests/test_cli.py::test_stats_command_reports_counts` checks only selected substrings, so it does not currently protect the complete text output against formatting regressions.

## Proposed outcome

Add `--format` to the `stats` subcommand in `src/textkit/cli.py::build_parser`, accepting `text` and `json`, with `text` as the default.

Omitting the option or specifying `--format text` must preserve the current stdout byte for byte, including indentation and the final newline. With `--format json`, `main` must print one JSON object on one line, followed by a newline, containing exactly these keys in this order:

- `words`: integer returned by `src/textkit/stats.py::word_count(text)`.
- `chars`: integer returned by `src/textkit/stats.py::char_count(text)`.
- `top`: an array of two-element `[word, count]` arrays, preserving the order returned by `src/textkit/stats.py::top_words(text, TOP_WORDS_SHOWN)`.

Both formats use `src/textkit/cli.py::TOP_WORDS_SHOWN`, currently 3. JSON rendering belongs in a small dedicated function alongside `_format_stats`, as required by the intent. Successful calls continue to return 0, and the existing missing-file error behavior remains intact.

## Affected users and systems

- CLI callers — `src/textkit/cli.py::build_parser` and `main` gain the format choice for `textkit stats`; `pyproject.toml` retains the existing command entry point.
- Output consumers — `src/textkit/cli.py::_format_stats` remains the text contract; the adjacent JSON renderer supplies the new machine-readable contract.
- Library callers — `src/textkit/stats.py` and the exports in `src/textkit/__init__.py` retain their existing behavior and interfaces.
- CLI tests — `tests/test_cli.py` gains exact text-output coverage and JSON serialization, option-validation, and error-path coverage.
- Statistics tests — `tests/test_stats.py` remains the reference for counting, case-insensitive ranking, and alphabetical tie-breaking.
- Documentation — `README.md` currently describes CLI output as plain text; its command description should briefly acknowledge the optional JSON format.
- Files and external systems — `src/textkit/cli.py::main` continues reading a local UTF-8 file and writing stdout/stderr; this change introduces no stored format or external-service integration.

## Constraints

- Use standard-library `json.dumps`, without key sorting or pretty-printing; default separators are acceptable. This is required by the intent and fits the empty runtime dependency list in `pyproject.toml`.
- Preserve text output exactly as produced by `src/textkit/cli.py::_format_stats` and the newline added by `main`.
- Preserve statistics semantics from `src/textkit/stats.py`: whitespace-separated tokens, character counts including whitespace, lowercase frequency keys, descending frequency order, and alphabetical tie-breaking. JSON must represent existing results without changing the helpers.
- Preserve input and error semantics from `src/textkit/cli.py::main`, including UTF-8 reading, the `Path.is_file()` check, and the existing `parser.error` diagnostic for a missing file.
- Keep the option confined to the `stats` parser in `src/textkit/cli.py::build_parser`; the existing `slug` command remains compatible.
- Repository conventions remain governed by `AGENTS.md`. This read-only spec stage follows `work/7/prompts/spec-1.md`; implementation checks are acceptance requirements, not checks executed during specification.

## Acceptance criteria

1. Given a UTF-8 file containing exactly `the cat sat on the mat the cat`, both `main(["stats", path])` and `main(["stats", path, "--format", "text"])` return 0, emit no stderr, and produce exactly `words: 8\nchars: 30\ntop:\n  the: 3\n  cat: 2\n  mat: 1\n`. Assert complete output equality in `tests/test_cli.py`.
2. Given that same file, `main(["stats", path, "--format", "json"])` returns 0 and emits no stderr. Parsing stdout with `json.loads` yields exactly `{"words": 8, "chars": 30, "top": [["the", 3], ["cat", 2], ["mat", 1]]}`.
3. JSON CLI coverage in `tests/test_cli.py` explicitly verifies that `words` and `chars` are integers, `top` is a list, and every entry is a two-element list containing a string and an integer. Decoded key order is `words`, `chars`, `top`; stdout contains one JSON line ending in a newline.
4. For an empty file, JSON output decodes to `{"words": 0, "chars": 0, "top": []}` and the command returns 0.
5. For a file containing exactly `Dog dog DOG cat`, JSON output decodes to `{"words": 4, "chars": 15, "top": [["dog", 3], ["cat", 1]]}`, confirming case normalization and an unpadded result when fewer than three distinct words exist.
6. Passing an unsupported value such as `--format yaml` to `stats` raises `SystemExit(2)` through argparse, reports an invalid choice on stderr, and emits no report on stdout; `stats --help` exposes the supported choices.
7. For a missing file, omitted format, explicit `text`, and explicit `json` all retain `SystemExit(2)`, the existing `no such file: <path>` diagnostic on stderr, and empty stdout. Extend coverage in `tests/test_cli.py`.
8. Existing `slug` and no-subcommand behavior covered by `tests/test_cli.py`, and helper behavior covered by `tests/test_stats.py`, remain passing.
9. On the completed implementation, `make test` and `make lint`, as defined in `Makefile`, both exit 0.

## Flagged concerns

- `tests/test_cli.py::test_stats_command_reports_counts` currently uses substring assertions; retaining only those assertions could miss violations of the required text compatibility.
- `src/textkit/stats.py::top_words` returns Python tuples; the observable JSON contract requires arrays, so verify the decoded structure rather than Python representations or substrings.
- The sample in `tests/test_stats.py` contains tied frequencies; preserving `top_words` ordering is necessary to keep `mat` as the third result.
- `src/textkit/stats.py::char_count` counts decoded characters, including whitespace; JSON must not substitute byte length or trim file contents.
- `src/textkit/cli.py::main` currently lets UTF-8 decoding and other read failures propagate after the file check; changing that behavior would expand the requested scope.

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

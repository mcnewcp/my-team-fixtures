# Role: build (write mode)

You are the build role of an automated software factory, working on issue 7. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

You may read, create and edit files in this worktree, and you may run `make`, `pytest`, `uv` and
`python`. Nothing else. Never run `git commit`, `git push`, `git add`, any other `git` write, or
`gh`. Never touch anything under `.github/`, `.claude/`, `.codex/`, `.devcontainer/`, and never
edit `Makefile`, `factory.toml`, `AGENTS.md`, `CLAUDE.md` or `REVIEW.md`. The factory commits,
pushes and talks to GitHub; a stage that edits a protected path is rejected and thrown away.
Under `work/` you may edit exactly one file: `work/7/plan.md`.

## The plan

Add `textkit stats <file> --format {text,json}`, defaulting to the existing text report. JSON must contain ordered `words`, `chars`, and `top` fields on one line with a final newline.

## Files that change

- `src/textkit/cli.py` — Add the stats-only format option, a dedicated JSON renderer, and format selection in `main` while preserving input handling and text output.
- `tests/test_cli.py` — Replace substring assertions with exact text assertions; add JSON contract, invalid-option, and help coverage; extend missing-file coverage across formats.
- `README.md` — Briefly document the default text output and optional `textkit stats <file> --format json` command.

## Order of work

1. Extend `tests/test_cli.py` before changing implementation:
   - Parameterize `test_stats_command_reports_counts` with `format_args` values `[]` and `["--format", "text"]`, using IDs `default` and `text`. Write exactly `the cat sat on the mat the cat` as UTF-8. Both invocations must return 0, emit empty stderr, and produce exactly `words: 8\nchars: 30\ntop:\n  the: 3\n  cat: 2\n  mat: 1\n`. This replaces the existing substring assertions. Covers acceptance criterion 1.
   - Import standard-library `json` and add parameterized `test_stats_command_reports_json`, using the cases below. Write each input as UTF-8 and invoke `main(["stats", str(sample), "--format", "json"])`. Assert return value 0 and empty stderr. Decode stdout with `json.loads` and compare the entire object with the expected value. Also assert `list(decoded) == ["words", "chars", "top"]`, that `words` and `chars` have exact type `int`, that `top` is a list, and that each entry is a two-element list containing a string and an integer. Assert `stdout.endswith("\n")` and `stdout.count("\n") == 1`. Covers acceptance criteria 2–5 and the UTF-8/whitespace constraint.

   | Case ID | Exact input | Expected decoded JSON |
   | --- | --- | --- |
   | `sample` | `the cat sat on the mat the cat` | `{"words": 8, "chars": 30, "top": [["the", 3], ["cat", 2], ["mat", 1]]}` |
   | `empty` | Empty string | `{"words": 0, "chars": 0, "top": []}` |
   | `mixed-case` | `Dog dog DOG cat` | `{"words": 4, "chars": 15, "top": [["dog", 3], ["cat", 1]]}` |
   | `unicode-whitespace` | ` café\tCAFÉ\n` | `{"words": 2, "chars": 11, "top": [["café", 2]]}` |

   - Add `test_stats_command_rejects_an_invalid_format`: create a valid input file, invoke stats with `--format yaml`, and assert `SystemExit(2)`, empty stdout, and stderr containing `invalid choice` and `yaml`. Covers acceptance criterion 6.
   - Add `test_stats_command_help_lists_formats`: invoke `main(["stats", "--help"])`, assert `SystemExit(0)`, empty stderr, and stdout containing `--format {text,json}`. Covers acceptance criterion 6.
   - Parameterize `test_stats_command_rejects_a_missing_file` with `[]`, `["--format", "text"]`, and `["--format", "json"]`, using IDs `default`, `text`, and `json`. For every invocation assert `SystemExit(2)`, empty stdout, and stderr containing the complete `f"no such file: {missing_path}"` diagnostic. Covers acceptance criterion 7.
   - Retain `test_slug_command_prints_slug` and `test_no_subcommand_is_a_usage_error` as existing regression coverage for acceptance criterion 8.

2. Run proof command P1 before implementation. Confirm the default text and default missing-file cases pass. Confirm the new format behavior fails, particularly `test_stats_command_reports_json[sample]` and `test_stats_command_reports_counts[text]`, because the parser does not yet accept `--format`.

3. Update `src/textkit/cli.py`:
   - Import standard-library `json`.
   - In `build_parser`, add `stats_parser.add_argument("--format", choices=("text", "json"), default="text", help="output format (default: text)")` beside the file argument.
   - Add `_format_stats_json(text: str) -> str` beside `_format_stats`, with a docstring stating that it returns a one-line JSON statistics report. Return `json.dumps` of a dictionary constructed in this exact insertion order: `"words": word_count(text)`, `"chars": char_count(text)`, `"top": top_words(text, TOP_WORDS_SHOWN)`. Use default serialization options; tuple entries are serialized as JSON arrays. The helper returns the string without adding a newline.
   - Keep `_format_stats` unchanged.
   - In `main`, retain the slug branch and existing `Path.is_file()` check and `parser.error` diagnostic. After that check, read the file once with `args.file.read_text(encoding="utf-8")`. Select `_format_stats_json` when `args.format == "json"`, otherwise `_format_stats`, and pass the selected renderer's result to one `print` call. Retain success return value 0.
   - Run P1 again and require every CLI test to pass. This implements acceptance criteria 1–7 and preserves the CLI behavior in criterion 8.

4. Update the introductory CLI description in `README.md` to say the commands print plain text by default and stats also supports JSON via `textkit stats <file> --format json`. Review the wording against the implemented option and defaults.

5. Run P2 and P3 on the completed change and require both to exit 0. P2 verifies the existing statistics and slug behavior required by acceptance criterion 8; together the commands satisfy acceptance criterion 9.

## Proof

Run these commands from the repository root during implementation. No tests or other writing commands were executed during this read-only planning stage.

| ID | Exact command | Required evidence |
| --- | --- | --- |
| P1 | `uv run --frozen pytest tests/test_cli.py` | Before implementation, demonstrates the new format tests fail while existing default behavior remains valid. After implementation, exit 0 proves exact default/explicit text output, JSON values and structure, key order, one-line framing, empty and mixed-case inputs, UTF-8 character counting, option validation/help, missing-file behavior, and existing slug/no-subcommand behavior. Covers acceptance criteria 1–7 and the CLI portion of 8. |
| P2 | `make test` | Exit 0 proves the full suite passes, including all CLI tests, unchanged `tests/test_stats.py` counting/ranking/tie-breaking coverage, and `tests/test_slug.py`. Covers acceptance criteria 1–8 and the test requirement in 9. |
| P3 | `make lint` | Exit 0 proves the completed change passes the repository's Ruff check. Covers the lint requirement in acceptance criterion 9. |

## Risks

- Text formatting could change through shared rendering or newline handling. Leave `_format_stats` intact and protect both text invocation forms with full stdout equality.
- JSON could have reordered keys, object-shaped top entries, incorrect scalar types, or multiple lines. Use the ordered dictionary literal and default `json.dumps`; decoded equality, explicit type/order checks, and newline assertions catch these mistakes.
- Ranking, normalization, or the top-word limit could diverge between formats. Both renderers call the existing helpers with `TOP_WORDS_SHOWN`; the sample verifies alphabetical tie-breaking and truncation, while mixed-case and empty cases verify normalization and unpadded results.
- Character counts could accidentally use byte lengths or stripped input. Preserve UTF-8 `read_text` and `char_count(text)`; the Unicode/whitespace case catches either regression.
- Format selection could disturb slug handling or file errors. Keep the option on the stats parser, select the renderer after the existing slug branch and file check, and verify all missing-file variants. Preserve propagation of decoding and other read failures by adding no exception handling.

All flagged concerns are addressed; no unresolved design questions remain.


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


## Checks

$ make test
uv run --frozen pytest
...................                                                      [100%]
19 passed in 0.06s
Using CPython 3.14.7
Creating virtual environment at: .venv
   Building textkit @ file:///home/mcnewcp/personal/my-team-fixtures/.factory/worktrees/7
      Built textkit @ file:///home/mcnewcp/personal/my-team-fixtures/.factory/worktrees/7
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
`work/7/plan.md` in this same pass: add every new path to "## Files that change" by exact
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

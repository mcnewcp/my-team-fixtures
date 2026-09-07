# Role: review (read-only)

You are the review role of an automated software factory, working on issue 7. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

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


## The diff under review

The diff under review is not reproduced here. It is the file `.factory/tmp/review-1.diff`, relative to the root of this worktree: 6774 bytes, 183 lines.

Read it completely before you judge anything: start at the beginning and keep going until you have seen line 183 — with a file-reading tool, continue with offset/limit; with a shell, `cat` the file, or walk it in slices with `sed -n '1,400p'`, `sed -n '401,800p'` and so on. A single read may return only the first part of the file. Do not review from a partial read.

## Check output from the last stage

$ make test
uv run --frozen pytest
............................                                             [100%]
28 passed in 0.05s
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

This is review round 1 of issue 7, over the commit 84f3e0000ee9 (0 fix round(s) so far).

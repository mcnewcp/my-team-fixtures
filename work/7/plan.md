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

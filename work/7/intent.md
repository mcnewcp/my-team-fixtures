# Intent: Add --format json to textkit stats

- number: 7
- url: https://github.com/mcnewcp/my-team-fixtures/issues/7
- labels: factory
- snapshot_at: 2026-09-07T16:16:03Z
- sha256: 581bb892133e9f8b56171f463358f6ca6f6392d2ba212d19ae688664813b2a84

---

## Problem

`textkit stats <file>` prints a human-readable block:

```
words: 8
chars: 30
top:
  the: 3
  cat: 2
  mat: 1
```

That is fine to read but awkward to consume from a script — anything that wants the
numbers has to parse indentation and colons, and the parsing breaks the moment the
wording changes. There is no machine-readable output mode.

## Proposed outcome

Add a `--format` option to the `stats` subcommand with choices `text` (the default,
byte-for-byte the current output) and `json`.

With `--format json`, `textkit stats` prints a single JSON object to stdout, followed
by a newline, with exactly these keys:

- `words` — integer, the value of `word_count(text)`
- `chars` — integer, the value of `char_count(text)`
- `top` — a list of `[word, count]` two-element lists (JSON arrays, not objects), in
  the order `top_words` returns them, using the same limit as the text format (3)

Example for a file containing `the cat sat on the mat the cat`:

```
$ textkit stats sample.txt --format json
{"words": 8, "chars": 30, "top": [["the", 3], ["cat", 2], ["mat", 1]]}
```

Serialize with `json.dumps` (default separators are fine); do not sort keys, and do not
pretty-print. Exit code stays 0 on success and the missing-file error path is unchanged.

## Affected users and systems

`textkit.cli` only. Scripts that shell out to `textkit stats` gain a stable contract;
the default `text` output is unchanged, so no existing caller breaks.

## Constraints

- Standard library only (`json` is already available); no new dependencies.
- Keep `main` small — put the JSON rendering in its own small function next to the
  existing `_format_stats`.
- Add CLI tests for both formats, including one that round-trips the JSON with
  `json.loads` and asserts `top` is a list of two-element lists.
- `make test` and `make lint` must stay green.

## Open questions

None.

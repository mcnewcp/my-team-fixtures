# Role: spec (read-only)

You are the spec role of an automated software factory, working on issue 7. Your final answer is a single JSON object matching the output schema the harness was given; nothing else is the deliverable.

Do not create, edit or delete any file, and do not run anything that writes (tests, installs,
formatters, git commands that change state). Read with whatever read-only means your tools give
you: a file-reading/search tool if you have one, otherwise read-only shell commands such as
`cat`, `sed -n`, `grep`, `git diff`, `git log`. Read and search the repository as much as you
need; the factory writes every file.

## The intent

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


## What to produce

Write a requirements and design spec for THIS codebase. Ground every claim in code that is
actually here: name the modules, files and entry points the change touches. A generic restatement
of the intent is a failure.

`markdown` is the whole spec, starting at a level-2 heading, with these sections in this order:

## Problem
What is wrong or missing today, in terms of the code as it exists. Name the files and the
behaviour a user or caller sees now.

## Proposed outcome
The observable behaviour once the change lands, written so a reviewer can tell whether it
happened.

## Affected users and systems
What depends on this: callers, commands, stored data and formats, external services, tests,
documentation. One line each, with the path.

## Constraints
Compatibility, performance, security, dependency and convention constraints the implementation
must respect. For each one inferred from the repository, say where you got it.

## Acceptance criteria
A numbered list. Each item is checkable by a human or a test: an input, an action, an expected
result. Nothing that is a matter of taste.

## Flagged concerns
Risks, ambiguities and likely regressions the implementer and the reviewer should watch, one line
of reasoning each. These are warnings, not blockers.

Do not write an "Open questions" section. The factory appends one from `open_questions`.

## The bar for open questions

`open_questions` stops the run and waits for a human, so use it only for a question that BLOCKS
implementation: you cannot decide what to build without an answer, and no defensible default
exists. Everything else is an assumption — state it in the spec ("Assumes X, because Y") and keep
going. Preferences, naming, and anything you can settle by reading the code are never open
questions. An empty list is the normal, good outcome.

Each open question is one self-contained sentence, answerable without this transcript, and says
what it blocks.

## Rules

- Scope is the intent and nothing more. Do not invent adjacent work.
- Say what and why, not how. The plan role designs the implementation.
- Where the intent conflicts with the codebase, say so under Flagged concerns and specify what
  the code makes possible.
- Cite paths and symbols whenever you assert something about the repository.
- Conventions come from AGENTS.md. Do not restate them.

## Stage note

Issue snapshot taken at 2026-09-07T16:16:03Z.

The previous attempt was discarded because: claude exited 1: You've hit your session limit · resets 12:50pm (America/Chicago)

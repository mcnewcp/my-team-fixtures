# Intent: Add textkit.truncate(text, width, ellipsis='…')

- number: 5
- url: https://github.com/mcnewcp/my-team-fixtures/issues/5
- labels: factory
- snapshot_at: 2026-09-07T02:02:03Z
- sha256: 6cc6cd11ba9b01cd94a8bb6403c54145a94555f3ea9b368f7e090072c2399632

---

## Problem

`textkit` can produce a slug or count words, but there is no way to shorten a string
to fit a fixed-width display (a terminal column, a table cell, a preview line). Callers
end up writing their own `text[:width]`, which cuts words in half and silently drops the
signal that the text was shortened at all.

## Proposed outcome

Add `truncate(text, width, ellipsis="…")` to a new `src/textkit/truncate.py`, re-exported
from `textkit/__init__.py`, with this behavior:

- If `len(text) <= width`, return `text` unchanged.
- Otherwise return a shortened string whose total length, **including the ellipsis**, is
  at most `width`.
- Truncation is word-boundary aware: cut at the last whitespace boundary that keeps the
  result within `width - len(ellipsis)`, then strip trailing whitespace before appending
  the ellipsis. If a single word is longer than the available room (there is no usable
  boundary), cut mid-word at exactly `width - len(ellipsis)` characters.
- `width < len(ellipsis)` raises `ValueError`. `width == len(ellipsis)` is legal and
  returns just the ellipsis when the text is longer than `width`.

Examples (default ellipsis `…`, one character):

- `truncate("hello world", 20)` -> `"hello world"` (already short enough)
- `truncate("hello world", 11)` -> `"hello world"` (exactly `width`)
- `truncate("hello world", 8)` -> `"hello…"` (room is 7; last boundary is after
  `hello`; 6 characters total, which is allowed to be shorter than `width`)
- `truncate("supercalifragilistic", 10)` -> `"supercali…"` (room is 9, no whitespace,
  so cut mid-word at 9 characters; 10 characters total)
- `truncate("a b", 1)` -> `"…"` (room is 0)
- `truncate("hello world", 6, ellipsis="...")` -> `"hel..."` (room is 3, no whitespace
  in `"hel"`, so cut mid-word)
- `truncate("hello world", 0)` -> raises `ValueError` (0 < `len("…")`)

## Affected users and systems

Library callers of `textkit` and anyone formatting text for fixed-width output. No
existing function changes; `textkit.cli` does not use `truncate` yet.

## Constraints

- Standard library only; no new dependencies.
- Keep the function small and documented, per `AGENTS.md`.
- Add `tests/test_truncate.py` covering: no-op case, word-boundary cut, mid-word cut,
  a custom multi-character ellipsis, `width == len(ellipsis)`, and the `ValueError`.
- `make test` and `make lint` must stay green.

## Open questions

None.

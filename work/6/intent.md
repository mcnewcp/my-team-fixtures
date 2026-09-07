# Intent: word_count should ignore punctuation-only tokens

- number: 6
- url: https://github.com/mcnewcp/my-team-fixtures/issues/6
- labels: factory
- snapshot_at: 2026-09-07T02:08:43Z
- sha256: 7051df144ced802103b9489c285fa6e10363805b348edf24fadb25b2a5f35511

---

## Problem

`word_count` splits on whitespace and counts every resulting token, so punctuation that
stands alone is counted as a word. Reported counts are inflated for ordinary prose that
uses em dashes, ellipses, or bullet characters:

- `word_count("hello -- world")` returns `3`, but there are 2 words.
- `word_count("one ... two")` returns `3`, but there are 2 words.
- `word_count("* item")` returns `2`, but there is 1 word.

`textkit stats` reports this inflated number, so the CLI is wrong in the same way.

## Proposed outcome

A token that contains no alphanumeric character is not a word. Concretely, in
`src/textkit/stats.py`, `word_count` counts only tokens matching "contains at least one
character for which `str.isalnum()` is true".

Expected results after the change:

- `word_count("hello -- world")` -> `2`
- `word_count("one ... two")` -> `2`
- `word_count("* item")` -> `1`
- `word_count("hello, world!")` -> `2` (punctuation attached to a word still counts)
- `word_count("don't stop")` -> `2`
- `word_count("2026 was fine")` -> `3` (digits are alphanumeric)
- `word_count("")` -> `0`, `word_count("   ")` -> `0`
- `word_count("-- ... !!!")` -> `0`

`top_words` must apply the same rule, so punctuation-only tokens never appear in the
top list: `top_words("a -- a -- b", 2)` -> `[("a", 2), ("b", 1)]`. `char_count` is
unchanged.

## Affected users and systems

Every caller of `word_count` and `top_words`, and the `textkit stats` CLI output.
Existing counts will drop for text containing standalone punctuation; this is the fix,
not a regression.

## Constraints

- Standard library only. Keep the shared tokenizing logic in one place rather than
  duplicating the rule in both functions.
- Update `tests/test_stats.py` with the examples above; existing assertions that rely
  on the old behavior should be corrected, not deleted.
- `make test` and `make lint` must stay green.

## Open questions

None.

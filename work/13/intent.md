# Intent: Filter stopwords in textkit stats

- number: 13
- url: https://github.com/mcnewcp/my-team-fixtures/issues/13
- labels: factory
- snapshot_at: 2026-09-07T13:04:06Z
- sha256: 06bfd985da4141b9f4f96aa04558a759871fb911d4f48c409de52af245be02a9

---

## Problem

`textkit stats` and `top_words()` rank function words ("the", "and", "of") at the top of every real document, which makes the top-words list useless for summarising content.

## Proposed outcome

`top_words()` and `textkit stats` can exclude stopwords for a chosen language. **The maintainer has not decided the questions below and they must be answered before any code is written; do not pick defaults on their behalf.**

## Affected users and systems

`src/textkit/stats.py`, `src/textkit/cli.py`, their tests, and the README.

## Constraints

- No third-party dependency may be added without explicit maintainer approval (none has been given).
- Any bundled word list needs a licence the maintainer has approved (none has been approved).

## Open questions

1. Which languages must be supported in the first version, and where do their stopword lists come from (bundled file with which licence, or a runtime download)?
2. Is stopword filtering the default behaviour of `stats`/`top_words`, or opt-in via a flag/parameter, and what is the flag called?
3. Should filtered words also be excluded from `word_count`, or only from the ranking?

# Intent: Make slugify configurable

- number: 8
- url: https://github.com/mcnewcp/my-team-fixtures/issues/8
- labels: factory
- snapshot_at: 2026-09-07T02:17:35Z
- sha256: 438c85ec8c43993a2a6756cb9d2807eceff1800122c13d699f813ee858523c84

---

## Problem

`slugify` always does exactly one thing: it lowercases, folds to ASCII, and joins the
remaining alphanumeric runs with a hyphen. People using `textkit` for things other than
URLs keep asking for two kinds of control it does not offer:

- **Separator.** Some outputs want underscores (Python identifiers, S3 key prefixes) or
  no separator at all (compact IDs). Today they post-process the result with `.replace()`,
  which is fine until the text legitimately contains a hyphen.
- **Maximum length.** Slugs feed into filenames and database columns with hard limits.
  Callers truncate afterwards and routinely end up with a trailing separator or a word
  chopped in half.

Both are worked around today by every caller in the same clumsy way, which is a sign the
library should own the behavior.

## Proposed outcome

`slugify` becomes configurable so that a caller can choose the separator character and
cap the length of the returned slug, without breaking any existing caller that just
calls `slugify(text)`.

## Affected users and systems

Every caller of `textkit.slugify`, including `textkit slug` on the command line. The
default behavior for a plain `slugify(text)` call must not change: `make test` must pass
with the existing `tests/test_slug.py` assertions untouched.

## Constraints

- Standard library only; no new dependencies.
- Keep `slugify` small and documented, per `AGENTS.md`; put any helper in `slug.py`.
- Existing behavior stays the default. Add tests for whatever new behavior is agreed.
- `make test` and `make lint` must stay green.

## Open questions

- What should the API shape be — additional keyword arguments on `slugify` (e.g.
  `separator=`, `max_length=`), or a small options object / a second function so the
  signature does not keep growing as more knobs arrive?
- What should the length cap actually mean: a hard character cut, or a cut back to the
  last whole word so the slug never ends mid-word or with a dangling separator? And is
  the default `None` (no cap) or some concrete number?

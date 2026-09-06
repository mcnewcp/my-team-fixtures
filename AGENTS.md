# Conventions for agents working in this repo

`textkit` is a small, dependency-free Python library plus a thin CLI. It is a fixture
repo: keep it small, obvious, and easy to read end to end.

## Layout

- src layout: importable code lives in `src/textkit/`, one module per concern
  (`slug.py`, `stats.py`, `cli.py`). Public names are re-exported from `__init__.py`.
- Tests live in `tests/`, one `test_<module>.py` per source module.
- Python 3.12+, standard library only at runtime. Dev tools (pytest, ruff) come from
  the `dev` dependency group in `pyproject.toml`.

## Checks

- Run `make test` and `make lint` before you consider a change done; both must exit 0.
- Both run through `uv run --frozen`, so `uv.lock` must stay in sync with
  `pyproject.toml`; if you change dependencies, run `uv lock` in the same change.

## Style

- Keep every function small and single-purpose, with a docstring saying what it
  returns. Line length is 100 (`ruff`).
- Add or update a test with every behavior change; a bug fix starts with a failing test.

## Boundaries

- Never edit `Makefile`, `AGENTS.md`, `CLAUDE.md`, or `REVIEW.md`.
- Do not commit, push, tag, or open pull requests. The operator tooling owns every
  commit and push.

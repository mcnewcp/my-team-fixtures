The maintainer’s answers resolve the specification’s blockers: support English, enable filtering by default, and exclude stopwords from both rankings and word counts. Their delegation authorizes the remaining choices below.

Use a small, originally curated English list embedded as a private `frozenset` in `stats.py`. Choose CC0-1.0 for the word-list data only, recording its original provenance and dedication in the source and README. No external corpus, download, runtime dependency, or separate data file is needed. The initial list is:

`a an and are as at be been being but by for from had has have he her his i in is it its not of on or our she that the their them they this to was we were will with you your`

Add keyword-only `language: str | None = "en"` to `top_words(text, n)` and `word_count(text)`. Omitted configuration enables English filtering; `language=None` disables filtering and restores existing results. Accept only the exact language identifier `en`; unsupported values raise a descriptive `ValueError`, including when `n` is non-positive. Valid configurations retain the existing empty result for non-positive `n`.

Expose `textkit stats FILE --language en` and `textkit stats FILE --no-stopwords`. Argparse validates language choices, including when disabling filtering. Pass `None` when `--no-stopwords` is present and otherwise pass the selected language through `main()` and `_format_stats()` to both statistics functions.

## Files that change

- `src/textkit/stats.py` — embed the list, share language resolution and token filtering, and extend the existing functions and docstrings.
- `src/textkit/cli.py` — add parser options and propagate the configuration into the report.
- `tests/test_stats.py` — establish default filtering, explicit configuration, compatibility, and edge cases.
- `tests/test_cli.py` — establish report contents, option behavior, and language errors.
- `README.md` — document the list, provenance, data licence, interfaces, defaults, counting changes, and limitations.

No new files or public exports are needed. No protected-file or operator changes are required. Factory-owned artifacts, including the plan, remain untouched.

Implement in this order:

1. Write the behavior tests first and run the focused suite to establish expected failures. For acceptance criteria 1–4, cover case-insensitive filtering, filtering before truncation, remaining frequencies, alphabetical ties, non-positive limits, empty/whitespace-only input, all-stopword input, and fewer remaining words than requested. Test both library functions with omitted configuration, explicit `en`, disabled filtering, and unsupported languages. Include unsupported-language validation with non-positive limits.
2. Update existing expectations deliberately. The existing sample has 30 characters and eight original tokens; default filtering leaves four tokens and ranks `cat: 2`, `mat: 1`, `sat: 1`. Explicitly disabled filtering must retain the original counts and ranking. Keep independent assertions for punctuation-bearing tokens such as `the,`, which remain eligible, and mixed whitespace.
3. Implement small private helpers in `stats.py` so counting and ranking use the same selected list and filtering rules. Preserve whitespace tokenization, `lower()` normalization, frequency ordering, alphabetical ties, and original character counting. Validate configuration before returning early for non-positive limits.
4. Wire the CLI configuration through `_format_stats()`. Test default and explicit English reports, disabled filtering, unsupported-language argparse errors with exit status 2, and empty rankings that still print `words:`, `chars:`, and `top:`. Retain the three-entry maximum and existing slug, missing-file, and missing-subcommand coverage.
5. Complete the documentation required by acceptance criterion 5, then run the proof commands. Keep functions small with return-value docstrings and retain the 100-character line limit.

The intentional compatibility risk is changed results for existing calls that omit configuration. Document `language=None` and `--no-stopwords` as migration paths. The curated list is deliberately limited; document its complete membership without suggesting comprehensive linguistic coverage. Punctuation stripping, stemming, and language detection remain outside scope.

## Proof

Run from the repository root during implementation:

- `uv run --frozen pytest tests/test_stats.py tests/test_cli.py` — run after writing tests, before implementation, to demonstrate the requested behavior is initially absent.
- `make test` — must exit 0 after implementation; verifies acceptance criteria 1–4 and existing regression coverage through the repository’s frozen environment.
- `make lint` — must exit 0; verifies the configured Ruff checks, completing acceptance criterion 6.
- `uv build --wheel` — builds the existing package without changing dependencies or packaging configuration.

Then verify that the built wheel contains working stopword data, independently of the source-tree import:

```sh
uv run --frozen python - <<'PY'
import sys
from pathlib import Path

wheel = max(Path('dist').glob('textkit-*.whl'), key=lambda p: p.stat().st_mtime)
sys.path.insert(0, str(wheel.resolve()))
import textkit

assert '.whl/' in textkit.__file__
assert textkit.word_count('the and of cat') == 1
assert textkit.top_words('the and of cat', 3) == [('cat', 1)]
assert textkit.word_count('the and of cat', language=None) == 4
PY
```

Review README coverage against acceptance criterion 5 and inspect `git diff --check` and `git diff --stat` for whitespace errors and intended scope. No implementation, file writes, GitHub access, or proof checks were performed during this planning pass.

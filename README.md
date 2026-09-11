# textkit

`textkit` is a very small, dependency-free Python library and command-line tool for
tidying up plain text. It turns a title into a URL-friendly slug (`slugify`) and
reports simple statistics about a document — word count, character count, and the
most frequent words (`word_count`, `char_count`, `top_words`). The same functions are
exposed on the command line as `textkit slug <text>` and `textkit stats <file>`, which
print plain text meant to be read by a person or piped into another tool.

This repository is a **disposable fixture** for the software-factory prototype. It
exists so the factory has a small, realistic Python project to open issues against,
branch from, and send pull requests to; nothing here is used in production and any
commit may be rewritten or deleted without notice. The project deliberately stays
tiny — src layout, no runtime dependencies, `make test` and `make lint` as the only
entry points — so that an end-to-end factory run is quick to read and easy to reset.

## Stopword filtering

Word counts and rankings exclude English stopwords by default. English is the only
supported language, selected with the exact identifier `en`. This changes the
results of existing calls that omit configuration. To restore the original counts
and rankings, use `language=None` in Python or `--no-stopwords` on the command line.
Character counts always include every original character, including whitespace.

Both library functions accept a keyword-only `language: str | None = "en"`:

```python
from textkit import char_count, top_words, word_count

text = "the cat sat on the mat the cat"
word_count(text)                       # 4
word_count(text, language="en")        # 4
top_words(text, 3)                     # [('cat', 2), ('mat', 1), ('sat', 1)]
top_words(text, 3, language="en")      # [('cat', 2), ('mat', 1), ('sat', 1)]
word_count(text, language=None)        # 8
top_words(text, 3, language=None)      # [('the', 3), ('cat', 2), ('mat', 1)]
char_count(text)                       # 30
```

Unsupported language values raise a descriptive `ValueError`, even on empty input
or when `top_words()` receives a non-positive limit. For valid configurations, a
non-positive limit returns `[]`.

```sh
textkit stats document.txt                  # English filtering by default
textkit stats document.txt --language en    # Explicit English filtering
textkit stats document.txt --no-stopwords   # Include every token
```

`--no-stopwords` disables filtering for both the `words:` count and the `top:`
ranking, including when combined with `--language en`. Unsupported `--language`
values are argparse usage errors (exit status 2), even with `--no-stopwords`.
Reports retain `words:`, `chars:`, and `top:`, with at most three ranked entries.
Empty input or input containing only filtered stopwords has zero words and an empty
ranking; the report still prints all three labels.

Tokens are split on whitespace and normalized with `lower()` for both matching and
ranking. Filtering happens before the ranking limit is applied. Remaining words
sort by descending frequency with alphabetical tie-breaking. Punctuation stays
part of tokens: `the` is filtered, but `the,` remains eligible. There is no
punctuation stripping, stemming, or language detection.

The complete English list is deliberately small, originally curated for textkit,
and embedded in `src/textkit/stats.py`. It does not claim comprehensive linguistic
coverage and uses no external corpus, downloads, or extra dependencies. This
word-list data only is dedicated to the public domain under CC0-1.0; the dedication
does not change the licensing of the surrounding code. Its complete membership is:

```text
a an and are as at be been being but by for from had has have he her his i in is it its
not of on or our she that the their them they this to was we were will with you your
```

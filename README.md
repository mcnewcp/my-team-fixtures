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

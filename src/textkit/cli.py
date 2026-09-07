"""Command-line interface: ``textkit slug <text>`` and ``textkit stats <file>``."""

from __future__ import annotations

import argparse
from pathlib import Path

from .slug import slugify
from .stats import char_count, top_words, word_count

TOP_WORDS_SHOWN = 3


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``textkit`` command."""
    parser = argparse.ArgumentParser(prog="textkit", description="Small text utilities.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    slug_parser = subcommands.add_parser("slug", help="print a slug for TEXT")
    slug_parser.add_argument("text", help="text to slugify")

    stats_parser = subcommands.add_parser("stats", help="print statistics for FILE")
    stats_parser.add_argument("file", type=Path, help="UTF-8 text file to summarize")
    stats_parser.add_argument(
        "--stopwords",
        metavar="LANG",
        help="exclude the stopwords of language LANG from the top list (supported: en)",
    )

    return parser


def _format_stats(text: str, *, stopwords: str | None = None) -> str:
    """Render the plain-text statistics report for ``text``."""
    lines = [f"words: {word_count(text)}", f"chars: {char_count(text)}", "top:"]
    ranked = top_words(text, TOP_WORDS_SHOWN, stopwords=stopwords)
    lines += [f"  {word}: {count}" for word, count in ranked]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI over ``argv`` (defaults to ``sys.argv``) and return the exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "slug":
        print(slugify(args.text))
        return 0

    if not args.file.is_file():
        parser.error(f"no such file: {args.file}")
    text = args.file.read_text(encoding="utf-8")
    try:
        report = _format_stats(text, stopwords=args.stopwords)
    except ValueError as exc:
        parser.error(str(exc))
    print(report)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

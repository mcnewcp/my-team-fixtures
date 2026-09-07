"""Command-line interface: ``textkit slug [options] <text>`` and ``textkit stats <file>``."""

from __future__ import annotations

import argparse
from pathlib import Path

from .slug import slugify
from .stats import char_count, top_words, word_count

TOP_WORDS_SHOWN = 3


def _positive_int(value: str) -> int:
    """Return ``value`` parsed as an int of at least 1, or raise ``argparse.ArgumentTypeError``."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from None
    if number < 1:
        raise argparse.ArgumentTypeError(f"expected a value of at least 1, got {value!r}")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the ``textkit`` command."""
    parser = argparse.ArgumentParser(prog="textkit", description="Small text utilities.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    slug_parser = subcommands.add_parser("slug", help="print a slug for TEXT")
    slug_parser.add_argument("text", help="text to slugify")
    slug_parser.add_argument(
        "--separator",
        default="-",
        help="text placed between words (default: %(default)r)",
    )
    slug_parser.add_argument(
        "--max-length",
        type=_positive_int,
        default=None,
        metavar="N",
        help="max slug length in characters (default: no limit)",
    )

    stats_parser = subcommands.add_parser("stats", help="print statistics for FILE")
    stats_parser.add_argument("file", type=Path, help="UTF-8 text file to summarize")

    return parser


def _format_stats(text: str) -> str:
    """Render the plain-text statistics report for ``text``."""
    lines = [f"words: {word_count(text)}", f"chars: {char_count(text)}", "top:"]
    lines += [f"  {word}: {count}" for word, count in top_words(text, TOP_WORDS_SHOWN)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI over ``argv`` (defaults to ``sys.argv``) and return the exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "slug":
        try:
            print(slugify(args.text, separator=args.separator, max_length=args.max_length))
        except ValueError as exc:
            parser.error(str(exc))
        return 0

    if not args.file.is_file():
        parser.error(f"no such file: {args.file}")
    print(_format_stats(args.file.read_text(encoding="utf-8")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

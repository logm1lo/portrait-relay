"""Lightweight command-line entry point for Portrait Relay."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from portrait_relay import __version__
from portrait_relay.config import DisclosureMode


def build_parser() -> argparse.ArgumentParser:
    """Build the public parser without importing media or ML dependencies."""

    parser = argparse.ArgumentParser(
        prog="portrait-relay",
        description="Local, noncommercial face-swap research application.",
    )
    parser.add_argument("-s", "--source", help="source face image")
    parser.add_argument("-t", "--target", help="target image or video")
    parser.add_argument("-o", "--output", help="output file or directory")
    parser.add_argument(
        "--disclosure",
        choices=[mode.value for mode in DisclosureMode],
        default=DisclosureMode.VISIBLE_AND_METADATA.value,
        help="output disclosure policy (default: visible+metadata)",
    )
    parser.add_argument(
        "--acknowledge-unlabeled-output",
        action="store_true",
        help="required acknowledgement when --disclosure=none",
    )
    parser.add_argument(
        "--keep-audio",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="keep target audio (default: enabled)",
    )
    parser.add_argument("--version", action="version", version=f"Portrait Relay {__version__}")
    return parser


def _validate_disclosure(arguments: Sequence[str]) -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--disclosure",
        choices=[mode.value for mode in DisclosureMode],
        default=DisclosureMode.VISIBLE_AND_METADATA.value,
    )
    parser.add_argument("--acknowledge-unlabeled-output", action="store_true")
    known, _ = parser.parse_known_args(arguments)
    if known.disclosure == DisclosureMode.NONE.value and not known.acknowledge_unlabeled_output:
        parser.error("--disclosure=none requires --acknowledge-unlabeled-output")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the lightweight help path or hand off to the legacy application."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if any(value in {"-h", "--help", "--version"} for value in arguments):
        build_parser().parse_args(arguments)
        return 0
    _validate_disclosure(arguments)
    if argv is not None:
        sys.argv = [sys.argv[0], *arguments]
    from portrait_relay.runtime import prepare_runtime

    prepare_runtime()
    from modules import platform_info

    platform_info.print_banner()
    from modules import core

    core.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reject local tool state, private material, and generated artifacts."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

BASELINE_TAG = "upstream-deep-live-cam-f7db376"
FORBIDDEN_PARTS = {".claude", ".codex", ".agents", ".chatgpt"}
FORBIDDEN_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "audit.json",
    "audit.jsonl",
    "session.json",
    "transcript.md",
}
FORBIDDEN_SUFFIXES = {".onnx", ".pth", ".ckpt", ".pem", ".key"}
TRAILER_PATTERN = re.compile(
    r"^Co-authored-by:.*(?:Claude|ChatGPT|Codex|Copilot|Sourcery)",
    re.IGNORECASE | re.MULTILINE,
)


def _git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], text=True).strip()


def changed_paths() -> set[Path]:
    """Return tracked and uncommitted paths changed after the baseline."""

    values: set[str] = set()
    for arguments in (
        ("diff", "--name-only", f"{BASELINE_TAG}..HEAD"),
        ("diff", "--name-only", "--cached"),
        ("diff", "--name-only"),
        ("ls-files", "--others", "--exclude-standard"),
    ):
        output = _git(*arguments)
        values.update(line for line in output.splitlines() if line)
    return {Path(value) for value in values}


def check_paths(paths: set[Path]) -> list[str]:
    """Return path policy violations."""

    errors: list[str] = []
    for path in sorted(paths):
        lowered_parts = {part.lower() for part in path.parts}
        if lowered_parts & FORBIDDEN_PARTS:
            errors.append(f"forbidden tool-state path: {path}")
        if path.name in FORBIDDEN_NAMES:
            errors.append(f"forbidden local metadata file: {path}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"forbidden binary or credential file: {path}")
        lowered_name = path.name.lower()
        if any(token in lowered_name for token in ("prompt-dump", "chat-export")):
            errors.append(f"forbidden conversation export: {path}")
    return errors


def check_new_commit_messages() -> list[str]:
    """Reject assistant co-author trailers introduced after the baseline."""

    messages = _git("log", "--format=%B%x00", f"{BASELINE_TAG}..HEAD")
    if TRAILER_PATTERN.search(messages):
        return ["new commit history contains a bot or assistant co-author trailer"]
    return []


def main() -> int:
    errors = [*check_paths(changed_paths()), *check_new_commit_messages()]
    if errors:
        for error in errors:
            print(f"repository hygiene: {error}", file=sys.stderr)
        return 1
    print("repository hygiene: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

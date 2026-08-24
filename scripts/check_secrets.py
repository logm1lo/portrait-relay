#!/usr/bin/env python3
"""Reject common credential formats in files changed after the import baseline."""

from __future__ import annotations

import re
import sys

from check_repository_hygiene import changed_paths

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{50,})\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "generic assigned secret": re.compile(
        r"(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)\s*[:=]\s*"
        r"['\"][A-Za-z0-9+/=_-]{20,}['\"]"
    ),
}


def main() -> int:
    errors: list[str] = []
    for path in sorted(changed_paths()):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for label, pattern in PATTERNS.items():
            if match := pattern.search(content):
                line = content.count("\n", 0, match.start()) + 1
                errors.append(f"{path}:{line}: possible {label}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("secret check: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

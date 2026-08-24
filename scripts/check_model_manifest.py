#!/usr/bin/env python3
"""Validate immutable model manifest invariants without downloading files."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from portrait_relay.models import MODEL_REVISION, MODEL_SPECS

SHA256 = re.compile(r"^[0-9a-f]{64}$")
REVISION = re.compile(r"^[0-9a-f]{40}$")


def main() -> int:
    errors: list[str] = []
    if not REVISION.fullmatch(MODEL_REVISION):
        errors.append("model repository revision is not a full Git commit")
    if not MODEL_SPECS:
        errors.append("model manifest is empty")
    for name, spec in MODEL_SPECS.items():
        if name != spec.name or name.startswith(("/", "..")) or "//" in name:
            errors.append(f"unsafe or inconsistent model name: {name}")
        if spec.size <= 0:
            errors.append(f"invalid size for {name}")
        if not SHA256.fullmatch(spec.sha256):
            errors.append(f"invalid SHA-256 for {name}")
        if spec.revision != MODEL_REVISION or not REVISION.fullmatch(spec.revision):
            errors.append(f"mutable model revision for {name}")
        if spec.source != "hacksider/deep-live-cam":
            errors.append(f"unreviewed model repository for {name}")
        parsed = urlparse(spec.url)
        if parsed.scheme != "https" or parsed.hostname != "huggingface.co":
            errors.append(f"unapproved model source for {name}")
        if spec.revision not in parsed.path:
            errors.append(f"mutable model source for {name}")
        if not spec.license_note.strip():
            errors.append(f"missing license note for {name}")
    if errors:
        for error in errors:
            print(f"model manifest: {error}")
        return 1
    print(f"model manifest: {len(MODEL_SPECS)} entries passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

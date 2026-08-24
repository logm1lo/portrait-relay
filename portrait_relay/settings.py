"""Versioned and atomic user settings persistence."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SETTINGS_VERSION = 1


def config_directory() -> Path:
    """Return the platform application configuration directory."""

    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "Portrait Relay"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Portrait Relay"
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "portrait-relay"


def settings_path() -> Path:
    """Return the current settings file path."""

    return config_directory() / "settings.json"


def load_settings(path: Path | None = None) -> dict[str, Any]:
    """Load validated settings, returning an empty mapping on corruption."""

    target = path or settings_path()
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict) or value.get("schema_version") != SETTINGS_VERSION:
        return {}
    settings = value.get("settings")
    return settings if isinstance(settings, dict) else {}


def save_settings(settings: Mapping[str, Any], path: Path | None = None) -> None:
    """Write settings atomically with owner-only permissions where supported."""

    target = path or settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": SETTINGS_VERSION, "settings": dict(settings)}
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)

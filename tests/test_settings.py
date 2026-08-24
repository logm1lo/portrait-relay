import json
import sys
from pathlib import Path

import pytest

from portrait_relay.settings import (
    SETTINGS_VERSION,
    config_directory,
    load_settings,
    save_settings,
    settings_path,
)


def test_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "settings.json"

    save_settings({"keep_audio": False, "processors": ["face_swapper"]}, path)

    assert load_settings(path) == {
        "keep_audio": False,
        "processors": ["face_swapper"],
    }
    assert not list(path.parent.glob("*.tmp"))


def test_corrupt_settings_return_empty_mapping(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text("not-json", encoding="utf-8")

    assert load_settings(path) == {}


def test_unknown_schema_returns_empty_mapping(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"schema_version": SETTINGS_VERSION + 1, "settings": {"x": 1}}),
        encoding="utf-8",
    )

    assert load_settings(path) == {}


@pytest.mark.parametrize(
    ("platform", "environment", "ending"),
    [
        ("win32", {"APPDATA": "/tmp/windows-config"}, ("windows-config", "Portrait Relay")),
        ("darwin", {}, ("Application Support", "Portrait Relay")),
        ("linux", {"XDG_CONFIG_HOME": "/tmp/linux-config"}, ("linux-config", "portrait-relay")),
    ],
)
def test_platform_config_directory(
    platform: str,
    environment: dict[str, str],
    ending: tuple[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", platform)
    for key in ("APPDATA", "XDG_CONFIG_HOME"):
        monkeypatch.delenv(key, raising=False)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)

    assert config_directory().parts[-2:] == ending
    assert settings_path().name == "settings.json"


def test_valid_envelope_with_non_mapping_settings_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"schema_version": SETTINGS_VERSION, "settings": []}), encoding="utf-8"
    )

    assert load_settings(path) == {}

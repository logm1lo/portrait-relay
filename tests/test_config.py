from pathlib import Path

import pytest

from portrait_relay.config import AppConfig, DisclosureMode


def test_app_config_defaults_to_visible_disclosure() -> None:
    config = AppConfig(source_path=Path("source.jpg"))

    assert config.disclosure_mode is DisclosureMode.VISIBLE_AND_METADATA
    assert config.keep_audio is True


def test_unlabeled_output_requires_acknowledgement() -> None:
    with pytest.raises(ValueError, match="requires acknowledge"):
        AppConfig(disclosure_mode=DisclosureMode.NONE)


def test_unlabeled_output_accepts_explicit_acknowledgement() -> None:
    config = AppConfig(
        disclosure_mode=DisclosureMode.NONE,
        acknowledge_unlabeled_output=True,
    )

    assert config.disclosure_mode.includes_metadata is False


def test_execution_threads_must_be_positive() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        AppConfig(execution_threads=0)


def test_config_copies_metadata_into_read_only_mapping() -> None:
    source = {"job": "one"}
    config = AppConfig(metadata=source)
    source["job"] = "two"

    assert config.metadata["job"] == "one"
    with pytest.raises(TypeError):
        config.metadata["job"] = "three"  # type: ignore[index]

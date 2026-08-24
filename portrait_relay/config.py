"""Typed runtime configuration for Portrait Relay."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType


class DisclosureMode(StrEnum):
    """Available output disclosure policies."""

    VISIBLE_AND_METADATA = "visible+metadata"
    METADATA = "metadata"
    NONE = "none"

    @property
    def includes_visible_label(self) -> bool:
        """Return whether processed frames need a visible label."""

        return self is DisclosureMode.VISIBLE_AND_METADATA

    @property
    def includes_metadata(self) -> bool:
        """Return whether saved output needs provenance metadata."""

        return self is not DisclosureMode.NONE


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Job-scoped application configuration.

    The legacy application still exposes module globals to old processors. New
    services accept this immutable value so state can be moved out of globals
    without another public API change.
    """

    source_path: Path | None = None
    target_path: Path | None = None
    output_path: Path | None = None
    frame_processors: tuple[str, ...] = ("face_swapper",)
    execution_providers: tuple[str, ...] = ("CPUExecutionProvider",)
    execution_threads: int = 1
    keep_fps: bool = False
    keep_audio: bool = True
    keep_frames: bool = False
    explicit_content_screen: bool = False
    disclosure_mode: DisclosureMode = DisclosureMode.VISIBLE_AND_METADATA
    acknowledge_unlabeled_output: bool = False
    model_directory: Path | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate combinations which would otherwise produce unsafe output."""

        if self.execution_threads < 1:
            raise ValueError("execution_threads must be at least 1")
        if self.disclosure_mode is DisclosureMode.NONE and not self.acknowledge_unlabeled_output:
            raise ValueError("disclosure mode 'none' requires acknowledge_unlabeled_output")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

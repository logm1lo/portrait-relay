"""Typed frame processor interface and legacy module adapter."""

from __future__ import annotations

import inspect
from functools import cache
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray

Frame = NDArray[np.uint8]


class Processor(Protocol):
    """Interface implemented by new frame processors."""

    name: str

    def preflight(self) -> None:
        """Validate dependencies before a processing job starts."""

    def process_frame(
        self, source_face: Any, frame: Frame, *, target_face: Any | None = None
    ) -> Frame:
        """Process one BGR frame."""

    def close(self) -> None:
        """Release processor-owned resources."""


@cache
def _accepts_target_face(process_frame: Any) -> bool:
    """Inspect a legacy processor signature once, outside its error path."""

    signature = inspect.signature(process_frame)
    return "target_face" in signature.parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )


def invoke_legacy_processor(
    process_frame: Any,
    source_face: Any,
    frame: Frame,
    *,
    target_face: Any | None,
) -> Frame:
    """Invoke a legacy processor without masking an internal TypeError."""

    if _accepts_target_face(process_frame):
        result = process_frame(source_face, frame, target_face=target_face)
    else:
        result = process_frame(source_face, frame)
    if not isinstance(result, np.ndarray):
        raise TypeError("frame processor returned a non-array result")
    return result

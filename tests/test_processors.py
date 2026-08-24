from typing import Any

import numpy as np
import pytest

from portrait_relay.processors import invoke_legacy_processor


def test_processor_with_target_face_receives_keyword() -> None:
    frame = np.zeros((2, 2, 3), dtype=np.uint8)

    def process(source: Any, value: np.ndarray, *, target_face: Any) -> np.ndarray:
        assert source == "source"
        assert target_face == "target"
        return value + 1

    result = invoke_legacy_processor(process, "source", frame, target_face="target")

    assert np.all(result == 1)


def test_legacy_processor_without_target_face_is_supported() -> None:
    frame = np.zeros((2, 2, 3), dtype=np.uint8)

    def process(_source: Any, value: np.ndarray) -> np.ndarray:
        return value + 2

    result = invoke_legacy_processor(process, None, frame, target_face="ignored")

    assert np.all(result == 2)


def test_internal_type_error_is_not_retried() -> None:
    calls = 0

    def process(_source: Any, value: np.ndarray, *, target_face: Any) -> np.ndarray:
        nonlocal calls
        calls += 1
        raise TypeError("processor bug")

    with pytest.raises(TypeError, match="processor bug"):
        invoke_legacy_processor(
            process,
            None,
            np.zeros((1, 1, 3), dtype=np.uint8),
            target_face=None,
        )

    assert calls == 1


def test_non_array_processor_result_is_rejected() -> None:
    def process(_source: Any, _value: np.ndarray) -> str:
        return "bad"

    with pytest.raises(TypeError, match="non-array"):
        invoke_legacy_processor(
            process,
            None,
            np.zeros((1, 1, 3), dtype=np.uint8),
            target_face=None,
        )

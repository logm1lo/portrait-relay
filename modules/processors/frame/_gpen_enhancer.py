"""Shared implementation for manually supplied GPEN enhancer weights.

Modified for Portrait Relay on 2026-08-25.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

import modules.globals
import modules.processors.frame.core
from modules import imread_unicode, imwrite_unicode
from modules.core import update_status
from modules.face_analyser import get_one_face
from modules.processors.frame._onnx_enhancer import (
    create_onnx_session,
    enhance_face_onnx,
    warmup_session,
)
from modules.typing import Face, Frame
from modules.utilities import is_image, is_video


@dataclass(slots=True)
class GpenEnhancer:
    """Legacy frame-processor facade backed by one configurable implementation."""

    name: str
    input_size: int
    model_file: str
    _session: Any | None = field(default=None, init=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)

    def _obtain_model(self):
        from modules.model_downloader import ensure_model

        return ensure_model(self.model_file)

    def pre_check(self) -> bool:
        if self._obtain_model() is not None:
            return True
        update_status(
            f"Could not obtain {self.model_file}. Place it in the models folder "
            "manually after verifying its source and checksum.",
            self.name,
        )
        return False

    def pre_start(self) -> bool:
        if is_image(modules.globals.target_path) or is_video(modules.globals.target_path):
            return True
        update_status("Select an image or video for target path.", self.name)
        return False

    def get_enhancer(self) -> Any:
        with self._lock:
            if self._session is None:
                model_path = self._obtain_model()
                if model_path is None:
                    raise FileNotFoundError(f"Model file not found: models/{self.model_file}")
                self._session = create_onnx_session(model_path)
                warmup_session(self._session)
        return self._session

    def enhance_face(self, temp_frame: Frame, face: Face) -> Frame:
        return enhance_face_onnx(temp_frame, face, self.get_enhancer(), self.input_size)

    def process_frame(
        self,
        source_face: Face | None,
        temp_frame: Frame,
        detected_faces: list[Face] | None = None,
    ) -> Frame:
        del source_face
        target_face = detected_faces[0] if detected_faces else get_one_face(temp_frame)
        if target_face is None:
            return temp_frame
        return self.enhance_face(temp_frame, target_face)

    def process_frame_v2(self, temp_frame: Frame) -> Frame:
        return self.process_frame(None, temp_frame)

    def process_frames(
        self,
        source_path: str | None,
        temp_frame_paths: list[str],
        progress: Any = None,
    ) -> None:
        del source_path
        for temp_frame_path in temp_frame_paths:
            temp_frame = imread_unicode(temp_frame_path)
            if temp_frame is not None:
                imwrite_unicode(temp_frame_path, self.process_frame(None, temp_frame))
            if progress:
                progress.update(1)

    def process_image(self, source_path: str | None, target_path: str, output_path: str) -> None:
        del source_path
        target_frame = imread_unicode(target_path)
        if target_frame is None:
            raise ValueError(f"failed to read target image: {target_path}")
        imwrite_unicode(output_path, self.process_frame(None, target_frame))

    def process_video(self, source_path: str | None, temp_frame_paths: list[str]) -> None:
        modules.processors.frame.core.process_video(
            source_path,
            temp_frame_paths,
            self.process_frames,
        )

"""Job-scoped temporary workspace management."""

from __future__ import annotations

import shutil
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class JobWorkspace:
    """A unique temporary directory owned by one processing job."""

    target: Path
    keep_frames: bool = False
    root: Path = field(init=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        parent = self.target.resolve().parent / ".portrait-relay-tmp"
        parent.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix=f"{self.target.stem}-", dir=parent))

    @property
    def output_path(self) -> Path:
        """Return the intermediate video path for this job."""

        return self.root / "temp.mp4"

    def close(self) -> None:
        """Remove only this job's directory unless frame retention is enabled."""

        if self._closed:
            return
        self._closed = True
        parent = self.root.parent
        if not self.keep_frames:
            shutil.rmtree(self.root, ignore_errors=True)
        try:
            parent.rmdir()
        except OSError:
            pass

    def __enter__(self) -> JobWorkspace:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


class WorkspaceRegistry:
    """Thread-safe compatibility registry for legacy path-based helpers."""

    def __init__(self) -> None:
        self._items: dict[Path, JobWorkspace] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _key(target: str | Path) -> Path:
        return Path(target).resolve()

    def get_or_create(self, target: str | Path) -> JobWorkspace:
        key = self._key(target)
        with self._lock:
            workspace = self._items.get(key)
            if workspace is None:
                workspace = JobWorkspace(key)
                self._items[key] = workspace
            return workspace

    def release(self, target: str | Path, *, keep_frames: bool = False) -> None:
        key = self._key(target)
        with self._lock:
            workspace = self._items.pop(key, None)
        if workspace is not None:
            workspace.keep_frames = keep_frames
            workspace.close()

"""Runtime preparation deferred until after lightweight CLI parsing."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def prepare_runtime() -> None:
    """Expose bundled tools and vendor runtime libraries to child imports."""

    project_root = Path(__file__).resolve().parent.parent
    os.environ["PATH"] = str(project_root) + os.pathsep + os.environ.get("PATH", "")

    if sys.platform == "win32":
        _prepare_windows(project_root)
    elif sys.platform.startswith("linux"):
        _prepare_linux(project_root)


def _prepare_windows(project_root: Path) -> None:
    candidate_roots = [
        Path(sys.prefix) / "Lib" / "site-packages",
        project_root / "venv" / "Lib" / "site-packages",
    ]
    for site_packages in candidate_roots:
        candidates = [site_packages / "torch" / "lib"]
        nvidia = site_packages / "nvidia"
        if nvidia.is_dir():
            candidates.extend(path / "bin" for path in nvidia.iterdir())
        for candidate in candidates:
            if not candidate.is_dir():
                continue
            os.environ["PATH"] = str(candidate) + os.pathsep + os.environ["PATH"]
            add_dll_directory = getattr(os, "add_dll_directory", None)
            if add_dll_directory is None:
                continue
            try:
                add_dll_directory(str(candidate))
            except OSError:
                continue


def _prepare_linux(project_root: Path) -> None:
    import ctypes

    python_directory = f"python{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        project_root / "venv" / "lib" / python_directory / "site-packages",
        Path(sys.prefix) / "lib" / python_directory / "site-packages",
    ]
    for site_packages in candidates:
        nvidia = site_packages / "nvidia"
        if not nvidia.is_dir():
            continue
        for package in nvidia.iterdir():
            library_directory = package / "lib"
            if not library_directory.is_dir():
                continue
            current = os.environ.get("LD_LIBRARY_PATH", "")
            entries = current.split(os.pathsep) if current else []
            if str(library_directory) not in entries:
                os.environ["LD_LIBRARY_PATH"] = os.pathsep.join([str(library_directory), *entries])
            for library in sorted(library_directory.glob("lib*.so*")):
                try:
                    ctypes.CDLL(str(library), mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    continue
        break

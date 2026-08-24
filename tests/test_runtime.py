import ctypes
import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from portrait_relay import runtime


def test_prepare_runtime_dispatches_for_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    windows = Mock()
    linux = Mock()
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(runtime, "_prepare_windows", windows)
    monkeypatch.setattr(runtime, "_prepare_linux", linux)

    runtime.prepare_runtime()

    windows.assert_called_once()
    linux.assert_not_called()


def test_prepare_runtime_dispatches_for_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    linux = Mock()
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(runtime, "_prepare_linux", linux)

    runtime.prepare_runtime()

    linux.assert_called_once()


def test_windows_runtime_adds_available_vendor_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    site_packages = tmp_path / "Lib" / "site-packages"
    vendor = site_packages / "nvidia" / "cudnn" / "bin"
    vendor.mkdir(parents=True)
    add_directory = Mock(side_effect=OSError("test failure"))
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(os, "add_dll_directory", add_directory, raising=False)

    runtime._prepare_windows(tmp_path / "project")

    add_directory.assert_called_once_with(str(vendor))
    assert str(vendor) in os.environ["PATH"]


def test_linux_runtime_loads_libraries_and_ignores_bad_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    site_packages = (
        tmp_path
        / "lib"
        / f"python{sys.version_info.major}.{sys.version_info.minor}"
        / "site-packages"
    )
    libraries = site_packages / "nvidia" / "cudnn" / "lib"
    libraries.mkdir(parents=True)
    first = libraries / "libfirst.so"
    second = libraries / "libsecond.so"
    first.touch()
    second.touch()
    loader = Mock(side_effect=[None, OSError("bad library")])
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr(ctypes, "CDLL", loader)
    monkeypatch.delenv("LD_LIBRARY_PATH", raising=False)

    runtime._prepare_linux(tmp_path / "project")

    assert loader.call_count == 2
    assert os.environ["LD_LIBRARY_PATH"].split(os.pathsep)[0] == str(libraries)

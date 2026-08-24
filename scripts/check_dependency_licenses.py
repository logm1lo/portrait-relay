#!/usr/bin/env python3
"""Verify that every declared direct dependency has a reviewed license entry."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

REVIEWED_LICENSES = {
    "albumentations": "MIT",
    "c2pa-python": "MIT OR Apache-2.0",
    "cv2-enumerate-cameras": "MIT",
    "cython": "Apache-2.0",
    "easydict": "LGPL-3.0-only",
    "insightface": "MIT (code only; model terms are separate)",
    "keras": "Apache-2.0",
    "matplotlib": "PSF-based",
    "numpy": "BSD-3-Clause",
    "onnx": "Apache-2.0",
    "onnxruntime": "MIT",
    "onnxruntime-directml": "MIT",
    "onnxruntime-gpu": "MIT",
    "onnxruntime-openvino": "MIT",
    "opencv-python": "Apache-2.0",
    "opennsfw2": "MIT",
    "pillow": "HPND",
    "protobuf": "BSD-3-Clause",
    "psutil": "BSD-3-Clause",
    "prettytable": "BSD-3-Clause",
    "pygrabber": "MIT",
    "pyside6": "LGPL-3.0-only OR GPL-3.0-only OR commercial",
    "requests": "Apache-2.0",
    "scikit-image": "BSD-3-Clause",
    "scikit-learn": "BSD-3-Clause",
    "scipy": "BSD-3-Clause",
    "tqdm": "MPL-2.0 AND MIT",
    "typing-extensions": "PSF-2.0",
}


def _name(requirement: str) -> str:
    return re.split(r"[<>=!~;\[]", requirement, maxsplit=1)[0].strip().lower()


def main() -> int:
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
    requirements = list(project.get("dependencies", []))
    for extra, values in project.get("optional-dependencies", {}).items():
        if extra != "test":
            requirements.extend(values)
    names = {_name(value) for value in requirements}
    missing = sorted(names - REVIEWED_LICENSES.keys())
    stale = sorted(REVIEWED_LICENSES.keys() - names)
    if missing:
        print("unreviewed direct dependency licenses: " + ", ".join(missing), file=sys.stderr)
        return 1
    if stale:
        print("stale dependency license entries: " + ", ".join(stale), file=sys.stderr)
        return 1
    print(f"dependency license check: {len(names)} direct packages reviewed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

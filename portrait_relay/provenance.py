"""Visible and machine-readable disclosure for processed media."""

from __future__ import annotations

import json
import mimetypes
import os
import stat
import subprocess
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from portrait_relay import __version__
from portrait_relay.config import DisclosureMode

DIGITAL_SOURCE_TYPE = (
    "http://cv.iptc.org/newscodes/digitalsourcetype/compositeWithTrainedAlgorithmicMedia"
)
VISIBLE_LABEL = "AI-manipulated"


@dataclass(frozen=True, slots=True)
class OutputProvenance:
    """Non-personal processing facts recorded with an output asset."""

    disclosure_mode: DisclosureMode
    processors: tuple[str, ...] = ()
    model_hashes: Mapping[str, str] | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible representation."""

        return {
            "application": "Portrait Relay",
            "application_version": __version__,
            "digital_source_type": DIGITAL_SOURCE_TYPE,
            "disclosure_mode": self.disclosure_mode.value,
            "processors": list(self.processors),
            "model_hashes": dict(self.model_hashes or {}),
        }


def draw_visible_label(frame: Any, label: str = VISIBLE_LABEL) -> Any:
    """Draw the disclosure label on a BGR image without changing dimensions."""

    import cv2

    height, width = frame.shape[:2]
    scale = max(0.45, min(width, height) / 900.0)
    thickness = max(1, round(scale * 2))
    padding = max(8, round(min(width, height) * 0.015))
    (text_width, text_height), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness
    )
    right = width - padding
    bottom = height - padding
    left = max(0, right - text_width - padding)
    top = max(0, bottom - text_height - baseline - padding)
    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 0), -1)
    cv2.putText(
        frame,
        label,
        (left + padding // 2, bottom - baseline - padding // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        (255, 255, 255),
        thickness,
        cv2.LINE_AA,
    )
    return frame


def apply_visible_disclosure_to_frames(paths: list[str]) -> None:
    """Add the default label to an extracted frame sequence in place."""

    import cv2

    for value in paths:
        path = Path(value)
        frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError(f"cannot read extracted frame: {path}")
        draw_visible_label(frame)
        if not cv2.imwrite(str(path), frame):
            raise OSError(f"cannot write disclosure label to frame: {path}")


def _xmp_packet(provenance: OutputProvenance) -> bytes:
    payload = json.dumps(provenance.as_dict(), sort_keys=True, separators=(",", ":"))
    escaped = (
        payload.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '  <rdf:Description rdf:about="" '
        'xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
        'xmlns:portraitRelay="https://github.com/logm1lo/portrait-relay/ns/1.0/" '
        f'Iptc4xmpExt:DigitalSourceType="{DIGITAL_SOURCE_TYPE}" '
        f'portraitRelay:Processing="{escaped}"/>\n'
        " </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        '<?xpacket end="w"?>'
    ).encode()


def apply_image_disclosure(path: Path, provenance: OutputProvenance) -> None:
    """Apply the configured visible label and XMP metadata to an image."""

    import cv2

    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"cannot read output image: {path}")
    if provenance.disclosure_mode.includes_visible_label:
        draw_visible_label(image)
        if not cv2.imwrite(str(path), image):
            raise OSError(f"cannot write disclosure label to {path}")
    if not provenance.disclosure_mode.includes_metadata:
        return

    from PIL import Image
    from PIL.PngImagePlugin import PngInfo

    suffix = path.suffix.lower()
    with Image.open(path) as opened:
        image_copy = opened.copy()
        exif = opened.info.get("exif")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=path.suffix, dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        if suffix == ".png":
            png_info = PngInfo()
            png_info.add_itxt("XML:com.adobe.xmp", _xmp_packet(provenance).decode())
            image_copy.save(temporary, pnginfo=png_info)
        elif suffix in {".jpg", ".jpeg", ".webp"}:
            save_options: dict[str, Any] = {"xmp": _xmp_packet(provenance)}
            if exif:
                save_options["exif"] = exif
            if suffix in {".jpg", ".jpeg"}:
                save_options.update(quality=95, optimize=True)
            image_copy.save(temporary, **save_options)
        else:
            return
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def apply_video_metadata(path: Path, provenance: OutputProvenance) -> None:
    """Remux a video with disclosure metadata without re-encoding streams."""

    if not provenance.disclosure_mode.includes_metadata:
        return
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.", suffix=path.suffix, dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    payload = json.dumps(provenance.as_dict(), sort_keys=True, separators=(",", ":"))
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(path),
        "-map",
        "0",
        "-c",
        "copy",
        "-metadata",
        f"digital_source_type={DIGITAL_SOURCE_TYPE}",
        "-metadata",
        f"comment={payload}",
        "-y",
        str(temporary),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _protected_private_key(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"C2PA private key not found: {path}")
    if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise PermissionError("C2PA private key must not be group- or world-readable")


def sign_c2pa_if_configured(path: Path, provenance: OutputProvenance) -> bool:
    """Sign an output when explicit C2PA certificate and key paths are set."""

    certificate_value = os.environ.get("PORTRAIT_RELAY_C2PA_CERT")
    key_value = os.environ.get("PORTRAIT_RELAY_C2PA_KEY")
    if not certificate_value and not key_value:
        return False
    if not certificate_value or not key_value:
        raise ValueError("both PORTRAIT_RELAY_C2PA_CERT and KEY are required")

    certificate_path = Path(certificate_value).expanduser()
    key_path = Path(key_value).expanduser()
    _protected_private_key(key_path)
    if not certificate_path.is_file():
        raise FileNotFoundError(f"C2PA certificate not found: {certificate_path}")

    try:
        from c2pa import Builder, C2paSignerInfo, C2paSigningAlg, Context, Signer
    except ImportError as error:
        raise RuntimeError("install the c2pa optional dependency to sign outputs") from error

    algorithms = {
        "es256": C2paSigningAlg.ES256,
        "ps256": C2paSigningAlg.PS256,
        "ed25519": C2paSigningAlg.ED25519,
    }
    selected = os.environ.get("PORTRAIT_RELAY_C2PA_ALGORITHM", "ps256").lower()
    if selected not in algorithms:
        raise ValueError(f"unsupported C2PA algorithm: {selected}")

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    manifest = {
        "claim_generator": f"Portrait Relay/{__version__}",
        "title": path.name,
        "format": mime_type,
        "assertions": [
            {
                "label": "c2pa.actions.v2",
                "data": {
                    "actions": [
                        {
                            "action": "c2pa.edited",
                            "digitalSourceType": DIGITAL_SOURCE_TYPE,
                        }
                    ]
                },
            }
        ],
    }
    signer_info = C2paSignerInfo(
        alg=algorithms[selected],
        sign_cert=certificate_path.read_bytes(),
        private_key=key_path.read_bytes(),
        ta_url=os.environ.get(
            "PORTRAIT_RELAY_C2PA_TIMESTAMP", "http://timestamp.digicert.com"
        ).encode(),
    )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.signed.", suffix=path.suffix, dir=path.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with Context() as context:
            with Signer.from_info(signer_info) as signer:
                with Builder(json.dumps(manifest), context) as builder:
                    with path.open("rb") as source, temporary.open("w+b") as destination:
                        builder.sign(signer, mime_type, source, destination)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def finalize_output(path: Path, provenance: OutputProvenance) -> bool:
    """Write output metadata and optionally attach signed Content Credentials."""

    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
        apply_image_disclosure(path, provenance)
    elif suffix in {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v"}:
        apply_video_metadata(path, provenance)
    return sign_c2pa_if_configured(path, provenance)

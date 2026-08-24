from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
from PIL import Image

from portrait_relay.config import DisclosureMode
from portrait_relay.provenance import (
    DIGITAL_SOURCE_TYPE,
    OutputProvenance,
    apply_image_disclosure,
    apply_video_metadata,
    apply_visible_disclosure_to_frames,
    draw_visible_label,
    finalize_output,
    sign_c2pa_if_configured,
)


def provenance(mode: DisclosureMode) -> OutputProvenance:
    return OutputProvenance(
        disclosure_mode=mode,
        processors=("face_swapper",),
        model_hashes={"model.onnx": "a" * 64},
    )


def test_visible_label_changes_pixels_without_changing_dimensions() -> None:
    frame = np.full((240, 320, 3), 127, dtype=np.uint8)

    result = draw_visible_label(frame.copy())

    assert result.shape == frame.shape
    assert np.any(result != frame)
    assert np.any(result[-60:, -180:] == 0)


def test_png_receives_visible_label_and_xmp(tmp_path: Path) -> None:
    path = tmp_path / "output.png"
    original = np.full((240, 320, 3), 127, dtype=np.uint8)
    assert cv2.imwrite(str(path), original)

    apply_image_disclosure(path, provenance(DisclosureMode.VISIBLE_AND_METADATA))

    changed = cv2.imread(str(path))
    assert changed is not None
    assert np.any(changed != original)
    with Image.open(path) as opened:
        xmp = opened.info["XML:com.adobe.xmp"]
    assert DIGITAL_SOURCE_TYPE in xmp
    assert "Portrait Relay" in xmp


def test_metadata_mode_keeps_pixels_and_writes_xmp(tmp_path: Path) -> None:
    path = tmp_path / "output.png"
    original = np.full((80, 100, 3), 90, dtype=np.uint8)
    assert cv2.imwrite(str(path), original)

    apply_image_disclosure(path, provenance(DisclosureMode.METADATA))

    changed = cv2.imread(str(path))
    assert np.array_equal(changed, original)
    with Image.open(path) as opened:
        assert DIGITAL_SOURCE_TYPE in opened.info["XML:com.adobe.xmp"]


def test_c2pa_partial_configuration_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "output.jpg"
    path.write_bytes(b"not-needed")
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_CERT", "/missing/cert.pem")
    monkeypatch.delenv("PORTRAIT_RELAY_C2PA_KEY", raising=False)

    with pytest.raises(ValueError, match="both"):
        sign_c2pa_if_configured(path, provenance(DisclosureMode.METADATA))


def test_visible_disclosure_updates_frame_sequence(tmp_path: Path) -> None:
    path = tmp_path / "0001.png"
    original = np.full((120, 180, 3), 100, dtype=np.uint8)
    assert cv2.imwrite(str(path), original)

    apply_visible_disclosure_to_frames([str(path)])

    assert np.any(cv2.imread(str(path)) != original)


def test_visible_disclosure_rejects_unreadable_frame(tmp_path: Path) -> None:
    path = tmp_path / "broken.png"
    path.write_bytes(b"broken")

    with pytest.raises(ValueError, match="cannot read"):
        apply_visible_disclosure_to_frames([str(path)])


def test_none_mode_does_not_modify_image(tmp_path: Path) -> None:
    path = tmp_path / "output.png"
    original = np.full((80, 100, 3), 90, dtype=np.uint8)
    assert cv2.imwrite(str(path), original)

    apply_image_disclosure(path, provenance(DisclosureMode.NONE))

    assert np.array_equal(cv2.imread(str(path)), original)


@pytest.mark.parametrize("suffix", [".jpg", ".webp"])
def test_supported_image_formats_receive_xmp(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"output{suffix}"
    Image.new("RGB", (60, 40), "gray").save(path)

    apply_image_disclosure(path, provenance(DisclosureMode.METADATA))

    with Image.open(path) as opened:
        assert DIGITAL_SOURCE_TYPE.encode() in opened.info["xmp"]


def test_video_metadata_remuxes_atomically(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "output.mp4"
    path.write_bytes(b"original")

    def fake_run(command: list[str], **_kwargs: object) -> None:
        Path(command[-1]).write_bytes(b"remuxed")
        assert f"digital_source_type={DIGITAL_SOURCE_TYPE}" in command
        assert not any("input_path" in item for item in command)

    monkeypatch.setattr("portrait_relay.provenance.subprocess.run", fake_run)

    apply_video_metadata(path, provenance(DisclosureMode.METADATA))

    assert path.read_bytes() == b"remuxed"
    assert not list(tmp_path.glob(".*.mp4"))


def test_video_none_mode_skips_ffmpeg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = Mock()
    monkeypatch.setattr("portrait_relay.provenance.subprocess.run", runner)

    apply_video_metadata(tmp_path / "output.mp4", provenance(DisclosureMode.NONE))

    runner.assert_not_called()


def test_c2pa_requires_protected_existing_material(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "output.jpg"
    path.write_bytes(b"image")
    cert = tmp_path / "cert.pem"
    cert.write_bytes(b"cert")
    key = tmp_path / "key.pem"
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_CERT", str(cert))
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_KEY", str(key))

    with pytest.raises(FileNotFoundError, match="private key"):
        sign_c2pa_if_configured(path, provenance(DisclosureMode.METADATA))

    key.write_bytes(b"key")
    key.chmod(0o644)
    with pytest.raises(PermissionError, match="must not be"):
        sign_c2pa_if_configured(path, provenance(DisclosureMode.METADATA))


def test_c2pa_signs_with_explicit_protected_material(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "output.jpg"
    path.write_bytes(b"image")
    cert = tmp_path / "cert.pem"
    cert.write_bytes(b"cert")
    key = tmp_path / "key.pem"
    key.write_bytes(b"key")
    key.chmod(0o600)
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_CERT", str(cert))
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_KEY", str(key))

    class ContextManager:
        def __enter__(self):
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    class FakeSigner(ContextManager):
        @classmethod
        def from_info(cls, _info: object):
            return cls()

    class FakeBuilder(ContextManager):
        def __init__(self, manifest: str, _context: object):
            assert DIGITAL_SOURCE_TYPE in manifest

        def sign(self, _signer: object, mime: str, source, destination) -> None:
            assert mime == "image/jpeg"
            destination.write(b"signed:" + source.read())

    c2pa = ModuleType("c2pa")
    c2pa.Builder = FakeBuilder
    c2pa.Context = ContextManager
    c2pa.Signer = FakeSigner
    c2pa.C2paSignerInfo = lambda **values: values
    c2pa.C2paSigningAlg = SimpleNamespace(ES256="es256", PS256="ps256", ED25519="ed25519")
    monkeypatch.setitem(__import__("sys").modules, "c2pa", c2pa)

    assert sign_c2pa_if_configured(path, provenance(DisclosureMode.METADATA)) is True
    assert path.read_bytes() == b"signed:image"


def test_c2pa_rejects_unknown_algorithm(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "output.jpg"
    path.write_bytes(b"image")
    cert = tmp_path / "cert.pem"
    cert.write_bytes(b"cert")
    key = tmp_path / "key.pem"
    key.write_bytes(b"key")
    key.chmod(0o600)
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_CERT", str(cert))
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_KEY", str(key))
    monkeypatch.setenv("PORTRAIT_RELAY_C2PA_ALGORITHM", "unknown")
    monkeypatch.setitem(
        __import__("sys").modules,
        "c2pa",
        SimpleNamespace(
            Builder=object,
            Context=object,
            Signer=object,
            C2paSignerInfo=object,
            C2paSigningAlg=SimpleNamespace(ES256="es256", PS256="ps256", ED25519="ed25519"),
        ),
    )

    with pytest.raises(ValueError, match="unsupported"):
        sign_c2pa_if_configured(path, provenance(DisclosureMode.METADATA))


def test_finalize_routes_media_and_skips_signing_without_configuration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    image = tmp_path / "output.png"
    video = tmp_path / "output.mp4"
    other = tmp_path / "output.txt"
    image_handler = Mock()
    video_handler = Mock()
    monkeypatch.setattr("portrait_relay.provenance.apply_image_disclosure", image_handler)
    monkeypatch.setattr("portrait_relay.provenance.apply_video_metadata", video_handler)

    assert finalize_output(image, provenance(DisclosureMode.METADATA)) is False
    assert finalize_output(video, provenance(DisclosureMode.METADATA)) is False
    assert finalize_output(other, provenance(DisclosureMode.METADATA)) is False
    image_handler.assert_called_once()
    video_handler.assert_called_once()

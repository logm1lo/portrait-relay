from __future__ import annotations

import hashlib
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from modules import model_downloader
from portrait_relay.models import ModelSpec


class FakeResponse:
    def __init__(
        self,
        data: bytes,
        *,
        url: str,
        content_length: int | str | None = None,
        status: int = 200,
        read_error: Exception | None = None,
    ):
        self._data = data
        self._read = False
        self._url = url
        self.status = status
        self._read_error = read_error
        self.headers = {
            "Content-Length": str(len(data) if content_length is None else content_length)
        }

    def geturl(self) -> str:
        return self._url

    def read(self, _size: int) -> bytes:
        if self._read_error is not None:
            raise self._read_error
        if self._read:
            return b""
        self._read = True
        return self._data

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: Any) -> None:
        return None


def make_spec(data: bytes, *, allow_download: bool = True) -> ModelSpec:
    return ModelSpec(
        "tiny.onnx",
        len(data),
        hashlib.sha256(data).hexdigest(),
        "test-only fixture",
        allow_download=allow_download,
    )


def test_download_verifies_and_atomically_installs_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"test-model"
    spec = make_spec(data)
    response = FakeResponse(data, url="https://huggingface.co/model/tiny.onnx")
    urlopen = Mock(return_value=response)
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", urlopen)
    target = tmp_path / "tiny.onnx"

    assert model_downloader._download(spec, target) is True

    assert target.read_bytes() == data
    assert not target.with_suffix(".onnx.part").exists()
    assert target.with_suffix(".onnx.verified").is_file()
    assert "context" not in urlopen.call_args.kwargs


def test_download_rejects_unapproved_redirect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"test-model"
    spec = make_spec(data)
    monkeypatch.setattr(
        model_downloader.urllib.request,
        "urlopen",
        Mock(return_value=FakeResponse(data, url="https://example.com/tiny.onnx")),
    )

    assert model_downloader._download(spec, tmp_path / "tiny.onnx") is False
    assert not (tmp_path / "tiny.onnx").exists()


def test_download_rejects_oversized_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = make_spec(b"four")
    response = FakeResponse(
        b"12345",
        url="https://huggingface.co/model/tiny.onnx",
        content_length=5,
    )
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(return_value=response))

    assert model_downloader._download(spec, tmp_path / "tiny.onnx") is False


def test_download_rejects_checksum_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = make_spec(b"good")
    response = FakeResponse(b"evil", url="https://huggingface.co/model/tiny.onnx")
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(return_value=response))

    assert model_downloader._download(spec, tmp_path / "tiny.onnx") is False
    assert not (tmp_path / "tiny.onnx.part").exists()


def test_manual_only_model_quarantines_unverified_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = make_spec(b"approved", allow_download=False)
    target = tmp_path / "tiny.onnx"
    target.write_bytes(b"modified")
    monkeypatch.setattr(model_downloader, "get_model_spec", lambda _name: spec)
    monkeypatch.setattr(model_downloader, "local_path", lambda _name, _dest=None: str(target))

    assert model_downloader.ensure_model("tiny.onnx") is None
    assert not target.exists()
    assert target.with_name("tiny.onnx.invalid").read_bytes() == b"modified"


def test_manifest_helpers_reject_unknown_and_normalize_paths(tmp_path: Path) -> None:
    assert model_downloader.resolve_url("inswapper_128.onnx").startswith("https://huggingface.co/")
    with pytest.raises(ValueError, match="approved manifest"):
        model_downloader.resolve_url("unknown.onnx")
    assert model_downloader.expected_size("unknown.onnx") is None
    assert model_downloader.local_path("folder\\model.onnx", str(tmp_path)) == str(
        tmp_path / "model.onnx"
    )
    assert model_downloader.local_path("folder/model.onnx").endswith("models/folder/model.onnx")


def test_present_file_uses_and_invalidates_verification_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"approved"
    spec = make_spec(data)
    target = tmp_path / "tiny.onnx"
    target.write_bytes(data)
    monkeypatch.setattr(model_downloader, "get_model_spec", lambda _name: spec)
    monkeypatch.setattr(model_downloader, "local_path", lambda _name, _dest=None: str(target))

    assert model_downloader.is_present("tiny.onnx") is True
    marker = target.with_suffix(".onnx.verified")
    assert marker.is_file()
    assert model_downloader.is_present("tiny.onnx") is True
    target.write_bytes(b"modified")
    assert model_downloader.is_present("tiny.onnx") is False


@pytest.mark.parametrize(
    "url",
    [
        "http://huggingface.co/model.onnx",
        "https://huggingface.co.example.org/model.onnx",
        "file:///tmp/model.onnx",
    ],
)
def test_response_url_policy_rejects_untrusted_sources(url: str) -> None:
    with pytest.raises(ValueError, match="unapproved"):
        model_downloader._validate_response_url(url)


def test_download_resumes_valid_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"complete-model"
    spec = make_spec(data)
    target = tmp_path / "tiny.onnx"
    partial = target.with_suffix(".onnx.part")
    partial.write_bytes(data[:4])
    response = FakeResponse(data[4:], url="https://huggingface.co/model/tiny.onnx", status=206)
    urlopen = Mock(return_value=response)
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", urlopen)

    assert model_downloader._download(spec, target) is True
    assert target.read_bytes() == data
    assert urlopen.call_args.args[0].headers["Range"] == "bytes=4-"


def test_server_ignoring_range_restarts_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"complete"
    spec = make_spec(data)
    target = tmp_path / "tiny.onnx"
    target.with_suffix(".onnx.part").write_bytes(b"old")
    response = FakeResponse(data, url="https://huggingface.co/model/tiny.onnx", status=200)
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(return_value=response))

    assert model_downloader._download(spec, target) is True
    assert target.read_bytes() == data


def test_partial_larger_than_manifest_is_discarded_before_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = b"valid"
    spec = make_spec(data)
    target = tmp_path / "tiny.onnx"
    target.with_suffix(".onnx.part").write_bytes(b"far-too-large")
    response = FakeResponse(data, url="https://huggingface.co/model/tiny.onnx")
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(return_value=response))

    assert model_downloader._download(spec, target) is True
    assert target.read_bytes() == data


def test_stream_larger_than_manifest_is_rejected_without_length_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = make_spec(b"four")
    response = FakeResponse(
        b"12345",
        url="https://huggingface.co/model/tiny.onnx",
        content_length=0,
    )
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(return_value=response))

    assert model_downloader._download(spec, tmp_path / "tiny.onnx") is False


def test_network_and_stream_failures_discard_partial_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = make_spec(b"approved")
    target = tmp_path / "tiny.onnx"
    monkeypatch.setattr(
        model_downloader.urllib.request,
        "urlopen",
        Mock(side_effect=urllib.error.URLError("TLS failure")),
    )
    assert model_downloader._download(spec, target) is False

    response = FakeResponse(
        b"",
        url="https://huggingface.co/model/tiny.onnx",
        read_error=OSError("truncated"),
    )
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(return_value=response))
    assert model_downloader._download(spec, target) is False
    assert not target.with_suffix(".onnx.part").exists()


def test_invalid_content_length_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = make_spec(b"approved")
    response = FakeResponse(
        b"approved",
        url="https://huggingface.co/model/tiny.onnx",
        content_length="invalid",
    )
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(return_value=response))

    assert model_downloader._download(spec, tmp_path / "tiny.onnx") is False


def test_http_error_is_reported_without_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = make_spec(b"approved")
    error = urllib.error.HTTPError(spec.url, 500, "failed", {}, None)
    monkeypatch.setattr(model_downloader.urllib.request, "urlopen", Mock(side_effect=error))

    assert model_downloader._download(spec, tmp_path / "tiny.onnx") is False


def test_ensure_model_handles_unknown_valid_and_downloaded_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "tiny.onnx"
    spec = make_spec(b"approved")
    monkeypatch.setattr(model_downloader, "local_path", lambda _name, _dest=None: str(target))
    monkeypatch.setattr(
        model_downloader, "get_model_spec", lambda name: None if name == "bad" else spec
    )

    assert model_downloader.ensure_model("bad", quiet=True) is None
    target.write_bytes(b"approved")
    assert model_downloader.ensure_model("tiny.onnx") == str(target)
    target.unlink()
    monkeypatch.setattr(
        model_downloader, "_download", lambda _spec, path: path.write_bytes(b"x") > 0
    )
    assert model_downloader.ensure_model("tiny.onnx") == str(target)


def test_ensure_any_prefers_present_then_downloads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model_downloader, "is_present", lambda name: name == "second")
    monkeypatch.setattr(model_downloader, "local_path", lambda name, _dest=None: f"/models/{name}")
    assert model_downloader.ensure_any(["first", "second"]) == "/models/second"

    monkeypatch.setattr(model_downloader, "is_present", lambda _name: False)
    monkeypatch.setattr(
        model_downloader, "ensure_model", lambda name: "/models/last" if name == "last" else None
    )
    assert model_downloader.ensure_any(["first", "last"]) == "/models/last"
    assert model_downloader.ensure_any(["first"]) is None


def test_insightface_pack_rejects_unknown_and_installs_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert model_downloader.ensure_insightface_pack("unknown") is False
    monkeypatch.setattr(model_downloader, "is_present", lambda _name, _dest=None: False)
    monkeypatch.setattr(model_downloader, "ensure_model", lambda _name, quiet, dest_dir: dest_dir)

    assert model_downloader.ensure_insightface_pack("buffalo_l") is True

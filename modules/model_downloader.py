"""Verified model downloader for Portrait Relay.

Modified from Deep-Live-Cam on 2026-08-25.
"""

from __future__ import annotations

import hashlib
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterable
from pathlib import Path

from tqdm import tqdm

from modules.paths import MODELS_DIR
from portrait_relay.models import MODEL_SPECS, ModelSpec, get_model_spec

_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()
CHUNK_SIZE = 1024 * 256
ALLOWED_DOWNLOAD_HOST_SUFFIXES = ("huggingface.co", "hf.co", "xethub.hf.co")


def _lock_for(key: str) -> threading.Lock:
    with _LOCKS_GUARD:
        if key not in _LOCKS:
            _LOCKS[key] = threading.Lock()
        return _LOCKS[key]


def resolve_url(name: str) -> str:
    """Return the immutable source URL for an approved model."""

    spec = get_model_spec(name)
    if spec is None:
        raise ValueError(f"model is not present in the approved manifest: {name}")
    return spec.url


def local_path(name: str, dest_dir: str | None = None) -> str:
    """Return the local destination for a normalized manifest name."""

    normalized = name.replace("\\", "/")
    if dest_dir is not None:
        return str(Path(dest_dir) / Path(normalized).name)
    return str(Path(MODELS_DIR).joinpath(*normalized.split("/")))


def expected_size(name: str) -> int | None:
    """Return the exact manifest size for a model."""

    spec = get_model_spec(name)
    return spec.size if spec else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verification_marker(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".verified")


def _marker_value(path: Path, spec: ModelSpec) -> str:
    stat_result = path.stat()
    return f"{spec.sha256} {stat_result.st_size} {stat_result.st_mtime_ns}\n"


def _verify_file(path: Path, spec: ModelSpec) -> bool:
    if not path.is_file() or path.stat().st_size != spec.size:
        return False
    marker = _verification_marker(path)
    try:
        if marker.read_text(encoding="ascii") == _marker_value(path, spec):
            return True
    except (FileNotFoundError, OSError, UnicodeError):
        pass
    if _sha256(path) != spec.sha256:
        return False
    try:
        marker.write_text(_marker_value(path, spec), encoding="ascii")
        os.chmod(marker, 0o600)
    except OSError:
        pass
    return True


def is_present(name: str, dest_dir: str | None = None) -> bool:
    """Return whether an approved model exists and matches its SHA-256."""

    spec = get_model_spec(name)
    return bool(spec and _verify_file(Path(local_path(name, dest_dir)), spec))


def _validate_response_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not any(
        host == suffix or host.endswith(f".{suffix}") for suffix in ALLOWED_DOWNLOAD_HOST_SUFFIXES
    ):
        raise ValueError(f"model download redirected to an unapproved URL: {url}")


def _discard_partial(partial: Path) -> None:
    partial.unlink(missing_ok=True)


def _download(spec: ModelSpec, target: Path) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    resume_from = partial.stat().st_size if partial.is_file() else 0
    if resume_from > spec.size:
        _discard_partial(partial)
        resume_from = 0

    headers = {"User-Agent": "Portrait-Relay/0.1.0"}
    if resume_from:
        headers["Range"] = f"bytes={resume_from}-"

    try:
        request = urllib.request.Request(spec.url, headers=headers)
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as error:
        if resume_from and error.code in (416, 501):
            _discard_partial(partial)
            return _download(spec, target)
        print(f"[PR.MODELS] Failed to download {spec.name}: HTTP {error.code}")
        return False
    except (urllib.error.URLError, OSError, ValueError) as error:
        print(f"[PR.MODELS] Failed to download {spec.name}: {error}")
        return False

    with response:
        try:
            _validate_response_url(response.geturl())
        except ValueError as error:
            print(f"[PR.MODELS] Failed to download {spec.name}: {error}")
            return False
        if resume_from and getattr(response, "status", 200) != 206:
            resume_from = 0
        try:
            content_length = int(response.headers.get("Content-Length", 0) or 0)
        except (TypeError, ValueError):
            print(f"[PR.MODELS] Invalid Content-Length for {spec.name}")
            _discard_partial(partial)
            return False
        if content_length and resume_from + content_length > spec.size:
            print(f"[PR.MODELS] Server response for {spec.name} exceeds manifest size")
            _discard_partial(partial)
            return False
        mode = "ab" if resume_from else "wb"
        try:
            with partial.open(mode) as handle:
                with tqdm(
                    total=spec.size,
                    initial=resume_from,
                    desc=f"Downloading {Path(spec.name).name}",
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as progress:
                    downloaded = resume_from
                    while buffer := response.read(CHUNK_SIZE):
                        downloaded += len(buffer)
                        if downloaded > spec.size:
                            raise ValueError("download exceeded the manifest size")
                        handle.write(buffer)
                        progress.update(len(buffer))
                    handle.flush()
                    os.fsync(handle.fileno())
        except (urllib.error.URLError, OSError, ValueError) as error:
            print(f"[PR.MODELS] Download of {spec.name} interrupted: {error}")
            _discard_partial(partial)
            return False

    if not _verify_file(partial, spec):
        print(f"[PR.MODELS] SHA-256 or size mismatch for {spec.name}; discarding")
        _discard_partial(partial)
        return False
    try:
        os.replace(partial, target)
        _verification_marker(partial).unlink(missing_ok=True)
        _verification_marker(target).write_text(_marker_value(target, spec), encoding="ascii")
    except OSError as error:
        print(f"[PR.MODELS] Could not finalize {spec.name}: {error}")
        return False
    return True


def ensure_model(name: str, quiet: bool = False, dest_dir: str | None = None) -> str | None:
    """Return a verified model path, downloading only when policy permits."""

    normalized = name.replace("\\", "/")
    spec = get_model_spec(normalized)
    if spec is None:
        if not quiet:
            print(f"[PR.MODELS] Refusing unknown model: {normalized}")
        return None
    target = Path(local_path(normalized, dest_dir))
    with _lock_for(str(target)):
        if _verify_file(target, spec):
            return str(target)
        if target.exists():
            quarantine = target.with_name(target.name + ".invalid")
            try:
                os.replace(target, quarantine)
                print(f"[PR.MODELS] Quarantined unverified model as {quarantine.name}")
            except OSError as error:
                print(f"[PR.MODELS] Cannot quarantine unverified model: {error}")
                return None
        if not spec.allow_download:
            if not quiet:
                print(
                    f"[PR.MODELS] Automatic download is disabled for {normalized}. "
                    "Provide a verified file manually."
                )
            return None
        if not quiet:
            print(f"[PR.MODELS] Downloading verified model {normalized}")
        if _download(spec, target):
            return str(target)
    return None


def ensure_any(names: Iterable[str]) -> str | None:
    """Return the first verified model from an ordered preference list."""

    for name in names:
        if is_present(name):
            return local_path(name)
    for name in names:
        path = ensure_model(name)
        if path is not None:
            return path
    return None


def ensure_insightface_pack(name: str = "buffalo_l") -> bool:
    """Install one approved InsightFace pack into its standard directory."""

    members = [key for key in MODEL_SPECS if key.startswith(f"{name}/")]
    if not members:
        return False
    destination = str(Path.home() / ".insightface" / "models" / name)
    if all(is_present(member, destination) for member in members):
        return True
    print(f"[PR.MODELS] Verified InsightFace pack '{name}' is missing")
    ok = all(
        ensure_model(member, quiet=True, dest_dir=destination) is not None for member in members
    )
    if not ok:
        print(f"[PR.MODELS] Could not install complete pack '{name}'")
    return ok

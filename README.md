# Portrait Relay

Portrait Relay is a local desktop application for noncommercial face-swap research. It can process images, videos, and live camera frames with ONNX models. Outputs are visibly labeled and receive machine-readable disclosure metadata by default.

This project is derived from [Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam) at commit `f7db37679a85f6f9ca33e93652b3b03d1dd66ac5`. It is independently maintained and is not affiliated with deeplivecam.net.

## Responsible use

Use Portrait Relay only with the knowledge and consent of the people represented in the source and target media. Do not use it for impersonation, fraud, harassment, non-consensual intimate imagery, or deceptive publication.

The application cannot determine whether consent exists. Its optional explicit-content screen is a limited classifier, not a consent or safety system.

The default disclosure mode adds an `AI-manipulated` label and metadata. Removing disclosure requires an explicit acknowledgement. Metadata can be stripped by other software and is not tamper-resistant unless C2PA signing is configured.

## License and model terms

The application source is licensed under AGPL-3.0. Model files have separate terms.

InsightFace code is MIT licensed. Models provided by InsightFace, including the inswapper and buffalo model families used here, are limited to noncommercial research unless you obtain separate authorization. See [MODEL_LICENSES.md](MODEL_LICENSES.md) before downloading or using any model.

No model file is stored in this repository. The downloader accepts only files in the immutable model manifest and verifies their exact size and SHA-256 digest. GPEN downloads are disabled until their provenance and redistribution terms are resolved.

## Requirements

- Python 3.11 through 3.14
- FFmpeg and FFprobe on `PATH`
- A virtual environment
- One supported ONNX Runtime profile

Python 3.12 is the primary development environment. CI also checks Python 3.11, 3.13, and 3.14.

## Installation

Clone the standalone repository and create a virtual environment:

```bash
git clone https://github.com/logm1lo/portrait-relay.git
cd portrait-relay
python -m venv .venv
```

Activate the environment, then install the desktop application with exactly one runtime profile.

CPU:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[desktop,cpu]"
```

NVIDIA CUDA 12.8 with cuDNN 9:

```bash
python -m pip install -e ".[desktop,cuda12]"
```

NVIDIA CUDA 13 with cuDNN 9:

```bash
python -m pip install -e ".[desktop,cuda13]"
```

Other supported profiles are `coreml`, `directml`, and `openvino`. Do not combine runtime profiles. ONNX Runtime 1.26.x is used for CUDA 12.8; 1.28.x is used for CUDA 13.

## Running

Start the desktop interface:

```bash
portrait-relay
```

The compatibility launcher remains available for the 0.1 release:

```bash
python run.py
```

Process a file from the command line:

```bash
portrait-relay --source source.jpg --target target.mp4 --output output.mp4
```

Keep disclosure enabled unless a controlled research workflow requires otherwise:

```bash
portrait-relay --source source.jpg --target target.jpg --output output.jpg \
  --disclosure metadata
```

Completely unlabeled output requires explicit acknowledgement:

```bash
portrait-relay --source source.jpg --target target.jpg --output output.jpg \
  --disclosure none --acknowledge-unlabeled-output
```

Use `--no-keep-audio` to omit the target audio track.

## Model storage

Approved models are downloaded over verified TLS connections from an immutable repository revision. Each file is written to a partial file, checked against the manifest, and atomically moved into place.

Models are stored under `models/` or the standard InsightFace model directory. Both locations are excluded from Git. A file that has the expected name but fails verification is quarantined with an `.invalid` suffix.

GPEN weights are manual-only. Supplying a file does not grant a license to use or redistribute it.

## Output disclosure and C2PA

The modes are:

- `visible+metadata`: visible label and metadata, enabled by default
- `metadata`: metadata only
- `none`: no disclosure, requiring explicit acknowledgement

For images and videos, metadata uses the IPTC Digital Source Type `compositeWithTrainedAlgorithmicMedia`. When the optional C2PA dependency and trusted signing credentials are configured, Portrait Relay also signs the final asset.

Set these variables outside the repository:

```bash
export PORTRAIT_RELAY_C2PA_CERT=/secure/path/certificate-chain.pem
export PORTRAIT_RELAY_C2PA_KEY=/secure/path/private-key.pem
export PORTRAIT_RELAY_C2PA_ALGORITHM=ps256
```

On POSIX systems, the private key must not be readable by group or other users. For production signing, use a managed key service or hardware-backed key rather than a file-based key.

## Development

Install the locked development environment:

```bash
uv sync --frozen --extra test
```

Run the local checks:

```bash
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run python scripts/check_repository_hygiene.py
uv run python scripts/check_secrets.py
uv run python scripts/check_dependency_licenses.py
uv run python scripts/check_model_manifest.py
uv build
```

GitHub Dependabot vulnerability alerts and security updates are enabled for the public repository.

The local audit, assistant transcripts, prompts, model files, and tool state must never be committed. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Known limitations

- This is an alpha release and does not guarantee identity fidelity or stable real-time performance on every accelerator.
- The explicit-content screen has false positives and false negatives.
- Unsigned metadata can be removed or changed.
- C2PA trust depends on the certificate and key management used by the operator.
- The project does not provide legal advice or model licensing.

Security reports should follow [SECURITY.md](SECURITY.md). Architecture decisions are recorded under `docs/adr/`.

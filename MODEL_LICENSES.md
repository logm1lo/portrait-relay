# Model licenses and provenance

Code and model files are licensed separately. The AGPL-3.0 license for this repository does not grant rights to third-party model weights.

## InsightFace and inswapper

InsightFace's Python code is MIT licensed. Its supplied pretrained models are restricted to noncommercial research unless separate permission is obtained.

InsightFace currently directs users of inswapper models to `contact@insightface.ai` for licensing and support. It directs users of open recognition packs such as `buffalo_l` to `recognition-oss-pack@insightface.ai` for licensing.

Sources:

- https://github.com/deepinsight/insightface
- https://github.com/deepinsight/insightface/tree/master/python-package

Portrait Relay pins files from the `hacksider/deep-live-cam` model repository to revision `581e70b61240b7928404c17900437f47cfe94133`. The repository's blanket license metadata is not treated as authority to relicense third-party weights.

## GFPGAN

GFPGAN source code is available under Apache-2.0, with additional third-party component notices in its upstream repository. Model weights may carry separate terms.

Source: https://github.com/TencentARC/GFPGAN

The `gfpgan-1024.onnx` entry remains checksum-pinned. Redistribution permission must be reviewed again before attaching it to a binary release.

## GPEN

The provenance and redistribution terms for the GPEN ONNX conversions used by the inherited project have not been established to a release-quality standard. Automatic download is disabled.

Users may place a GPEN file manually only after independently establishing their right to use it and confirming that its SHA-256 matches the manifest. Portrait Relay does not redistribute these files.

## Manifest policy

Every downloadable entry records:

- An immutable repository revision
- Exact byte size
- SHA-256 digest
- A short license note
- Whether automatic download is allowed

Unknown names, mutable download URLs, checksum mismatches, oversized responses, and unapproved redirect hosts are rejected.

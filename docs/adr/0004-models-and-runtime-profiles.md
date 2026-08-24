# ADR-0004: Use immutable model manifests and runtime profiles

## Status

Accepted on 2026-08-25.

## Context

The inherited downloader used mutable URLs, size-only checks, and disabled TLS verification on macOS. The dependency list installed conflicting OpenCV packages and did not express the CUDA and cuDNN compatibility matrix.

## Decision

Allow automatic downloads only through `ModelSpec` entries containing an immutable revision, exact size, SHA-256, license note, and policy flag. Use one OpenCV desktop package and one mutually exclusive ONNX Runtime profile per environment.

Keep InsightFace 0.7.3 for the first hardening release. InsightFace 1.0.1 adds unconditional dependencies on `onnxruntime` and `opencv-python`, which prevents clean mutually exclusive GPU runtime profiles. Revisit the upgrade when upstream packaging allows the runtime backend to remain operator-selected.

## Consequences

Existing unknown or modified weights no longer load silently. The first verification of a large file has a hashing cost, after which a local marker avoids repeated hashing unless size or modification time changes. GPEN remains manual-only.

## Alternatives considered

- Trusting a model repository's blanket license field was rejected because it cannot relicense unrelated third-party weights.
- Installing CPU and GPU ONNX Runtime wheels together was rejected because both expose the same Python module namespace.

# Architecture

Portrait Relay remains a local desktop monolith. The first release introduces typed boundaries around the inherited modules instead of attempting a full rewrite.

## Runtime flow

```text
CLI or Qt UI
    |
    v
job configuration
    |
    v
media pipeline -> frame processor adapter -> ONNX processors
    |                                      |
    v                                      v
output disclosure                    verified models
    |
    v
image or video output -> optional C2PA signing
```

The `portrait_relay` package owns new public interfaces, policy, provenance, settings, and the lightweight CLI. The inherited `modules` package remains available behind adapters while processors are migrated in small, testable slices.

## Boundaries

- `AppConfig` is immutable and represents one job. Legacy globals are populated at the compatibility boundary only.
- `Processor` is the target frame processor protocol. Legacy functions are inspected once and invoked without exception-based signature guessing.
- `ModelSpec` is the only authority for automatic model downloads.
- `OutputProvenance` contains non-personal processing facts and is shared by image, video, and live output.
- Settings are versioned and written atomically outside the working directory.

## Non-functional requirements

- No output disclosure regression in default mode.
- No automatically downloaded model without an immutable source and SHA-256.
- No more than 10 percent median throughput regression for a supported profile.
- No more than 15 percent peak-memory regression for a supported profile.
- A failed job cleans only its own temporary workspace.
- CLI help and version output do not import media, Qt, or ML libraries.
- New public interfaces are fully typed and covered by behavior-focused tests.

## Failure controls

- The old fork remains available until the new repository and CI are verified.
- Model checksum failure quarantines the file and prevents inference.
- C2PA signing is opt-in and fails closed when partially configured.
- Unsigned metadata is described honestly as removable.
- Refactoring proceeds behind characterization tests, not as an all-at-once rewrite.

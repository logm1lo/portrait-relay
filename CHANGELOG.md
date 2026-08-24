# Changelog

All notable changes to Portrait Relay are recorded here.

## 0.1.0 - Unreleased

### Added

- Independent Portrait Relay package and command-line entry point
- Default visible and machine-readable output disclosure
- Optional C2PA signing with externally managed credentials
- Immutable model manifest with size and SHA-256 verification
- Atomic, platform-specific settings storage
- Repository hygiene and model-manifest checks
- Multi-version and multi-platform CI definitions

### Changed

- Rebranded the application and removed upstream commercial links
- Preserved the Deep-Live-Cam baseline and contributor history
- Added explicit CPU, CUDA 12, CUDA 13, CoreML, DirectML, and OpenVINO profiles
- Made `--keep-audio` reversible with `--no-keep-audio`
- Replaced processor TypeError fallback with signature-aware adaptation
- Scoped temporary frame directories to individual jobs

### Security

- Restored normal TLS certificate verification
- Rejected mutable, unknown, oversized, or checksum-mismatched model downloads
- Disabled automatic GPEN downloads pending provenance review

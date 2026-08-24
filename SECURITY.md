# Security policy

## Supported version

Security fixes are provided for the current `0.1.x` development line.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature for `logm1lo/portrait-relay`. Do not open a public issue for an unpatched vulnerability and do not include private media, faces, model files, credentials, or signing keys in a report.

Include the affected version, operating system, execution provider, reproduction steps, and the smallest non-sensitive test case possible.

## Security boundaries

Portrait Relay processes local media and untrusted binary model files. Only manifest-approved model files are downloaded automatically. ONNX parsing still occurs in native dependencies, so operators should run the application as an unprivileged user and keep dependencies current.

Output metadata is not tamper-resistant unless valid C2PA signing is configured. File-based C2PA private keys must be protected with owner-only permissions and must never be stored in this repository.

The application does not upload source media, target media, biometric embeddings, or output files. Optional model download requests disclose the usual network metadata to the model host.

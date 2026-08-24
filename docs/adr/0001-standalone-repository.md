# ADR-0001: Preserve history in a standalone repository

## Status

Accepted on 2026-08-25.

## Context

The project needs an independent identity without losing upstream authorship, license provenance, or the ability to audit inherited behavior.

## Decision

Create `logm1lo/portrait-relay` as a new, non-fork GitHub repository. Push the existing `main` history and the baseline tag through an explicit ref allowlist. Retain the original project as the `upstream` remote. Archive the old fork only after the new repository passes its release gates.

## Consequences

The repository keeps inherited commit messages and contributor trailers, including bot trailers. It does not inherit GitHub issues, pull requests, or repository settings. The migration requires explicit verification before the old fork is archived.

## Alternatives considered

- Rewriting history was rejected because it would falsify provenance.
- Asking GitHub Support to detach the existing fork was rejected because the new product has a new name and because deletion or network changes add avoidable risk.

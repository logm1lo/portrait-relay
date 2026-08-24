# ADR-0002: Introduce typed boundaries before package migration

## Status

Accepted on 2026-08-25.

## Context

The inherited application contains large UI and processor modules, mutable globals, and dynamically loaded processor functions. A direct rewrite would combine behavioral changes with structural changes and make regressions difficult to isolate.

## Decision

Add the `portrait_relay` package for stable policy and service interfaces. Keep the inherited `modules` package behind adapters during the 0.1 release. Move behavior in small slices after characterization tests exist.

## Consequences

Two package namespaces coexist temporarily. This is less visually clean than an immediate move, but it preserves compatibility and provides reviewable migration points. The compatibility launcher will be removed after one release cycle.

## Alternatives considered

- A single mechanical package rename was rejected because it would create a large, low-signal diff.
- Continuing with only globals was rejected because concurrency and testing remain unsafe.

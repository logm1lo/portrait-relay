# ADR-0003: Disclose manipulated output by default

## Status

Accepted on 2026-08-25.

## Context

Face-swapped media is easy to misrepresent after leaving the application. Visible labels are robust to ordinary metadata stripping, while metadata helps automated inspection and provenance tooling.

## Decision

Default to `visible+metadata`. Apply the text `AI-manipulated` to processed frames and write the IPTC Digital Source Type `compositeWithTrainedAlgorithmicMedia` to supported outputs. Allow metadata-only and fully unlabeled modes, but require explicit acknowledgement for the latter. Support C2PA signing only with operator-supplied trusted credentials.

## Consequences

The default modifies pixels and may not suit every controlled experiment. Users can choose metadata-only mode. Unsigned metadata remains removable and is never described as proof of authenticity.

## Alternatives considered

- Metadata-only by default was rejected because common media workflows strip metadata.
- Mandatory C2PA signing was rejected because the project cannot safely ship or provision a trusted signing identity.

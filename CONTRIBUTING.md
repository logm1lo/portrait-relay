# Contributing

Contributions should be small enough to review and should preserve the noncommercial research scope, disclosure defaults, and model integrity controls.

## Set up

```bash
uv sync --frozen --extra test
uv run pytest
```

Install a desktop runtime separately when testing the full application, for example:

```bash
uv sync --frozen --extra desktop --extra cpu --extra test
```

Runtime profiles are mutually exclusive.

## Before opening a pull request

Run:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest --cov=portrait_relay --cov=modules
uv run python scripts/check_repository_hygiene.py
uv run python scripts/check_model_manifest.py
uv build
```

Add behavior-focused tests for success and failure paths. Avoid tests that only assert mock calls.

## Repository hygiene

Do not commit:

- Model weights, generated media, or private test media
- Signing certificates or keys
- `.claude`, `.codex`, `.agents`, prompts, transcripts, or assistant session exports
- Local audits, terminal captures, coverage HTML, caches, or editor state
- Bot or assistant co-author trailers in new commits

The imported upstream history is preserved as received. Do not rewrite inherited authorship or remove existing contributor trailers.

Use plain, descriptive commit messages. Do not combine formatting, dependency changes, architecture changes, and behavioral changes in one large commit.

## Modification notices

Substantially changed inherited files should identify the project and modification date in a short module comment. Update `CHANGELOG.md` for user-visible changes.

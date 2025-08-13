# Repository Guidelines

## Project Structure & Module Organization
- `src/claude_codex_bridge/`: Core package (`__main__.py`, `bridge_server.py`, `engine.py`, `cache.py`).
- `tests/`: Unit tests (`test_engine.py`, `test_cache.py`).
- `.github/workflows/ci.yml`: CI for style, type-checking, security, and tests.
- `pyproject.toml`: Packaging, dependencies, and scripts. `Makefile`: minimal build targets.
- `docs/`: Additional reference docs.

## Build, Test, and Development Commands
- Setup: `uv sync --group dev` (installs dev deps).
- Build: `make build` or `uv build` (creates wheel/sdist in `dist/`).
- Run locally: `uv run python -m claude_codex_bridge` or `claude-codex-bridge`.
- Test: `uv run python -m pytest tests/ -v`.
- Coverage: `uv run python -m pytest tests/ --cov=src --cov-report=term`.
- Format: `uv run black src/ tests/`.
- Lint: `uv run flake8 src/ tests/`.
- Types: `uv run mypy src/`.

## Coding Style & Naming Conventions
- Python 3.11+. Use type hints; CI treats untyped defs as errors (`mypy: disallow_untyped_defs=True`).
- Formatting: Black (line length 88). Flake8 ignores `E203`, `W503`; keep max line length 88.
- Naming: packages/modules `snake_case`; classes `PascalCase`; functions/variables `snake_case`; constants `UPPER_SNAKE_CASE`.
- Docstrings: concise triple-quoted summaries; prefer small, focused functions and pure helpers.

## Testing Guidelines
- Framework: pytest (existing tests also use `unittest` style). Place tests under `tests/` and name files `test_*.py`.
- Write deterministic unit tests; cover happy-path and edge cases (e.g., invalid paths, cache expiry/eviction).
- Run locally with `uv run python -m pytest`; include coverage when adding features.

## Commit & Pull Request Guidelines
- Commits: follow Conventional Commits (e.g., `feat:`, `fix:`, `ci:`, `docs:`). Example: `feat(engine): add basic task filtering`.
- PRs: include a clear description, rationale, and links to issues. Add examples/output snippets when relevant; update docs if behavior or commands change.
- CI must pass (black, flake8, mypy, pytest, bandit). Prefer smaller, reviewable PRs.

## Security & Configuration Tips
- Always use absolute `working_directory`; the engine rejects unsafe paths.
- Prefer `read-only` or `workspace-write` sandbox modes; avoid `danger-full-access` unless necessary.
- Environment: `CACHE_TTL`, `MAX_CACHE_SIZE` configure caching.
- Do not commit secrets; keep timeouts and subprocess handling intact when modifying CLI invocation.


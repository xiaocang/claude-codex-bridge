# Repository Guidelines

## Development Setup
- Python 3.11+ using `uv` for dependency management.
- Install dependencies: `uv sync` (use `uv sync --group dev` to include dev tools).

## Quick Start Commands
- Run MCP server (development): `uv run python -m claude_codex_bridge`
- Direct entry: `uv run src/claude_codex_bridge/bridge_server.py`
- Debug with MCP Inspector: `uv run mcp dev src/claude_codex_bridge/bridge_server.py`
- Or via console script: `uv run claude-codex-bridge`
- Tests: `uv run python -m pytest tests/`
- Coverage: `uv run python -m pytest --cov=claude_codex_bridge --cov-report=term tests/`
- Format: `uv run black src/ tests/`
- Types: `uv run mypy src/`
- Lint: `uv run flake8 src/ tests/`
- Security: `uv run bandit -r src/`
- Build: `uv build` or `make build` (artifacts in `dist/`)
- Clean: `make clean`

## Backend Selection
- Default Codex backend: `mcp`.
- Force legacy CLI backend: pass `--legacy-cmd` (sets `CODEX_BACKEND=cli`).

## Environment Configuration
- Use a `.env` file in the project root to configure optional settings:
  - `CODEX_ALLOW_WRITE=true` to enable file write operations (default: false).
  - `CODEX_BACKEND=mcp|cli` to select backend (default: mcp).
  - `CODEX_CMD=codex` to override Codex command path.

## Project Structure & Module Organization
- `src/claude_codex_bridge/`: Core package (`__main__.py`, `bridge_server.py`, `engine.py`).
- `tests/`: Unit tests (engine, invocation args, delimiter handling, read-only mode, timeouts, task complexity).
- `.github/workflows/ci.yml`: CI for style, types, security, and tests.
- `pyproject.toml`: Packaging, dependencies, and scripts. `Makefile`: minimal build targets.

## Coding Style & Naming Conventions
- Python 3.11+. Use type hints; CI treats untyped defs as errors (`mypy: disallow_untyped_defs=True`).
- Formatting: Black (line length 88). Flake8 ignores `E203`, `W503`; keep max line length 88.
- Naming: packages/modules `snake_case`; classes `PascalCase`; functions/variables `snake_case`; constants `UPPER_SNAKE_CASE`.
- Docstrings: concise triple-quoted summaries; prefer small, focused functions and pure helpers.

## Testing Guidelines
- Framework: pytest. Place tests under `tests/` and name files `test_*.py`.
- Use `tempfile.TemporaryDirectory()` for isolated file system tests when applicable.
- Cover both success and failure paths; validate directory security, delimiter parsing, sandbox enforcement, timeouts, and parameter handling.
- Run locally with `uv run python -m pytest`; include coverage when adding features.

## Commit & Pull Request Guidelines
- Commits: follow Conventional Commits (e.g., `feat:`, `fix:`, `ci:`, `docs:`). Example: `feat(engine): add basic task filtering`.
- PRs: include a clear description, rationale, and links to issues. Add examples/output snippets when relevant; update docs if behavior or commands change.
- CI must pass (black, flake8, mypy, pytest, bandit). Prefer smaller, reviewable PRs.

## Security Considerations
- Always use absolute `working_directory`; the engine rejects unsafe paths and system directories (`/etc`, `/usr/bin`, `/bin`, `/sbin`, `/root`).
- Sandbox modes:
  - `read-only` (default) for safe analysis and planning.
  - `workspace-write` for development when write is explicitly allowed.
  - `danger-full-access` only when absolutely necessary.
- Environment controls:
  - `CODEX_ALLOW_WRITE=true` required to enable write operations.
  - Server defaults to read-only unless explicitly overridden.
- Process isolation and timeouts:
  - Codex runs in an isolated subprocess with the correct working directory.
  - 1-hour timeout prevents runaway processes; errors are handled gracefully.
- Do not commit secrets; keep timeouts and subprocess handling intact when modifying CLI invocation.

## Development Guidelines
- Write code, comments, and string constants in English.
- Use absolute paths for directory operations.
- Validate user inputs and environment configuration.
- Follow async/await patterns for I/O.
- Keep functions small and focused; prefer pure helpers.

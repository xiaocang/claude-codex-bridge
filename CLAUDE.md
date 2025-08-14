# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Setup

This project uses Python 3.11+ with the `uv` package manager for dependency management.

### Quick Start Commands
```bash
# Install dependencies
uv sync

# Run the MCP server (development mode)
uv run python -m claude_codex_bridge
# Or directly:
uv run src/claude_codex_bridge/bridge_server.py

# Debug with MCP Inspector
uv run mcp dev src/claude_codex_bridge/bridge_server.py

# Run all tests
uv run python -m pytest tests/

# Run specific test file
uv run python -m pytest tests/test_engine.py
uv run python -m pytest tests/test_cache.py

# Run tests with coverage
uv run python -m pytest --cov=claude_codex_bridge tests/

# Code quality checks
uv run black src/ tests/         # Format code
uv run mypy src/                 # Type checking
uv run flake8 src/ tests/        # Linting
uv run bandit -r src/            # Security analysis

# Build and package
uv build                         # Build wheel and sdist
make build                       # Alternative using Makefile
make clean                       # Clean build artifacts
```

### Environment Configuration
Create a `.env` file in the project root to configure optional settings:
```bash
# Cache configuration
CACHE_TTL=3600          # Cache time-to-live in seconds (default: 3600)
MAX_CACHE_SIZE=100      # Maximum cache entries (default: 100)
```

## Architecture Overview

This is an **intelligent MCP (Model Context Protocol) server** that acts as a bridge between Claude Code and OpenAI Codex CLI. The system consists of three main components:

### Core Components

**1. Bridge Server (`src/bridge_server.py`)**
- FastMCP-based server providing standardized tool interfaces
- Main entry point exposing tools: `codex_delegate`, `cache_stats`, `clear_cache`
- Handles asynchronous Codex CLI invocation with timeout management
- Provides MCP resources and prompt templates for common tasks

**2. Delegation Decision Engine (`src/engine.py`)**
- Analyzes tasks to determine delegation suitability (currently always delegates in V1)
- Validates working directory security (prevents access to system paths like `/etc`, `/usr/bin`)
- Prepares and optimizes task prompts for Codex CLI execution

**3. Result Cache (`src/cache.py`)**
- Memory-based LRU cache with TTL (time-to-live) expiration
- Generates cache keys from task parameters + file content hashes
- Automatically invalidates cache when directory contents change
- Supports cleanup of expired entries and size-based eviction

### Key Architectural Patterns

**Intelligent Task Delegation**: The system doesn't just forward requests - it analyzes task descriptions, optimizes instructions, and caches results based on file content changes.

**Security-First Design**: Working directory validation prevents path traversal attacks, and sandbox modes provide different levels of filesystem access control.

**Content-Aware Caching**: Cache keys include directory content hashes, so cache automatically invalidates when files change, ensuring results stay current.

## MCP Tool Usage

### Primary Tool: `codex_delegate`
Delegates coding tasks to OpenAI Codex CLI with intelligent prompt optimization and caching.

**Required Parameters:**
- `task_description`: Natural language description of the coding task
- `working_directory`: Absolute path to project directory

**Optional Parameters:**
- `execution_mode`: `untrusted`, `on-failure` (default), `on-request`, `never`
- `sandbox_mode`: `read-only`, `workspace-write` (default), `danger-full-access`
- `output_format`: `diff` (default), `full_file`, `explanation`

**Example Usage:**
```python
await codex_delegate(
    task_description="Add email validation method to User class",
    working_directory="/Users/username/my-project",
    execution_mode="on-failure",
    sandbox_mode="workspace-write"
)
```

### Cache Management Tools
- `cache_stats()`: Returns cache statistics and cleans expired entries
- `clear_cache()`: Clears all cached results

### MCP Resources
- `bridge://docs/usage`: Detailed usage guide
- `bridge://docs/best_practices`: Best practices for task descriptions

### MCP Prompt Templates
- `refactor_code(file_path, refactor_type)`: Generates refactoring prompts
- `generate_tests(file_path, test_framework)`: Generates test creation prompts

## Testing Strategy

The project uses pytest with comprehensive unit tests covering:

**Engine Tests (`tests/test_engine.py`):**
- Task delegation logic
- Working directory validation (security checks)
- Prompt preparation and optimization
- Dangerous path detection

**Cache Tests (`tests/test_cache.py`):**
- Cache key generation consistency
- Directory content hashing
- TTL expiration behavior
- LRU eviction under size constraints
- Statistics and cleanup operations

**Test Execution Patterns:**
- Uses `tempfile.TemporaryDirectory()` for isolated file system tests
- Tests both success and failure scenarios
- Validates security constraints

## Development Workflow

### Code Organization
- `src/claude_codex_bridge/`: Main source code with clean separation of concerns
- `tests/`: Unit tests mirroring source structure
- Configuration via environment variables with sensible defaults
- Error handling with graceful degradation

### Key Implementation Details
- Uses async/await throughout for non-blocking I/O operations
- Implements proper subprocess management with timeout handling
- Chinese comments in some files indicate international development context
- Follows Python best practices with type hints and comprehensive error handling
- Package is published to PyPI as `claude-codex-bridge`

### Working with Codex CLI Integration
- Requires OpenAI Codex CLI to be installed: `npm install -g @openai/codex`
- Uses subprocess execution with proper working directory isolation
- Supports multiple execution and sandbox modes for different security requirements
- Provides structured JSON output parsing with automatic content type detection

## Security Considerations

**Working Directory Validation**: Prevents access to system directories (`/etc`, `/usr/bin`, `/bin`, `/sbin`, `/root`)

**Sandbox Modes**: 
- `read-only`: Safe for code analysis
- `workspace-write`: Recommended for development
- `danger-full-access`: Use with extreme caution

**Path Security**: Always use absolute paths, validate directory existence and permissions

- write code, comments, and string const, with English, always
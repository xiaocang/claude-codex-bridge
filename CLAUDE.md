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

### Backend Selection
- Default Codex backend: MCP
- Force legacy CLI backend: add `--legacy-cmd` to the bridge invocation

### Environment Configuration
Create a `.env` file in the project root to configure optional settings:
- `CODEX_ALLOW_WRITE=true`: Enable file write operations (default: false for safety)
- `CODEX_BACKEND=mcp|cli`: Select backend type (default: mcp)
- `CODEX_CMD=codex`: Override Codex command path (default: "codex")

## Architecture Overview

This is an **intelligent MCP (Model Context Protocol) server** that acts as a bridge between Claude Code and OpenAI Codex CLI. The system consists of three main components:

### Core Components

**1. Bridge Server (`src/bridge_server.py`)**
- FastMCP-based server providing standardized tool interfaces
- Main entry point exposing tool: `codex_delegate`
- Handles asynchronous Codex CLI invocation with timeout management
- Provides MCP resources and prompt templates for common tasks

**2. Delegation Decision Engine (`src/engine.py`)**
- Analyzes tasks to determine delegation suitability (currently always delegates in V1)
- Validates working directory security (prevents access to system paths like `/etc`, `/usr/bin`)
- Prepares and optimizes task prompts for Codex CLI execution

### Key Architectural Patterns

**Intelligent Task Delegation**: The system doesn't just forward requests - it analyzes task descriptions and optimizes instructions for Codex CLI.

**Security-First Design**: Working directory validation prevents path traversal attacks, and sandbox modes provide different levels of filesystem access control.


## MCP Tool Usage

### Primary Tool: `codex_delegate`
Delegates coding tasks to OpenAI Codex CLI with intelligent prompt optimization.

**Required Parameters:**
- `task_description`: Natural language description of the coding task
- `working_directory`: Absolute path to project directory

**Optional Parameters:**
- `approval_policy`: `untrusted`, `on-failure` (default), `on-request`, `never`
- `sandbox_mode`: `read-only` (default), `workspace-write`, `danger-full-access`
- `output_format`: `explanation` (default), `diff`, `full_file`
- `task_complexity`: `minimal`, `low`, `medium` (default), `high`
- `max_output_tokens`: Maximum tokens for response (default: 100000)
- `web_search`: Enable web search tool (default: false)

**Example Usage:**
```python
await codex_delegate(
    task_description="Add email validation method to User class",
    working_directory="/Users/username/my-project",
    approval_policy="on-failure",
    sandbox_mode="workspace-write",
    task_complexity="medium"
)
```


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

**Additional Tests:**
- **Bridge Server Tests (`tests/test_bridge_server.py`)**: Async MCP server functionality
- **Invocation Tests**: Parameter handling and CLI/MCP backend selection
- **Delimiter Tests**: Output parsing with various delimiter configurations
- **Security Tests**: Directory validation and sandbox mode enforcement

**Test Execution Patterns:**
- Uses `tempfile.TemporaryDirectory()` for isolated file system tests
- Tests both success and failure scenarios
- Validates security constraints and parameter edge cases
- Mocks subprocess execution for timeout and error scenarios

## Development Workflow

### Code Organization
- `src/claude_codex_bridge/bridge_server.py`: Main MCP server with FastMCP integration
- `src/claude_codex_bridge/engine.py`: Delegation Decision Engine for task analysis
- `tests/`: Comprehensive test suite covering engine, server, and edge cases
- Configuration via environment variables with secure defaults
- Error handling with graceful degradation and structured responses

### Key Implementation Details
- **Dual Backend Support**: MCP (default) and CLI backends for Codex integration
- **Security-First Design**: Read-only mode by default, explicit write enablement required
- **Async Architecture**: Uses async/await throughout for non-blocking I/O operations
- **Robust Output Parsing**: Wrapper-style delimiter extraction with fallback support
- **Directory Security**: Path validation prevents access to system directories
- **Package Distribution**: Published to PyPI as `claude-codex-bridge`

### Backend Integration Patterns
**MCP Backend (Default):**
- Uses `codex mcp` subprocess with stdio client
- Process-level configuration via CLI flags
- Tool discovery and dynamic invocation
- Structured content extraction from MCP responses

**CLI Backend (Legacy):**
- Direct `codex exec` subprocess invocation
- Command-line parameter configuration
- stdout/stderr capture and parsing
- Backward compatibility with existing workflows

## Security Considerations

**Working Directory Validation**:
- Prevents access to system directories (`/etc`, `/usr/bin`, `/bin`, `/sbin`, `/root`)
- Requires absolute paths and validates directory existence
- Uses `os.path.realpath()` to resolve symlinks before validation

**Sandbox Modes**:
- `read-only`: Safe for code analysis and planning (default)
- `workspace-write`: Recommended for development (requires `--allow-write`)
- `danger-full-access`: Full system access (use with extreme caution)

**Environment-Based Controls**:
- `CODEX_ALLOW_WRITE=true`: Required to enable file write operations
- Server defaults to read-only mode for safety unless explicitly overridden

**Process Isolation**:
- Codex CLI/MCP runs in isolated subprocess with proper working directory
- 1-hour timeout protection against runaway processes
- Structured error handling for process failures

## Development Guidelines

- Write code, comments, and string constants in English
- Use absolute paths for all directory operations
- Validate all user inputs and environment configurations
- Test both success and failure scenarios thoroughly
- Follow async/await patterns for I/O operations

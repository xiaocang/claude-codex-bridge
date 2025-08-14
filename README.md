# Claude-Codex Bridge

An intelligent **MCP (Model Context Protocol) server** that leverages Codex's exceptional capabilities in **code analysis, architectural planning, and complex problem-solving**.

## Philosophy: Think First, Execute Later

Claude-Codex Bridge embraces a **planning-first approach** to software development. Codex's true strength lies not in blindly executing changes, but in:

- 🧠 **Deep Understanding**: Comprehending complex code relationships and patterns
- 📊 **Strategic Analysis**: Identifying optimization opportunities and architectural insights
- 🎯 **Thoughtful Planning**: Designing robust, well-considered solutions
- ✅ **Quality Assurance**: Reviewing code for best practices, security, and performance

### Why Read-Only by Default?

1. **Safety First**: Prevent accidental modifications during code exploration
2. **Better Decisions**: Encourage thorough analysis before making changes
3. **Learning Tool**: Understand the "why" behind recommendations, not just the "what"
4. **Audit Trail**: Clear separation between planning and execution phases

### Recommended Development Flow

```mermaid
graph LR
    A[🔍 Analyze] --> B[🧠 Understand]
    B --> C[📋 Plan]
    C --> D[👁️ Review]
    D --> E[⚡ Execute]
    E --> F[✅ Validate]
```

1. **Analyze**: Use read-only mode to deeply understand your codebase
2. **Understand**: Let Codex explain complex relationships and patterns
3. **Plan**: Design comprehensive solutions and strategies
4. **Review**: Examine Codex's recommendations carefully
5. **Execute**: Enable write mode and apply changes thoughtfully
6. **Validate**: Test and verify the implemented changes

## Project Overview

Claude-Codex Bridge is an **Intelligent Analysis Engine** that orchestrates task delegation between Claude Code and locally running OpenAI Codex CLI. Rather than a simple code generator, it's a sophisticated planning and analysis system with intelligent caching, security validation, and read-only safety defaults.

## Core Features

### 🚀 Intelligent Task Delegation
- **Automatic Task Routing**: Intelligently analyzes tasks and decides whether to delegate to Codex CLI
- **Working Directory Management**: Secure working directory validation and file access control
- **Execution Mode Control**: Supports multiple execution and sandbox modes for different security requirements

### 🧠 Intelligent Processing
- **Context Enhancement**: Intelligent context generation and file content management
- **Error Handling**: Comprehensive error handling and fallback mechanisms

### ⚡ Performance Optimization
- **Intelligent Caching**: File content hash-based result caching system
- **Concurrency Control**: Asynchronous execution and timeout management
- **Resource Management**: LRU cache strategy and automatic cleanup mechanisms

### 🛡️ Security Assurance
- **Path Validation**: Strict working directory validation to prevent path traversal attacks
- **Sandbox Isolation**: Supports multiple sandbox modes to restrict filesystem access
- **Permission Control**: Fine-grained execution permission management

## Technical Architecture

```mermaid
graph TD
    A[Claude Code] --> B[MCP Client]
    B --> C{Claude-Codex Bridge}

    C --> D[Delegation Decision Engine]
    C --> E[Result Cache]

    C --> G[Codex CLI]
    G --> H[Local Sandbox]

    C --> I[Output Parser]
    I --> B
    B --> A
```

### Component Overview

1. **MCP Server**: High-performance server based on FastMCP, providing standardized tool interfaces
2. **Delegation Decision Engine (DDE)**: Intelligently analyzes tasks and determines optimal execution strategies
3. **Result Cache**: Intelligent caching system based on content hashes, avoiding duplicate executions
4. **Output Parser**: Intelligently identifies and formats Codex output into structured data

## Quick Start

### Prerequisites

1. **Python 3.11+**
2. **OpenAI Codex CLI**: `npm install -g @openai/codex`

### Installation

#### From PyPI (Recommended)

```bash
pip install claude-codex-bridge
```

#### From Source

1. **uv Package Manager** (if building from source): `curl -LsSf https://astral.sh/uv/install.sh | sh`

2. **Clone the project**
   ```bash
   git clone https://github.com/xiaocang/claude-codex-bridge.git
   cd claude-codex-bridge
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

4. **Configure environment variables** (optional)
   ```bash
   # Copy environment variable template
   cp .env.example .env

   # Edit .env file, add API keys
   vim .env
   ```

### Starting the Server

The server supports two operational modes:

#### 📋 Planning Mode (Default - Recommended)
Start in read-only mode for safe code analysis and planning:

**If installed from PyPI:**
```bash
claude-codex-bridge
```

**Or using Python module:**
```bash
python -m claude_codex_bridge
```

**If running from source:**
```bash
uv run python -m claude_codex_bridge
```

#### ⚡ Execution Mode (When Ready to Apply Changes)
Enable write operations when you're ready to implement Codex's recommendations:

**If installed from PyPI:**
```bash
claude-codex-bridge --allow-write
```

**Or using Python module:**
```bash
python -m claude_codex_bridge --allow-write
```

**If running from source:**
```bash
uv run python -m claude_codex_bridge --allow-write
```

#### Command-Line Options
- `--allow-write`: Enable file modification operations (default: read-only)
- `--verbose`: Enable verbose output for debugging

### Claude Code Integration

#### 1. Configure MCP Server
You can configure separate servers for planning and execution modes:

**Planning Mode (Default):**
```bash
# In your project directory - for safe analysis and planning
claude mcp add codex-planning --command "claude-codex-bridge" --scope project
```

**Execution Mode:**
```bash
# In your project directory - for applying changes
claude mcp add codex-execution --command "claude-codex-bridge --allow-write" --scope project
```

**Or use the example configuration file:**
```bash
# Copy the example configuration
cp .mcp.json.example .mcp.json
# Edit to match your setup
```

#### 2. Usage Examples

**Planning Phase (Read-Only):**
```
/mcp__codex-planning__codex_delegate "Analyze the authentication system for security vulnerabilities" --working_directory "/path/to/your/project"
```

**Execution Phase (Write-Enabled):**
```
/mcp__codex-execution__codex_delegate "Implement the security fixes we planned earlier" --working_directory "/path/to/your/project"
```

## Practical Workflow Examples

### Example 1: Security Analysis & Hardening
```bash
# Step 1: Analysis (Planning Mode)
/mcp__codex-planning__codex_delegate "Analyze all API endpoints for security vulnerabilities"

# Step 2: Planning (Planning Mode)
/mcp__codex-planning__codex_delegate "Design comprehensive security fixes for the identified vulnerabilities"

# Step 3: Implementation (Execution Mode)
/mcp__codex-execution__codex_delegate "Implement the planned security improvements"
```

### Example 2: Performance Optimization
```bash
# Step 1: Profiling (Planning Mode)
/mcp__codex-planning__codex_delegate "Analyze the application for performance bottlenecks"

# Step 2: Strategy (Planning Mode)
/mcp__codex-planning__codex_delegate "Design optimization strategies for the identified performance issues"

# Step 3: Implementation (Execution Mode)
/mcp__codex-execution__codex_delegate "Implement the highest-impact performance optimizations"
```

### Example 3: Architecture Refactoring
```bash
# Step 1: Assessment (Planning Mode)
/mcp__codex-planning__codex_delegate "Evaluate the current architecture for scalability issues"

# Step 2: Design (Planning Mode)
/mcp__codex-planning__codex_delegate "Design a migration plan to improve the architecture"

# Step 3: Execution (Execution Mode)
/mcp__codex-execution__codex_delegate "Implement phase 1 of the architectural improvements"
```

## Main Tools

### `codex_delegate`

Leverage Codex's advanced analytical capabilities for code comprehension and strategic planning.

**Codex Specializes In**:
- 🔍 Analyzing complex codebases and identifying improvement opportunities
- 🏗️ Designing architectural solutions and refactoring strategies
- 📋 Planning implementation approaches for new features
- 🧪 Generating comprehensive test strategies
- ⚡ Reviewing code for quality, security, and performance issues

**Parameters**:
- `task_description` (required): Describe what you want Codex to analyze or plan
- `working_directory` (required): Project directory to analyze
- `execution_mode` (optional): Approval strategy (default: on-failure)
- `sandbox_mode` (optional): File access mode (forced to read-only unless --allow-write)
- `output_format` (optional): How to format the analysis results (diff/full_file/explanation)

**Planning Mode Example**:
```json
{
  "task_description": "Analyze the user authentication system for security vulnerabilities and design improvement strategies",
  "working_directory": "/Users/username/my-project",
  "execution_mode": "on-failure",
  "sandbox_mode": "read-only",
  "output_format": "explanation"
}
```

**Execution Mode Example**:
```json
{
  "task_description": "Implement the security improvements we planned for the authentication system",
  "working_directory": "/Users/username/my-project",
  "execution_mode": "on-failure",
  "sandbox_mode": "workspace-write",
  "output_format": "diff"
}
```

### `cache_stats`

Get cache statistics and clean up expired entries.

### `clear_cache`

Clear all cache entries.

## Configuration Options

### Environment Variables

```bash
# Cache configuration
CACHE_TTL=3600          # Cache TTL in seconds
MAX_CACHE_SIZE=100      # Maximum cache entries
```

### Execution Mode Explanation

- **untrusted**: Only runs trusted commands, most secure
- **on-failure**: Requests approval on failure, recommended for most tasks
- **on-request**: Model decides when to request approval, suitable for complex tasks
- **never**: Never requests approval, suitable for simple automation tasks

### Sandbox Mode Explanation

- **read-only**: Read-only access, suitable for code analysis and explanation
- **workspace-write**: Writable workspace, suitable for most development tasks
- **danger-full-access**: Full access, use with caution

## Development and Testing

### Running Tests

```bash
# Run all tests
uv run python -m pytest tests/

# Run specific tests
uv run python -m pytest tests/test_engine.py
uv run python -m pytest tests/test_cache.py
```

### Development Mode

```bash
# Debug with MCP Inspector
uv run mcp dev src/claude_codex_bridge/bridge_server.py
# Or if installed
mcp dev claude-codex-bridge
```

### Code Quality

```bash
# Code formatting
uv run black src/ tests/

# Type checking
uv run mypy src/

# Code linting
uv run flake8 src/ tests/
```

## Project Structure

```
claude-codex-bridge/
├── src/
│   └── claude_codex_bridge/
│       ├── __init__.py       # Package initialization
│       ├── __main__.py       # Entry point
│       ├── bridge_server.py # Main MCP server
│       ├── engine.py        # Delegation Decision Engine
│       └── cache.py         # Result caching system
├── tests/
│   ├── test_engine.py     # Engine unit tests
│   └── test_cache.py      # Cache unit tests
├── .env                   # Environment configuration
├── .mcp.json             # MCP client configuration example
├── pyproject.toml        # Project configuration
└── README.md            # Project documentation
```

## Best Practices

### Embrace the Planning-First Approach

#### 📋 Planning Phase (Read-Only Mode)

**✅ Excellent analysis requests**:
- "Analyze the user authentication system for security vulnerabilities and design patterns"
- "Review the database layer for performance bottlenecks and optimization opportunities"
- "Evaluate the API design for RESTful best practices and consistency"
- "Assess the testing strategy and identify gaps in code coverage"

**✅ Strategic planning requests**:
- "Design a migration plan from the current monolithic architecture to microservices"
- "Create a comprehensive refactoring strategy for legacy code modernization"
- "Plan the implementation of a new payment processing feature with security considerations"

#### ⚡ Execution Phase (Write Mode)

**✅ Implementation-focused requests**:
- "Implement the security improvements we planned for the authentication system"
- "Apply the performance optimizations designed for the database queries"
- "Execute phase 1 of the microservices migration plan"

### Task Description Guidelines

#### ❌ Avoid Vague Requests
- "Improve the code" → Too broad, no specific focus
- "Fix all issues" → Overwhelming scope
- "Add new features" → Lacks specificity

#### ✅ Write Specific, Actionable Descriptions
- **Analysis**: "What patterns, issues, or opportunities should Codex identify?"
- **Planning**: "What strategies, approaches, or solutions should Codex design?"
- **Implementation**: "What specific changes should Codex apply?"

### Security and Safety Recommendations

1. **Start with Analysis**: Always begin in read-only mode to understand before acting
2. **Use Absolute Paths**: Specify working directories with full paths
3. **Plan Before Executing**: Review Codex's recommendations before enabling write mode
4. **Validate Changes**: Test thoroughly after applying modifications
5. **Monitor Resources**: Keep an eye on cache and system resource usage

## Troubleshooting

### Common Issues

**Q: Codex CLI not found**
```
A: Make sure it's installed: npm install -g @openai/codex
```

**Q: Working directory validation failed**
```
A: Check that the directory path is absolute and exists
```

**Q: Cache miss**
```
A: File content changes invalidate cache, this is normal behavior
```

## Performance Optimization Tips

1. **Enable caching**: Set appropriate TTL and cache size
2. **Reasonable timeouts**: Set timeout based on task complexity
3. **Regular cleanup**: Use `clear_cache` tool to clean unused cache

## Version History

### v0.1.1
- 🔄 Version update and maintenance release

### v0.1.0
- ✅ Basic MCP server implementation
- ✅ Codex CLI integration
- ✅ Delegation Decision Engine
- ✅ Result caching system
- ✅ Security validation mechanism

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

For questions or suggestions, please create a GitHub Issue or contact the maintainers.

---

**Claude-Codex Bridge** - Making AI agent collaboration smarter 🚀

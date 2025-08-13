"""
Claude-Codex Bridge MCP Server

An intelligent bridge MCP server for orchestrating task delegation
between Claude and OpenAI Codex CLI.
"""

import asyncio
import json
import os
from typing import Literal, Tuple

from mcp.server.fastmcp import FastMCP

try:
    from .cache import ResultCache
    from .engine import DelegationDecisionEngine
except ImportError:
    # When running directly, use absolute imports
    from cache import ResultCache  # type: ignore[no-redef]
    from engine import DelegationDecisionEngine  # type: ignore[no-redef]

# Initialize FastMCP instance
mcp = FastMCP(
    name="claude-codex-bridge",
    instructions="An intelligent MCP server for orchestrating task delegation "
    "between Claude and Codex CLI.",
)

# Initialize Delegation Decision Engine
dde = DelegationDecisionEngine()

# Initialize result cache

cache_ttl = int(os.environ.get("CACHE_TTL", "3600"))  # Default 1 hour
cache_max_size = int(os.environ.get("MAX_CACHE_SIZE", "100"))  # Default 100 entries
result_cache = ResultCache(ttl=cache_ttl, max_size=cache_max_size)


async def invoke_codex_cli(
    prompt: str,
    working_directory: str,
    execution_mode: str,
    sandbox_mode: str,
    timeout: int = 300,  # 5 minute timeout
) -> Tuple[str, str]:
    """
    Asynchronously invoke Codex CLI and return its stdout and stderr.

    Args:
        prompt: The main instruction to send to Codex CLI
        working_directory: Codex working directory
        execution_mode: Codex CLI approval strategy mode
        sandbox_mode: Codex CLI sandbox strategy mode
        timeout: Command timeout in seconds

    Returns:
        Tuple containing (stdout, stderr)

    Raises:
        RuntimeError: When Codex CLI execution fails
        asyncio.TimeoutError: When command times out
    """
    # Build base command
    command = ["codex", "exec"]

    # Always specify working directory (critical)
    command.extend(["-C", working_directory])

    # Use convenience mode or specify parameters separately
    if execution_mode == "on-failure" and sandbox_mode == "workspace-write":
        # Use convenient --full-auto mode
        command.append("--full-auto")
    else:
        # Specify approval and sandbox modes separately
        command.extend(["-a", execution_mode])
        command.extend(["-s", sandbox_mode])

    # Add prompt as final positional argument
    command.append(prompt)

    process = None
    try:
        # Execute subprocess asynchronously
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_directory,  # Also set as double protection
        )

        # Wait for process completion (with timeout)
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

        # Check exit code
        if process.returncode != 0:
            error_message = (
                stderr.decode("utf-8").strip() if stderr else "Unknown error"
            )
            raise RuntimeError(
                f"Codex CLI execution failed (exit code: {process.returncode}): "
                f"{error_message}"
            )

        return stdout.decode("utf-8"), stderr.decode("utf-8")

    except asyncio.TimeoutError:
        # Timeout handling
        if process is not None:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()

        raise asyncio.TimeoutError(
            f"Codex CLI execution timed out (exceeded {timeout} seconds)"
        )

    except FileNotFoundError:
        raise RuntimeError(
            "codex command not found. Please ensure OpenAI Codex CLI is "
            "installed: npm install -g @openai/codex"
        )


def parse_codex_output(stdout: str, output_format: str) -> dict:
    """
    Parse Codex CLI output into structured JSON.

    Args:
        stdout: Codex CLI standard output
        output_format: Expected output format

    Returns:
        Structured parsing result
    """
    # Auto-detect output type
    output_type = "explanation"  # Default type

    if "--- a/" in stdout and "+++ b/" in stdout:
        output_type = "diff"
    elif "```" in stdout and stdout.count("```") >= 2:
        output_type = "code"
    elif any(
        keyword in stdout.lower()
        for keyword in ["file:", "class ", "function ", "def ", "import "]
    ):
        output_type = "code"

    return {
        "status": "success",
        "type": output_type,
        "content": stdout.strip(),
        "format": output_format,
        "detected_type": output_type,
    }


@mcp.tool()
async def codex_delegate(
    task_description: str,
    working_directory: str,
    execution_mode: Literal[
        "untrusted", "on-failure", "on-request", "never"
    ] = "on-failure",
    sandbox_mode: Literal[
        "read-only", "workspace-write", "danger-full-access"
    ] = "workspace-write",
    output_format: Literal["diff", "full_file", "explanation"] = "diff",
) -> str:
    """
    Delegate complex coding tasks to the OpenAI Codex CLI.

    Use this tool when you need to refactor code, fix bugs, generate new
    functions, add tests, or explain code snippets. It provides a structured
    way to interact with the local file system and leverage Codex's powerful
    coding capabilities.

    Args:
        task_description: A detailed, natural language description of the
            task to delegate to Codex.
        working_directory: The path to the project's working directory where
            Codex will operate.
        execution_mode: The approval policy mode for the Codex CLI.
        sandbox_mode: The sandbox policy mode for the Codex CLI.
        output_format: The expected format of the result.

    Returns:
        A JSON string containing the result of the task execution.
    """
    # 1. Validate working directory
    if not dde.validate_working_directory(working_directory):
        error_result = {
            "status": "error",
            "message": f"Invalid or unsafe working directory: {working_directory}",
            "error_type": "invalid_directory",
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)

    # 2. Check cache
    cached_result = result_cache.get(
        task_description, working_directory, execution_mode, sandbox_mode, output_format
    )
    if cached_result:
        # Parse cached result and add cache flag
        try:
            result_dict = json.loads(cached_result)
            result_dict["cache_hit"] = True
            result_dict["cache_note"] = "This result comes from the cache"
            return json.dumps(result_dict, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # Invalid cache result format, continue with normal execution
            pass

    # 3. Use DDE to decide whether to delegate
    if not dde.should_delegate(task_description):
        rejection_result = {
            "status": "rejected",
            "message": "The task is not suitable for delegation to Codex CLI",
            "reason": "Task not suitable for Codex delegation",
        }
        return json.dumps(rejection_result, indent=2, ensure_ascii=False)

    # 4. Prepare Codex instruction
    codex_prompt = dde.prepare_codex_prompt(task_description)
    optimization_note = None  # Will be used for metacognitive optimization in future

    try:
        # 5. Invoke Codex CLI
        stdout, stderr = await invoke_codex_cli(
            codex_prompt, working_directory, execution_mode, sandbox_mode
        )

        # 6. Parse output
        result = parse_codex_output(stdout, output_format)

        # Add metadata
        result.update(
            {
                "working_directory": working_directory,
                "execution_mode": execution_mode,
                "sandbox_mode": sandbox_mode,
                "optimization_note": optimization_note,
                "original_task": task_description,
                "codex_prompt": (
                    codex_prompt if codex_prompt != task_description else None
                ),
            }
        )

        # If there is stderr, include it as well
        if stderr.strip():
            result["stderr"] = stderr.strip()

        # Add cache flag
        result["cache_hit"] = False

        # 7. Store result in cache (only on success)
        result_json = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            result_cache.set(
                task_description,
                working_directory,
                execution_mode,
                sandbox_mode,
                output_format,
                result_json,
            )
        except Exception as cache_error:
            # Cache failure should not affect main functionality
            print(f"Failed to store cache: {cache_error}")

        return result_json

    except Exception as e:
        # Handle execution errors
        error_result = {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "working_directory": working_directory,
            "execution_mode": execution_mode,
            "sandbox_mode": sandbox_mode,
            "optimization_note": "",  # No optimization applied on error
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@mcp.tool()
async def cache_stats() -> str:
    """
    Get cache statistics and manage cache.

    Returns:
        JSON string containing cache statistics
    """
    try:
        # Clean up expired cache
        expired_count = result_cache.cleanup_expired()

        # Get statistics
        stats = result_cache.get_stats()

        stats.update({"cleaned_expired_entries": expired_count, "status": "success"})

        return json.dumps(stats, indent=2, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Failed to get cache statistics: {str(e)}",
            "error_type": type(e).__name__,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@mcp.tool()
async def clear_cache() -> str:
    """
    Clears all caches.

    Returns:
        A JSON string of the operation result.
    """
    try:
        old_stats = result_cache.get_stats()
        result_cache.clear()

        result = {
            "status": "success",
            "message": "Cache has been cleared",
            "cleared_entries": old_stats["total_entries"],
        }

        return json.dumps(result, indent=2, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"Failed to clear cache: {str(e)}",
            "error_type": type(e).__name__,
        }
        return json.dumps(error_result, indent=2, ensure_ascii=False)


@mcp.resource("bridge://docs/usage")
def get_usage_guide() -> str:
    """
    Return the usage guide documentation for Claude-Codex Bridge.
    """
    return """
# Claude-Codex Bridge Usage Guide

Claude-Codex Bridge is an intelligent MCP server for orchestrating task
delegation between Claude and OpenAI Codex CLI.

## Basic Usage

### Calling the codex_delegate tool

```
codex_delegate(
    task_description="Your task description",
    working_directory="/path/to/your/project",
    execution_mode="on-failure",      # optional
    sandbox_mode="workspace-write",   # optional
    output_format="diff"              # optional
)
```

### Parameter Explanation

**task_description** (required)
- Detailed natural language description of the task to delegate to Codex
- Example: "Refactor main.py file by extracting all functions into a
  new class named Utils"

**working_directory** (required)
- Absolute path to project working directory
- Codex will work and access files in this directory
- Example: "/Users/username/my-project"

**execution_mode** (optional, default: "on-failure")
- `untrusted`: Only run trusted commands
- `on-failure`: Request approval only on failure
- `on-request`: Model decides when to request approval
- `never`: Never request approval

**sandbox_mode** (optional, default: "workspace-write")
- `read-only`: Read-only filesystem access
- `workspace-write`: Writable workspace files
- `danger-full-access`: Full system access (dangerous)

**output_format** (optional, default: "diff")
- `diff`: Returns changes in patch format
- `full_file`: Returns complete modified file content
- `explanation`: Returns natural language explanation

## Advanced Features

### Metacognitive Instruction Optimization
When `ANTHROPIC_API_KEY` environment variable is set, the bridge uses
Claude 3 Haiku to automatically optimize your task instructions for clarity
and specificity.

### Automatic Output Type Detection
The bridge automatically recognizes Codex return content types (diff,
code blocks, or explanation text) and labels them in responses.

## Best Practices

1. **Clear task objectives**: Clearly state "what" you want done, not "how"
2. **Provide full paths**: Always use absolute paths for working directories
3. **Choose appropriate execution mode**: Select suitable execution and
   sandbox modes based on task complexity and risk
4. **Safety first**: For production environments, recommended to use
   `read-only` sandbox mode

## Example Usage

### Code Refactoring
```
task_description: "Refactor all functions in src/utils.py to use async/await syntax"
working_directory: "/Users/username/my-python-project"
execution_mode: "on-failure"
sandbox_mode: "workspace-write"
```

### Test Generation
```
task_description: "Generate complete unit tests for the User class in models/user.py"
working_directory: "/Users/username/my-django-project"
execution_mode: "on-request"
sandbox_mode: "workspace-write"
```

### Code Explanation
```
task_description: "Explain the sorting algorithm implementation in algorithm.py"
working_directory: "/Users/username/algorithms"
execution_mode: "untrusted"
sandbox_mode: "read-only"
output_format: "explanation"
```

## Error Handling

The bridge provides detailed error information including:
- Working directory validation errors
- Codex CLI execution errors
- Timeout errors
- Permission errors

Check the `status` field in returned JSON to determine execution result.

## Prerequisites

1. Install OpenAI Codex CLI: `npm install -g @openai/codex`
2. Optional: Set `ANTHROPIC_API_KEY` environment variable to enable
   metacognitive optimization
"""


@mcp.resource("bridge://docs/best_practices")
def get_best_practices() -> str:
    """
    Returns best practices for writing effective Codex delegation instructions.
    """
    return """
# Codex Delegation Task Best Practices

## Task Description Writing Tips

### ✅ Good Task Descriptions
- **Specific and clear**: "Add a validate_email method to the User class to
  verify email format"
- **Scope defined**: "Refactor all authentication-related functions in src/auth.py"
- **Clear objective**: "Add boundary condition tests for calculate_tax function"

### ❌ Descriptions to Avoid
- **Too vague**: "Improve the code"
- **Too broad**: "Fix all issues in the project"
- **No context**: "Add new feature"

## Execution Mode Selection

### untrusted (Safest)
- Use case: Code analysis, documentation generation, read-only operations
- Pros: Highest security
- Cons: Limited functionality

### on-failure (Recommended)
- Use case: Most development tasks
- Pros: Balanced security and efficiency
- Requests approval when failing

### on-request (Flexible)
- Use case: Complex tasks requiring human judgment
- Codex requests approval when needed

### never (High risk)
- Use case: Fully automated simple tasks
- Note: Requires complete trust in Codex's judgment

## Sandbox Mode Selection

### read-only (Safest)
- For code analysis, explanation, documentation generation
- Won't modify any files

### workspace-write (Recommended)
- Can modify files in workspace
- Suitable for most development tasks

### danger-full-access (Dangerous)
- Full filesystem access
- Use only in special cases

## Success Rate Improvement Tips

1. **Break down complex tasks**
   ```
   ❌ "Rewrite the entire user management system"
   ✅ "Refactor create_user function in user.py for better readability"
   ```

2. **Provide specific file paths**
   ```
   ❌ "Modify configuration file"
   ✅ "Modify database connection settings in config/settings.py"
   ```

3. **Specify expected outcomes**
   ```
   ❌ "Optimize the code"
   ✅ "Optimize process_data function to reduce memory usage"
   ```

4. **Include necessary constraints**
   ```
   Example: "Add input validation while ensuring Python 3.8+ compatibility"
   ```

## Working Directory Best Practices

- Use absolute paths
- Ensure directory exists and is accessible
- Avoid system directories (/etc, /usr/bin etc.)
- Regularly clean temporary files

## Error Handling

- Check returned `status` field
- Read `error_type` and `message` for details
- For timeout errors, consider breaking down tasks or increasing timeout

## Performance Optimization

- Consider longer timeout for complex tasks
- Enable metacognition optimization to improve instruction quality
- Use caching mechanism to avoid repeating identical tasks
"""


try:
    from mcp.server.fastmcp.messages import UserMessage
except ImportError:
    # Try alternative import path or use a simple dict alternative
    class FallbackUserMessage:
        def __init__(self, content: str) -> None:
            self.content = content

    UserMessage = FallbackUserMessage


@mcp.prompt()
def refactor_code(file_path: str, refactor_type: str = "general") -> list:
    """
    Generates a prompt template for refactoring code.

    Args:
        file_path: The path to the file to be refactored
        refactor_type: The type of refactoring (general, performance,
            readability, structure)
    """
    refactor_descriptions = {
        "general": "Perform general code refactoring to improve code quality",
        "performance": "Refactor code to improve performance and efficiency",
        "readability": "Refactor code to improve readability and maintainability",
        "structure": "Refactor code structure to improve architectural design",
    }

    description = refactor_descriptions.get(refactor_type, "Refactor code")

    task_description = (
        f"Please {description} for the file '{file_path}'. Keep the original "
        f"functionality unchanged, but improve code quality, readability, and "
        f"maintainability."
    )

    return [
        UserMessage(f"I will refactor the {file_path} file for you."),
        UserMessage(f"Refactoring type: {refactor_type}"),
        UserMessage(f"Task: {task_description}"),
        UserMessage(
            "Please ensure the working directory is set correctly before "
            "calling the codex_delegate tool."
        ),
    ]


@mcp.prompt()
def generate_tests(file_path: str, test_framework: str = "pytest") -> list:
    """
    Generates a prompt template for creating tests for a specified file.

    Args:
        file_path: The path to the file for which to generate tests
        test_framework: The testing framework (pytest, unittest, jest, etc.)
    """
    task_description = (
        f"Generate comprehensive {test_framework} test cases for file "
        f"'{file_path}'.\\n\\n"
        f"Requirements:\\n"
        f"1. Cover all public functions and methods\\n"
        f"2. Include normal cases and edge condition tests\\n"
        f"3. Add exception handling tests\\n"
        f"4. Ensure test cases are clear and well-described\\n"
        f"5. Follow {test_framework} best practices"
    )

    return [
        UserMessage(f"I will generate {test_framework} test cases for {file_path}."),
        UserMessage(
            "This will include comprehensive test coverage, including edge "
            "cases and exception scenarios."
        ),
        UserMessage(f"Task description: {task_description}"),
        UserMessage(
            "Please call the codex_delegate tool after setting the correct "
            "working directory."
        ),
    ]


if __name__ == "__main__":
    # Start the MCP server
    mcp.run()

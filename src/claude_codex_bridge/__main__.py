#!/usr/bin/env python3
"""Entry point for Claude-Codex Bridge - Intelligent Code Analysis & Planning Tool."""

import argparse
import asyncio
import os
import sys

from .bridge_server import mcp


def main() -> None:
    """Main entry point with command-line argument support."""
    parser = argparse.ArgumentParser(
        description="Claude-Codex Bridge - Leverages Codex's exceptional capabilities "
        "in code analysis, architectural planning, and complex problem-solving.",
        epilog="By default, operates in read-only mode for safety. "
        "Use --allow-write to enable file modifications.",
    )

    parser.add_argument(
        "--allow-write",
        action="store_true",
        help="Enable write operations. Without this flag, Codex operates in "
        "read-only mode for analysis and planning only.",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument(
        "--legacy-cmd",
        action="store_true",
        help=(
            "Use legacy Codex CLI backend (codex exec). "
            "By default the bridge uses the Codex MCP backend."
        ),
    )
    args = parser.parse_args()

    # Set environment variables for the server to use
    os.environ["CODEX_ALLOW_WRITE"] = "true" if args.allow_write else "false"
    os.environ["CODEX_BACKEND"] = "cli" if args.legacy_cmd else "mcp"

    # Display startup information
    mode = "READ-WRITE" if args.allow_write else "READ-ONLY (Planning & Analysis)"
    backend = "legacy CLI (codex exec)" if args.legacy_cmd else "MCP"
    print(
        f"🧠 Starting Claude-Codex Bridge in {mode} mode using {backend} backend",
        file=sys.stderr,
    )

    if not args.allow_write:
        print(
            "📋 Codex will analyze and provide recommendations without modifying files.",
            file=sys.stderr,
        )
        print(
            "💡 To enable write operations, restart with --allow-write flag",
            file=sys.stderr,
        )

    asyncio.run(mcp.run())  # type: ignore[func-returns-value]


if __name__ == "__main__":
    main()

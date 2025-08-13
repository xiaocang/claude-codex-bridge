#!/usr/bin/env python3
"""Entry point for running the MCP server."""

import asyncio

from .bridge_server import mcp


def main() -> None:
    """Main entry point."""
    asyncio.run(mcp.run())  # type: ignore[func-returns-value]


if __name__ == "__main__":
    main()

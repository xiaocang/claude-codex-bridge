"""Claude-Codex Bridge - An intelligent MCP server for task delegation."""

__version__ = "0.1.3"
__author__ = "xiaocang"

from .engine import DelegationDecisionEngine

__all__ = ["DelegationDecisionEngine", "__version__"]

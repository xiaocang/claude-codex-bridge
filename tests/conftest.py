"""
Pytest configuration for claude-codex-bridge tests.

This file ensures that the src package is importable in all test files
without requiring per-file sys.path manipulation.
"""

import os
import sys

# Add src directory to Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

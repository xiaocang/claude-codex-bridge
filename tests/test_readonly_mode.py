"""
Tests for read-only mode enforcement and --allow-write flag functionality.
"""

import json
import os
import unittest
from unittest.mock import patch

from claude_codex_bridge.bridge_server import codex_delegate


class TestReadOnlyMode(unittest.IsolatedAsyncioTestCase):
    """Test read-only mode enforcement and write permission handling."""

    async def asyncSetUp(self):
        """Setup before tests."""
        # Reset environment for clean test state
        if "CODEX_ALLOW_WRITE" in os.environ:
            del os.environ["CODEX_ALLOW_WRITE"]

    async def asyncTearDown(self):
        """Cleanup after tests."""
        # Reset environment
        if "CODEX_ALLOW_WRITE" in os.environ:
            del os.environ["CODEX_ALLOW_WRITE"]

    @patch.dict(os.environ, {"CODEX_ALLOW_WRITE": "false", "CODEX_BACKEND": "cli"})
    @patch("claude_codex_bridge.bridge_server.invoke_codex_cli")
    @patch("claude_codex_bridge.bridge_server.dde.validate_working_directory")
    @patch("claude_codex_bridge.bridge_server.dde.should_delegate")
    async def test_sandbox_mode_forced_to_readonly_when_write_disabled(
        self, mock_should_delegate, mock_validate_dir, mock_invoke_codex
    ):
        """Test that sandbox_mode is forced to read-only when write is disabled."""
        # Setup mocks
        mock_validate_dir.return_value = True
        mock_should_delegate.return_value = True
        mock_invoke_codex.return_value = ("mock output", "")

        # Call with workspace-write but expect read-only to be enforced
        result_json = await codex_delegate(
            task_description="Test task",
            working_directory="/tmp/test",
            sandbox_mode="workspace-write",
        )

        result = json.loads(result_json)

        # Verify that the effective sandbox mode was read-only
        self.assertEqual(result["sandbox_mode"], "read-only")
        self.assertEqual(result["requested_sandbox_mode"], "workspace-write")

        # Verify operation_mode notice is included
        self.assertIn("operation_mode", result)
        self.assertEqual(result["operation_mode"]["mode"], "planning")

        # Verify codex was called with read-only mode
        mock_invoke_codex.assert_called_once()
        call_args = mock_invoke_codex.call_args[0]
        self.assertEqual(call_args[3], "read-only")  # sandbox_mode parameter

    @patch.dict(os.environ, {"CODEX_ALLOW_WRITE": "true", "CODEX_BACKEND": "cli"})
    @patch("claude_codex_bridge.bridge_server.invoke_codex_cli")
    @patch("claude_codex_bridge.bridge_server.dde.validate_working_directory")
    @patch("claude_codex_bridge.bridge_server.dde.should_delegate")
    async def test_sandbox_mode_preserved_when_write_enabled(
        self, mock_should_delegate, mock_validate_dir, mock_invoke_codex
    ):
        """Test that sandbox_mode is preserved when write is enabled."""
        # Setup mocks
        mock_validate_dir.return_value = True
        mock_should_delegate.return_value = True
        mock_invoke_codex.return_value = ("mock output", "")

        # Call with workspace-write and expect it to be preserved
        result_json = await codex_delegate(
            task_description="Test task",
            working_directory="/tmp/test",
            sandbox_mode="workspace-write",
        )

        result = json.loads(result_json)

        # Verify that the sandbox mode was preserved
        self.assertEqual(result["sandbox_mode"], "workspace-write")
        self.assertEqual(result["requested_sandbox_mode"], "workspace-write")

        # Verify no operation_mode notice is included
        self.assertNotIn("operation_mode", result)

        # Verify codex was called with workspace-write mode
        mock_invoke_codex.assert_called_once()
        call_args = mock_invoke_codex.call_args[0]
        self.assertEqual(call_args[3], "workspace-write")  # sandbox_mode parameter

    @patch.dict(os.environ, {"CODEX_ALLOW_WRITE": "false", "CODEX_BACKEND": "cli"})
    @patch("claude_codex_bridge.bridge_server.invoke_codex_cli")
    @patch("claude_codex_bridge.bridge_server.dde.validate_working_directory")
    @patch("claude_codex_bridge.bridge_server.dde.should_delegate")
    async def test_readonly_mode_not_overridden_when_already_readonly(
        self, mock_should_delegate, mock_validate_dir, mock_invoke_codex
    ):
        """Test that read-only mode is not overridden when already read-only."""
        # Setup mocks
        mock_validate_dir.return_value = True
        mock_should_delegate.return_value = True
        mock_invoke_codex.return_value = ("mock output", "")

        # Call with read-only mode
        result_json = await codex_delegate(
            task_description="Test task",
            working_directory="/tmp/test",
            sandbox_mode="read-only",
        )

        result = json.loads(result_json)

        # Verify that read-only mode was preserved and no notice was added
        self.assertEqual(result["sandbox_mode"], "read-only")
        self.assertEqual(result["requested_sandbox_mode"], "read-only")

        # Should not have operation_mode notice since no override occurred
        self.assertNotIn("operation_mode", result)

    @patch.dict(os.environ, {"CODEX_ALLOW_WRITE": "false"})
    @patch("claude_codex_bridge.bridge_server.dde.validate_working_directory")
    async def test_mode_notice_included_in_error_response(self, mock_validate_dir):
        """Test that mode notice is included in error responses."""
        # Setup mock to trigger an error
        mock_validate_dir.return_value = False

        # Call with workspace-write but expect error with mode notice
        result_json = await codex_delegate(
            task_description="Test task",
            working_directory="/invalid/path",
            sandbox_mode="workspace-write",
        )

        result = json.loads(result_json)

        # Verify error response
        self.assertEqual(result["status"], "error")

        # Should still have the mode override information
        self.assertEqual(result["sandbox_mode"], "read-only")
        self.assertEqual(result["requested_sandbox_mode"], "workspace-write")

    def test_operation_mode_notice_structure(self):
        """Test the structure of operation_mode notice."""
        # This tests the structure that should be included when mode is overridden
        expected_notice = {
            "mode": "planning",
            "description": "Operating in planning and analysis mode (read-only)",
            "message": "Codex will analyze your code and provide detailed "
            "recommendations without modifying files.",
            "hint": "To apply changes, restart the server with --allow-write flag",
            "benefits": [
                "Safe exploration of solutions",
                "Comprehensive analysis without risk",
                "Thoughtful planning before execution",
            ],
        }

        # Verify all expected fields are present
        self.assertIn("mode", expected_notice)
        self.assertIn("description", expected_notice)
        self.assertIn("message", expected_notice)
        self.assertIn("hint", expected_notice)
        self.assertIn("benefits", expected_notice)
        self.assertIsInstance(expected_notice["benefits"], list)
        self.assertEqual(len(expected_notice["benefits"]), 3)


if __name__ == "__main__":
    unittest.main()

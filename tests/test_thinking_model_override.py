"""Tests for caller-provided thinking model overrides."""

import json
import os
import unittest
from unittest.mock import patch

from claude_codex_bridge.bridge_server import codex_delegate


class TestThinkingModelOverride(unittest.IsolatedAsyncioTestCase):
    """Ensure thinking model selection honours caller overrides."""

    @patch.dict(os.environ, {"CODEX_ALLOW_WRITE": "false"})
    @patch("claude_codex_bridge.bridge_server.result_cache.get", return_value=None)
    @patch("claude_codex_bridge.bridge_server.result_cache.set")
    @patch("claude_codex_bridge.bridge_server.dde.determine_thinking_model")
    @patch("claude_codex_bridge.bridge_server.dde.should_delegate", return_value=True)
    @patch(
        "claude_codex_bridge.bridge_server.dde.validate_working_directory",
        return_value=True,
    )
    @patch("claude_codex_bridge.bridge_server.invoke_codex_cli")
    async def test_caller_provided_thinking_model_used(
        self,
        mock_invoke,
        _mock_validate,
        _mock_should,
        mock_determine,
        _mock_cache_set,
        _mock_cache_get,
    ) -> None:
        """When thinking_model is supplied, engine heuristics are ignored."""

        mock_determine.return_value = "low"
        mock_invoke.return_value = ("output", "")

        result_json = await codex_delegate(
            task_description="Analyze",
            working_directory="/tmp",
            thinking_model="high",
        )

        mock_determine.assert_not_called()
        _, kwargs = mock_invoke.call_args
        self.assertEqual(kwargs["thinking_model"], "high")

        result = json.loads(result_json)
        self.assertEqual(result["thinking_model"], "high")

    @patch.dict(os.environ, {"CODEX_ALLOW_WRITE": "false"})
    @patch("claude_codex_bridge.bridge_server.result_cache.get", return_value=None)
    @patch("claude_codex_bridge.bridge_server.result_cache.set")
    @patch(
        "claude_codex_bridge.bridge_server.dde.determine_thinking_model",
        return_value="medium",
    )
    @patch("claude_codex_bridge.bridge_server.dde.should_delegate", return_value=True)
    @patch(
        "claude_codex_bridge.bridge_server.dde.validate_working_directory",
        return_value=True,
    )
    @patch("claude_codex_bridge.bridge_server.invoke_codex_cli")
    async def test_default_thinking_model_from_engine(
        self,
        mock_invoke,
        _mock_validate,
        _mock_should,
        _mock_determine,
        _mock_cache_set,
        _mock_cache_get,
    ) -> None:
        """Without override, engine's thinking model is used."""

        mock_invoke.return_value = ("output", "")

        result_json = await codex_delegate(
            task_description="Analyze",
            working_directory="/tmp",
        )

        _, kwargs = mock_invoke.call_args
        self.assertEqual(kwargs["thinking_model"], "medium")

        result = json.loads(result_json)
        self.assertEqual(result["thinking_model"], "medium")


if __name__ == "__main__":
    unittest.main()

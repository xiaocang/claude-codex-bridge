"""
Tests for correct Codex CLI argument construction, ensuring prompts are
passed after a `--` delimiter so leading dashes are treated as text.
"""

import asyncio
import os
import unittest
from unittest.mock import patch

from claude_codex_bridge.bridge_server import invoke_codex_cli


class DummyProcess:
    def __init__(self, returncode: int = 0, stdout: bytes = b"ok", stderr: bytes = b""):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self):
        return self._stdout, self._stderr

    def terminate(self):
        pass

    async def wait(self):
        return

    def kill(self):
        pass


class TestInvocationArgs(unittest.IsolatedAsyncioTestCase):
    async def test_prompt_passed_after_delimiter(self):
        captured_args = {}

        async def fake_subprocess_exec(*cmd, **kwargs):
            captured_args["cmd"] = list(cmd)
            captured_args["cwd"] = kwargs.get("cwd")
            return DummyProcess(returncode=0, stdout=b"done", stderr=b"")

        with patch.object(
            asyncio, "create_subprocess_exec", side_effect=fake_subprocess_exec
        ):
            # Force read-only behavior to avoid write flags complicating the check
            os.environ["CODEX_ALLOW_WRITE"] = "false"

            prompt = "Analyze code"
            stdout, stderr = await invoke_codex_cli(
                prompt=prompt,
                working_directory="/tmp",
                execution_mode="on-failure",
                sandbox_mode="read-only",
                allow_write=False,
            )

            self.assertEqual(stdout, "done")
            self.assertEqual(stderr, "")

            cmd = captured_args["cmd"]
            # Ensure structure includes `--` before prompt
            self.assertIn("--", cmd)
            self.assertEqual(cmd[-2], "--")
            self.assertEqual(cmd[-1], prompt)

    async def test_leading_dash_prompt_is_not_treated_as_flag(self):
        captured_args = {}

        async def fake_subprocess_exec(*cmd, **kwargs):
            captured_args["cmd"] = list(cmd)
            return DummyProcess(returncode=0, stdout=b"ok", stderr=b"")

        with patch.object(
            asyncio, "create_subprocess_exec", side_effect=fake_subprocess_exec
        ):
            os.environ["CODEX_ALLOW_WRITE"] = "false"

            prompt = "-a do something"
            await invoke_codex_cli(
                prompt=prompt,
                working_directory="/tmp",
                execution_mode="on-failure",
                sandbox_mode="read-only",
                allow_write=False,
            )

            cmd = captured_args["cmd"]
            # Verify that the literal prompt with leading dash is the final
            # positional arg
            self.assertIn("--", cmd)
            self.assertEqual(cmd[-1], prompt)


if __name__ == "__main__":
    unittest.main()

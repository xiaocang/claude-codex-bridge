"""Tests for default timeout configuration in Codex CLI invocation."""

import asyncio
import os
import tempfile
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

    def terminate(self):  # pragma: no cover - simple stub
        pass

    async def wait(self):  # pragma: no cover - simple stub
        return

    def kill(self):  # pragma: no cover - simple stub
        pass


class TestDefaultTimeout(unittest.IsolatedAsyncioTestCase):
    async def test_default_timeout_value(self):
        captured_timeout = {}

        async def fake_wait_for(coro, timeout):
            captured_timeout["timeout"] = timeout
            return await coro

        async def fake_subprocess_exec(*cmd, **kwargs):
            return DummyProcess(returncode=0, stdout=b"done", stderr=b"")

        with patch.object(
            asyncio, "create_subprocess_exec", side_effect=fake_subprocess_exec
        ):
            with patch.object(asyncio, "wait_for", side_effect=fake_wait_for):
                os.environ["CODEX_ALLOW_WRITE"] = "false"
                with tempfile.TemporaryDirectory() as tmpdir:
                    await invoke_codex_cli(
                        prompt="Analyze code",
                        working_directory=tmpdir,
                        execution_mode="on-failure",
                        sandbox_mode="read-only",
                        task_complexity="medium",
                        allow_write=False,
                    )

        self.assertEqual(captured_timeout["timeout"], 3600)


if __name__ == "__main__":
    unittest.main()

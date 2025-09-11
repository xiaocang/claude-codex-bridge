"""Tests for task complexity parameter propagation to Codex CLI."""

import asyncio
import os
import tempfile
import unittest
from unittest.mock import patch

from claude_codex_bridge.bridge_server import codex_delegate


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


class TestTaskComplexity(unittest.IsolatedAsyncioTestCase):
    async def test_task_complexity_flag(self):
        captured_args = {}

        async def fake_subprocess_exec(*cmd, **kwargs):
            captured_args["cmd"] = list(cmd)
            return DummyProcess(returncode=0, stdout=b"done", stderr=b"")

        with patch.dict(os.environ, {"CODEX_BACKEND": "cli"}):
            with patch.object(
                asyncio, "create_subprocess_exec", side_effect=fake_subprocess_exec
            ):
                os.environ["CODEX_ALLOW_WRITE"] = "false"

                with tempfile.TemporaryDirectory() as tmpdir:
                    await codex_delegate(
                        task_description="Analyze code",
                        working_directory=tmpdir,
                        execution_mode="on-failure",
                        sandbox_mode="read-only",
                        output_format="diff",
                        task_complexity="high",
                    )

        cmd = captured_args["cmd"]
        pair_found = any(
            cmd[i] == "-c" and cmd[i + 1] == 'model_reasoning_effort="high"'
            for i in range(len(cmd) - 1)
        )
        self.assertTrue(pair_found)


if __name__ == "__main__":
    unittest.main()

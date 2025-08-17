"""
Unit tests for Delegation Decision Engine
"""

import os
import sys
import tempfile
import unittest

# Must be before imports from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from claude_codex_bridge.engine import DelegationDecisionEngine  # noqa: E402


class TestDelegationDecisionEngine(unittest.TestCase):
    """Delegation Decision Engine test class"""

    def setUp(self):
        """Setup before tests"""
        self.dde = DelegationDecisionEngine()

    def test_should_delegate_returns_true(self):
        """Test should_delegate method returns True"""
        result = self.dde.should_delegate("refactor code")
        self.assertTrue(result)

        result = self.dde.should_delegate("generate tests")
        self.assertTrue(result)

    def test_prepare_codex_prompt_passthrough(self):
        """测试 prepare_codex_prompt 方法透传原始指令"""
        original = "这是一个测试指令"
        result = self.dde.prepare_codex_prompt(original)
        self.assertEqual(result, original)

    def test_validate_working_directory_valid(self):
        """测试工作目录验证 - 有效目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.dde.validate_working_directory(temp_dir)
            self.assertTrue(result)

    def test_validate_working_directory_invalid_relative(self):
        """测试工作目录验证 - 相对路径无效"""
        result = self.dde.validate_working_directory("./relative/path")
        self.assertFalse(result)

    def test_validate_working_directory_nonexistent(self):
        """测试工作目录验证 - 不存在的目录"""
        result = self.dde.validate_working_directory("/nonexistent/directory")
        self.assertFalse(result)

    def test_validate_working_directory_dangerous_paths(self):
        """测试工作目录验证 - 危险路径"""
        dangerous_paths = ["/etc", "/usr/bin", "/bin", "/sbin", "/root"]

        for path in dangerous_paths:
            result = self.dde.validate_working_directory(path)
            self.assertFalse(result, f"危险路径 {path} 应该被拒绝")

    def test_validate_working_directory_similar_prefix_allowed(self):
        """路径名称与敏感目录同前缀但并非其子目录时允许访问"""
        with tempfile.TemporaryDirectory(prefix="etc_tmp_") as temp_dir:
            result = self.dde.validate_working_directory(temp_dir)
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()

"""
测试缓存模块的单元测试
"""

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

# Must be before imports from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from claude_codex_bridge.cache import ResultCache  # noqa: E402


class TestResultCache(unittest.TestCase):
    """结果缓存测试类"""

    def setUp(self):
        """测试前设置"""
        self.cache = ResultCache(ttl=3600, max_size=10)

        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()

        # 创建一些测试文件
        with open(os.path.join(self.temp_dir, "test.py"), "w") as f:
            f.write("print('hello world')")

    def test_cache_key_generation(self):
        """测试缓存键生成"""
        key1 = self.cache._generate_cache_key(
            "task1", "/dir1", "mode1", "sandbox1", "format1", "hash1"
        )
        key2 = self.cache._generate_cache_key(
            "task1", "/dir1", "mode1", "sandbox1", "format1", "hash1"
        )
        key3 = self.cache._generate_cache_key(
            "task2", "/dir1", "mode1", "sandbox1", "format1", "hash1"
        )

        # 相同参数应生成相同键
        self.assertEqual(key1, key2)

        # 不同参数应生成不同键
        self.assertNotEqual(key1, key3)

        # 键应该是固定长度的哈希值
        self.assertEqual(len(key1), 64)  # SHA256 产生 64 字符的十六进制字符串

    def test_directory_hash_calculation(self):
        """测试目录哈希计算"""
        hash1 = self.cache._calculate_directory_hash(self.temp_dir)
        hash2 = self.cache._calculate_directory_hash(self.temp_dir)

        # 相同目录内容应产生相同哈希
        self.assertEqual(hash1, hash2)

        # 修改文件内容
        with open(os.path.join(self.temp_dir, "test.py"), "a") as f:
            f.write("\n# modified")

        hash3 = self.cache._calculate_directory_hash(self.temp_dir)

        # 修改后应产生不同哈希
        self.assertNotEqual(hash1, hash3)

    def test_cache_set_and_get(self):
        """测试缓存存储和获取"""
        # 设置缓存
        self.cache.set(
            "task1", self.temp_dir, "mode1", "sandbox1", "format1", "result1"
        )

        # 获取缓存
        result = self.cache.get("task1", self.temp_dir, "mode1", "sandbox1", "format1")
        self.assertEqual(result, "result1")

        # 获取不存在的缓存
        result = self.cache.get("task2", self.temp_dir, "mode1", "sandbox1", "format1")
        self.assertIsNone(result)

    def test_cache_expiration(self):
        """测试缓存过期"""
        # 创建短期缓存
        short_cache = ResultCache(ttl=1, max_size=10)

        # 模拟时间流逝，避免实际等待
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000
            short_cache.set(
                "task1", self.temp_dir, "mode1", "sandbox1", "format1", "result1"
            )

            # 立即获取应该成功
            result = short_cache.get(
                "task1", self.temp_dir, "mode1", "sandbox1", "format1"
            )
            self.assertEqual(result, "result1")

            # 时间前进，触发过期
            mock_time.return_value = 1002
            result = short_cache.get(
                "task1", self.temp_dir, "mode1", "sandbox1", "format1"
            )
            self.assertIsNone(result)

    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        small_cache = ResultCache(ttl=3600, max_size=2)

        # 添加缓存条目
        small_cache.set(
            "task1", self.temp_dir, "mode1", "sandbox1", "format1", "result1"
        )
        small_cache.set(
            "task2", self.temp_dir, "mode2", "sandbox1", "format1", "result2"
        )

        # 此时缓存应该有2个条目
        self.assertEqual(len(small_cache.cache), 2)

        # 添加第三个条目，应该驱逐最旧的
        small_cache.set(
            "task3", self.temp_dir, "mode3", "sandbox1", "format1", "result3"
        )

        # 缓存仍然应该只有2个条目
        self.assertEqual(len(small_cache.cache), 2)

        # task1 应该被驱逐了
        result = small_cache.get("task1", self.temp_dir, "mode1", "sandbox1", "format1")
        self.assertIsNone(result)

        # task3 应该存在
        result = small_cache.get("task3", self.temp_dir, "mode3", "sandbox1", "format1")
        self.assertEqual(result, "result3")

    def test_cache_stats(self):
        """测试缓存统计"""
        # 添加一些缓存条目
        self.cache.set(
            "task1", self.temp_dir, "mode1", "sandbox1", "format1", "result1"
        )
        self.cache.set(
            "task2", self.temp_dir, "mode2", "sandbox1", "format1", "result2"
        )

        stats = self.cache.get_stats()

        self.assertEqual(stats["total_entries"], 2)
        self.assertEqual(stats["max_size"], 10)
        self.assertEqual(stats["ttl_seconds"], 3600)
        self.assertGreaterEqual(stats["active_entries"], 0)

    def test_cache_cleanup(self):
        """测试缓存清理"""
        # 创建有过期条目的缓存
        expired_cache = ResultCache(ttl=1, max_size=10)

        expired_cache.set(
            "task1", self.temp_dir, "mode1", "sandbox1", "format1", "result1"
        )
        expired_cache.set(
            "task2", self.temp_dir, "mode2", "sandbox1", "format1", "result2"
        )

        # 等待过期
        time.sleep(1.1)

        # 添加新的条目（不过期）
        expired_cache.set(
            "task3", self.temp_dir, "mode3", "sandbox1", "format1", "result3"
        )

        # 清理过期条目
        cleaned_count = expired_cache.cleanup_expired()

        # 应该清理了2个过期条目
        self.assertEqual(cleaned_count, 2)

        # 只剩下1个活跃条目
        self.assertEqual(len(expired_cache.cache), 1)

    def test_cache_clear(self):
        """测试缓存清空"""
        # 添加一些缓存条目
        self.cache.set(
            "task1", self.temp_dir, "mode1", "sandbox1", "format1", "result1"
        )
        self.cache.set(
            "task2", self.temp_dir, "mode2", "sandbox1", "format1", "result2"
        )

        # 确认有条目
        self.assertEqual(len(self.cache.cache), 2)

        # 清空缓存
        self.cache.clear()

        # 确认已清空
        self.assertEqual(len(self.cache.cache), 0)

    def tearDown(self):
        """测试后清理"""
        import shutil

        shutil.rmtree(self.temp_dir)


if __name__ == "__main__":
    unittest.main()

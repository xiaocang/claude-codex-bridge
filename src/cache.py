"""
Cache Module

Provides result caching functionality to improve performance and avoid
duplicate execution of same tasks.
"""

import hashlib
import json
import os
import time
from typing import Any, Dict, Optional


class ResultCache:
    """
    Memory-based result caching system.

    Uses task description, file content hash, and execution parameters to
    generate cache keys,
    avoiding duplicate execution of same Codex tasks.
    """

    def __init__(self, ttl: int = 3600, max_size: int = 100):
        """
        Initialize cache.

        Args:
            ttl: Cache time-to-live in seconds, default 1 hour
            max_size: Maximum cache entries, default 100
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
        self.max_size = max_size

    def _generate_cache_key(
        self,
        task_description: str,
        working_directory: str,
        execution_mode: str,
        sandbox_mode: str,
        output_format: str,
        files_hash: Optional[str] = None,
    ) -> str:
        """
        Generate cache key.

        Generate a unique cache key based on task parameters and file content.

        Args:
            task_description: Task description
            working_directory: Working directory
            execution_mode: Execution mode
            sandbox_mode: Sandbox mode
            output_format: Output format
            files_hash: File content hash value

        Returns:
            Generated cache key
        """
        # Build cache key string
        cache_data = {
            "task": task_description,
            "directory": working_directory,
            "exec_mode": execution_mode,
            "sandbox_mode": sandbox_mode,
            "output_format": output_format,
            "files_hash": files_hash or "none",
        }

        # Serialize to JSON string (ensuring consistent order)
        cache_string = json.dumps(cache_data, sort_keys=True)

        # Generate SHA256 hash
        return hashlib.sha256(cache_string.encode("utf-8")).hexdigest()

    def _calculate_directory_hash(self, directory: str) -> str:
        """
        Calculate the content hash of all files in a directory.

        Args:
            directory: The directory path to calculate the hash for

        Returns:
            The hash value of the directory content
        """
        try:
            file_hashes = []

            # Iterate over all files in the directory
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories and common ignored directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not d.startswith(".")
                    and d not in ["node_modules", "__pycache__", ".git"]
                ]

                for file in sorted(files):
                    # Skip hidden files and binary files
                    if file.startswith(".") or file.endswith(
                        (".pyc", ".so", ".exe", ".bin")
                    ):
                        continue

                    file_path = os.path.join(root, file)

                    try:
                        # Read file content and calculate hash
                        with open(file_path, "rb") as f:
                            file_content = f.read()
                            file_hash = hashlib.md5(
                                file_content, usedforsecurity=False
                            ).hexdigest()  # noqa: S324
                            relative_path = os.path.relpath(file_path, directory)
                            file_hashes.append(f"{relative_path}:{file_hash}")
                    except (IOError, OSError):
                        # Skip files that cannot be read
                        continue

            # Generate directory hash based on all file hashes
            combined = "|".join(file_hashes)
            return hashlib.sha256(combined.encode("utf-8")).hexdigest()

        except Exception:
            # If calculation fails, return a timestamp as a fallback
            return str(int(time.time()))

    def get(
        self,
        task_description: str,
        working_directory: str,
        execution_mode: str,
        sandbox_mode: str,
        output_format: str,
    ) -> Optional[str]:
        """
        Get result from cache.

        Args:
            task_description: Task description
            working_directory: Working directory
            execution_mode: Execution mode
            sandbox_mode: Sandbox mode
            output_format: Output format

        Returns:
            Cached result (JSON string), or None if it does not exist
        """
        # Calculate file hash (to detect file changes)
        files_hash = self._calculate_directory_hash(working_directory)

        # Generate cache key
        cache_key = self._generate_cache_key(
            task_description,
            working_directory,
            execution_mode,
            sandbox_mode,
            output_format,
            files_hash,
        )

        # Check if cache exists
        if cache_key not in self.cache:
            return None

        cache_entry = self.cache[cache_key]

        # Check if expired
        if time.time() - cache_entry["timestamp"] > self.ttl:
            # Delete expired entry
            del self.cache[cache_key]
            return None

        # Update access time (LRU)
        cache_entry["last_accessed"] = time.time()

        return str(cache_entry["result"])

    def set(
        self,
        task_description: str,
        working_directory: str,
        execution_mode: str,
        sandbox_mode: str,
        output_format: str,
        result: str,
    ) -> None:
        """
        Store result in cache.

        Args:
            task_description: Task description
            working_directory: Working directory
            execution_mode: Execution mode
            sandbox_mode: Sandbox mode
            output_format: Output format
            result: The result to be cached (JSON string)
        """
        # Calculate file hash
        files_hash = self._calculate_directory_hash(working_directory)

        # Generate cache key
        cache_key = self._generate_cache_key(
            task_description,
            working_directory,
            execution_mode,
            sandbox_mode,
            output_format,
            files_hash,
        )

        # If cache is full, delete the oldest entry (LRU)
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        # Store in cache
        current_time = time.time()
        self.cache[cache_key] = {
            "result": result,
            "timestamp": current_time,
            "last_accessed": current_time,
            "task_description": (
                task_description[:100] + "..."
                if len(task_description) > 100
                else task_description
            ),
        }

    def _evict_oldest(self) -> None:
        """Delete the least recently used cache entry (LRU policy)."""
        if not self.cache:
            return

        # Find the least recently used entry
        oldest_key = min(
            self.cache.keys(), key=lambda k: self.cache[k]["last_accessed"]
        )

        del self.cache[oldest_key]

    def clear(self) -> None:
        """Clear all cache."""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            A dictionary containing cache statistics
        """
        current_time = time.time()
        expired_count = sum(
            1
            for entry in self.cache.values()
            if current_time - entry["timestamp"] > self.ttl
        )

        return {
            "total_entries": len(self.cache),
            "expired_entries": expired_count,
            "active_entries": len(self.cache) - expired_count,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl,
            "oldest_entry_age": (
                current_time - min(entry["timestamp"] for entry in self.cache.values())
                if self.cache
                else 0
            ),
        }

    def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key
            for key, entry in self.cache.items()
            if current_time - entry["timestamp"] > self.ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

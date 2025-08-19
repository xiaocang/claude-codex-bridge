"""
Delegation Decision Engine (DDE)

Responsible for analyzing tasks and deciding whether and how to delegate to Codex CLI.
"""

import os


class DelegationDecisionEngine:
    """
    Analyzes tasks and decides whether and how to delegate to Codex CLI.
    """

    def __init__(self) -> None:
        pass

    def should_delegate(self, task_description: str) -> bool:
        """
        Determine whether to delegate based on task description.

        V1 version: Always delegates, no filtering.
        V2 version: Can introduce keyword analysis, task complexity assessment, etc.

        Args:
            task_description: Task description

        Returns:
            Whether should delegate to Codex CLI
        """
        # V1: Simple implementation - always delegate
        # Future: Can add keyword checking, task complexity analysis, etc.
        return True

    def prepare_codex_prompt(self, task_description: str) -> str:
        """
        Preprocess original task description to generate instructions more
        suitable for Codex.

        V1 version: Direct passthrough of original description.
        V2 version: Can convert natural language requests to more structured,
        explicit instruction sets.

        Args:
            task_description: Original task description

        Returns:
            Processed Codex instruction
        """
        # V1: Direct passthrough
        return task_description

    def validate_working_directory(self, directory: str) -> bool:
        """
        Validate if the working directory is safe and valid.

        Args:
            directory: The directory path to validate

        Returns:
            Whether the directory is valid and safe
        """
        # Ensure it is an absolute path
        if not os.path.isabs(directory):
            return False

        # Ensure the directory exists
        if not os.path.exists(directory):
            return False

        # Ensure it is a directory and not a file
        if not os.path.isdir(directory):
            return False

        # Basic security check - prevent access to sensitive system directories
        dangerous_paths = ["/etc", "/usr/bin", "/bin", "/sbin", "/root"]
        normalized_path = os.path.realpath(directory)

        for dangerous in dangerous_paths:
            dangerous_real = os.path.realpath(dangerous)
            try:
                if (
                    os.path.commonpath([normalized_path, dangerous_real])
                    == dangerous_real
                ):
                    return False
            except ValueError:
                # Paths are on different drives or otherwise incomparable; skip
                continue

        return True

"""Tests for wrapper-style delimiter extraction functionality."""

import unittest

from src.claude_codex_bridge.bridge_server import (
    _extract_wrapped_content,
    parse_codex_output,
)


class TestWrappedDelimiterExtraction(unittest.TestCase):
    """Test wrapper-style delimiter extraction."""

    def test_normal_extraction(self):
        """Test normal case with wrapped content."""
        text = (
            "Some preamble text\n--[=[\nThis is the content\n"
            "Multiple lines\n]=]--\nSome trailing text"
        )
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertEqual(result, "\nThis is the content\nMultiple lines\n")

    def test_no_delimiters(self):
        """Test when no delimiters are present."""
        text = "Just some plain text without any delimiters"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertIsNone(result)

    def test_only_start_delimiter(self):
        """Test when only start delimiter is present."""
        text = "Some text\n--[=[\nContent after start\nBut no end delimiter"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertIsNone(result)

    def test_only_end_delimiter(self):
        """Test when only end delimiter is present."""
        text = "Some text\nContent before end\n]=]--\nTrailing text"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertIsNone(result)

    def test_multiple_start_delimiters(self):
        """Test multiple start delimiters - should use first (greedy)."""
        text = "Preamble\n--[=[\nFirst content\n--[=[\nNested content\n]=]--\nTrailing"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertEqual(result, "\nFirst content\n--[=[\nNested content\n")

    def test_multiple_end_delimiters(self):
        """Test when multiple end delimiters are present - should use last (greedy)."""
        text = "Preamble\n--[=[\nContent with\n]=]--\nmore text\n]=]--\nTrailing"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertEqual(result, "\nContent with\n]=]--\nmore text\n")

    def test_empty_content(self):
        """Test when delimiters contain empty content."""
        text = "Preamble\n--[=[]=]--\nTrailing"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertEqual(result, "")

    def test_whitespace_handling(self):
        """Test whitespace around delimiters."""
        text = "Preamble\n  --[=[  \n  Content with spaces  \n  ]=]--  \nTrailing"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertEqual(result, "  \n  Content with spaces  \n  ")

    def test_custom_delimiters(self):
        """Test with different delimiter patterns."""
        text = "Before\n<<<START>>>\nWrapped content\n<<<END>>>\nAfter"
        result = _extract_wrapped_content(text, "<<<START>>>", "<<<END>>>")
        self.assertEqual(result, "\nWrapped content\n")

    def test_single_line_content(self):
        """Test with single line content."""
        text = "Before --[=[ Single line content ]=]-- After"
        result = _extract_wrapped_content(text, "--[=[", "]=]--")
        self.assertEqual(result, " Single line content ")


class TestParseCodexOutputWithWrapperDelimiters(unittest.TestCase):
    """Test parse_codex_output with new wrapper delimiter functionality."""

    def test_parse_with_wrapped_delimiters(self):
        """Test parsing with wrapper delimiters."""
        stdout = """
        Some reasoning and process output here.

        --[=[
        def hello():
            return "Hello World"
        ]=]--

        Additional trailing output.
        """
        result = parse_codex_output(
            stdout, "diff", start_delimiter="--[=[", end_delimiter="]=]--", strict=True
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("def hello():", result["content"])
        self.assertNotIn("reasoning and process", result["content"])
        self.assertNotIn("Additional trailing", result["content"])

    def test_parse_missing_delimiters_strict(self):
        """Test strict mode when delimiters are missing."""
        stdout = "Just some output without delimiters"
        result = parse_codex_output(
            stdout, "diff", start_delimiter="--[=[", end_delimiter="]=]--", strict=True
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "final_output_delimiter_missing")

    def test_parse_missing_delimiters_non_strict(self):
        """Test non-strict mode when delimiters are missing."""
        stdout = "Just some output without delimiters"
        result = parse_codex_output(
            stdout, "diff", start_delimiter="--[=[", end_delimiter="]=]--", strict=False
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], stdout.strip())

    def test_parse_partial_delimiters_strict(self):
        """Test strict mode when only one delimiter is present."""
        stdout = "Some text\n--[=[\nContent but no end delimiter"
        result = parse_codex_output(
            stdout, "diff", start_delimiter="--[=[", end_delimiter="]=]--", strict=True
        )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "final_output_delimiter_missing")

    def test_backward_compatibility_old_delimiter(self):
        """Test backward compatibility with old single delimiter."""
        stdout = "Reasoning here\n=x=x=x=x=x=x=x=\nActual content here"
        result = parse_codex_output(
            stdout, "diff", delimiter="=x=x=x=x=x=x=x=", strict=True  # Old parameter
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], "Actual content here")

    def test_default_wrapper_delimiters(self):
        """Test using default wrapper delimiters."""
        stdout = """
        Some reasoning and process output here.

        --[=[
        def hello():
            return "Hello World"
        ]=]--

        Additional trailing output.
        """
        result = parse_codex_output(stdout, "diff", strict=True)

        self.assertEqual(result["status"], "success")
        self.assertIn("def hello():", result["content"])
        self.assertNotIn("reasoning and process", result["content"])

    def test_content_type_detection(self):
        """Test that content type detection works on extracted content."""
        stdout = """
        This is reasoning text that should be ignored.

        --[=[
        --- a/test.py
        +++ b/test.py
        @@ -1,3 +1,3 @@
         def test():
        -    return "old"
        +    return "new"
        ]=]--

        More trailing content.
        """
        result = parse_codex_output(stdout, "diff", strict=True)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["detected_type"], "diff")
        self.assertIn("--- a/test.py", result["content"])
        self.assertNotIn("reasoning text", result["content"])


if __name__ == "__main__":
    unittest.main()

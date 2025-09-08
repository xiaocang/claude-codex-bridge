import os
import unittest
from unittest.mock import patch

from claude_codex_bridge.bridge_server import FINAL_OUTPUT_DELIMITER, parse_codex_output


class TestDelimiterStrictMode(unittest.TestCase):
    def test_strict_mode_errors_when_missing_delimiter(self):
        raw = "Model output without the delimiter."
        # Ensure default strict is enabled (true)
        if "FINAL_OUTPUT_STRICT" in os.environ:
            del os.environ["FINAL_OUTPUT_STRICT"]

        result = parse_codex_output(raw, output_format="explanation")
        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("error_type"), "final_output_delimiter_missing")

    def test_can_disable_strict_mode_via_parameter(self):
        raw = "No delimiter present here either."
        result = parse_codex_output(raw, output_format="explanation", strict=False)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("content"), raw)


if __name__ == "__main__":
    unittest.main()

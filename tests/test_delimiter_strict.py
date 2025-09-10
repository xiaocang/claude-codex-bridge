import unittest

from claude_codex_bridge.bridge_server import parse_codex_output


class TestDelimiterStrictMode(unittest.TestCase):
    def test_default_non_strict_when_missing_delimiter(self):
        raw = "Model output without the delimiter."
        # Default strict mode should be disabled; expect success with original content
        result = parse_codex_output(raw, output_format="explanation")
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("content"), raw)

    def test_can_enable_strict_mode_via_parameter(self):
        raw = "No delimiter present here either."
        result = parse_codex_output(raw, output_format="explanation", strict=True)
        self.assertEqual(result.get("status"), "error")
        self.assertEqual(result.get("error_type"), "final_output_delimiter_missing")


if __name__ == "__main__":
    unittest.main()

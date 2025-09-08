import unittest

from claude_codex_bridge.bridge_server import FINAL_OUTPUT_DELIMITER, parse_codex_output


class TestDelimiterExtraction(unittest.TestCase):
    def test_extracts_content_after_delimiter(self):
        before = "Some system logs or reasoning...\nMore content above\n"
        after = "This is the deliverable body.\nWith multiple lines.\n"
        raw = before + FINAL_OUTPUT_DELIMITER + "\n" + after

        result = parse_codex_output(raw, output_format="explanation")

        self.assertEqual(result["status"], "success")
        self.assertIn("deliverable body", result["content"])  # sanity check
        self.assertTrue(result["content"].startswith("This is the deliverable body."))

    def test_returns_original_when_delimiter_missing(self):
        raw = "No delimiter present here."
        result = parse_codex_output(raw, output_format="explanation")
        self.assertEqual(result["content"], raw)

    def test_custom_delimiter_parameter(self):
        custom_delimiter = "###CUSTOM###"
        before = "Some content before delimiter\n"
        after = "This is the deliverable content with custom delimiter."
        raw = before + custom_delimiter + "\n" + after

        result = parse_codex_output(
            raw, output_format="explanation", delimiter=custom_delimiter
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(result["content"].startswith("This is the deliverable content"))
        self.assertNotIn(before.strip(), result["content"])

    def test_strict_parameter_override(self):
        raw = "Content without any delimiter."

        # Test strict=True (should error)
        result_strict = parse_codex_output(
            raw, output_format="explanation", strict=True
        )
        self.assertEqual(result_strict["status"], "error")
        self.assertEqual(result_strict["error_type"], "final_output_delimiter_missing")

        # Test strict=False (should succeed)
        result_not_strict = parse_codex_output(
            raw, output_format="explanation", strict=False
        )
        self.assertEqual(result_not_strict["status"], "success")
        self.assertEqual(result_not_strict["content"], raw)

    def test_both_delimiter_and_strict_parameters(self):
        custom_delimiter = "<<<END>>>"
        before = "Pre-delimiter content\n"
        after = "Post-delimiter deliverable content."
        raw = before + custom_delimiter + "\n" + after

        result = parse_codex_output(
            raw, output_format="explanation", delimiter=custom_delimiter, strict=True
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["content"], "Post-delimiter deliverable content.")

        # Test with wrong delimiter but strict=False
        wrong_raw = "Content with wrong delimiter ===WRONG==="
        result_wrong = parse_codex_output(
            wrong_raw,
            output_format="explanation",
            delimiter=custom_delimiter,
            strict=False,
        )

        self.assertEqual(result_wrong["status"], "success")
        self.assertEqual(result_wrong["content"], wrong_raw)


if __name__ == "__main__":
    unittest.main()

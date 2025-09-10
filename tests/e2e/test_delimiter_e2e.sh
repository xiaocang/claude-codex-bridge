#!/bin/bash

# E2E test for wrapper-style delimiter extraction
# This test verifies that the MCP server correctly extracts content from Codex output
# using wrapper delimiters and handles various scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$TEST_DIR/../.." && pwd)"
TEMP_DIR=$(mktemp -d)
LOG_FILE="$TEMP_DIR/test.log"

# Cleanup function
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    rm -rf "$TEMP_DIR"
    if [[ -n $MCP_PID ]]; then
        kill $MCP_PID 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG_FILE"
    echo -e "$*"
}

log_success() {
    log "${GREEN}✓ $*${NC}"
}

log_error() {
    log "${RED}✗ $*${NC}"
}

log_info() {
    log "${YELLOW}ℹ $*${NC}"
}

# Test helper functions
assert_contains() {
    local actual="$1"
    local expected="$2"
    local test_name="$3"

    if [[ "$actual" == *"$expected"* ]]; then
        log_success "$test_name: Contains expected content"
        return 0
    else
        log_error "$test_name: Expected content not found"
        log_error "Expected: $expected"
        log_error "Actual: $actual"
        return 1
    fi
}

assert_not_contains() {
    local actual="$1"
    local unexpected="$2"
    local test_name="$3"

    if [[ "$actual" != *"$unexpected"* ]]; then
        log_success "$test_name: Does not contain unexpected content"
        return 0
    else
        log_error "$test_name: Found unexpected content"
        log_error "Unexpected: $unexpected"
        log_error "Actual: $actual"
        return 1
    fi
}

# Test wrapper delimiter extraction
test_wrapper_delimiter_extraction() {
    log_info "Testing wrapper delimiter extraction..."

    # Create a mock Codex response with wrapper delimiters
local mock_response=$(cat <<'EOF'
Some reasoning and process output here.
This should be filtered out.

--[=[
def hello_world():
    return "Hello from Codex!"

# This is the actual deliverable content
print(hello_world())
]=]--

Additional trailing content that should be ignored.
More reasoning that should not appear in final output.
EOF
)

    # Create a temporary Python script to test the parsing
    cat > "$TEMP_DIR/test_parsing.py" << EOF
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from claude_codex_bridge.bridge_server import parse_codex_output

# Test the parsing function directly
mock_output = '''$mock_response'''

result = parse_codex_output(
    mock_output,
    "diff",
    start_delimiter="--[=[",
    end_delimiter="]=]--",
    strict=True
)

print("Status:", result["status"])
print("Content:", repr(result["content"]))
EOF

    # Run the parsing test
    cd "$PROJECT_ROOT"
    local parse_result=$(uv run python "$TEMP_DIR/test_parsing.py" 2>&1)

    # Verify parsing results
    assert_contains "$parse_result" "Status: success" "Wrapper delimiter parsing"
    assert_contains "$parse_result" "def hello_world():" "Extracted content contains function"
    assert_contains "$parse_result" "Hello from Codex!" "Extracted content contains string"
    assert_not_contains "$parse_result" "reasoning and process" "Filtered out reasoning"
    assert_not_contains "$parse_result" "Additional trailing" "Filtered out trailing content"
}

# Test strict mode error handling
test_strict_mode_error() {
    log_info "Testing strict mode error handling..."

    # Create a mock response without delimiters
    local mock_response_no_delims="Just some output without any delimiters.
This should trigger an error in strict mode."

    # Create a temporary Python script to test strict mode
    cat > "$TEMP_DIR/test_strict.py" << EOF
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from claude_codex_bridge.bridge_server import parse_codex_output

mock_output = '''$mock_response_no_delims'''

result = parse_codex_output(
    mock_output,
    "diff",
    start_delimiter="--[=[",
    end_delimiter="]=]--",
    strict=True
)

print("Status:", result["status"])
print("Error type:", result.get("error_type", "None"))
print("Message:", result.get("message", "None"))
EOF

    # Run the strict mode test
    cd "$PROJECT_ROOT"
    local strict_result=$(uv run python "$TEMP_DIR/test_strict.py" 2>&1)

    # Verify strict mode results
    assert_contains "$strict_result" "Status: error" "Strict mode returns error"
    assert_contains "$strict_result" "final_output_delimiter_missing" "Correct error type"
}

# Test non-strict mode fallback
test_non_strict_fallback() {
    log_info "Testing non-strict mode fallback..."

    # Create a mock response without delimiters
    local mock_response_no_delims="Output without delimiters should be returned as-is."

    # Create a temporary Python script to test non-strict mode
    cat > "$TEMP_DIR/test_non_strict.py" << EOF
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from claude_codex_bridge.bridge_server import parse_codex_output

mock_output = '''$mock_response_no_delims'''

result = parse_codex_output(
    mock_output,
    "diff",
    start_delimiter="--[=[",
    end_delimiter="]=]--",
    strict=False
)

print("Status:", result["status"])
print("Content:", repr(result["content"]))
EOF

    # Run the non-strict mode test
    cd "$PROJECT_ROOT"
    local non_strict_result=$(uv run python "$TEMP_DIR/test_non_strict.py" 2>&1)

    # Verify non-strict mode results
    assert_contains "$non_strict_result" "Status: success" "Non-strict mode succeeds"
    assert_contains "$non_strict_result" "Output without delimiters" "Original content returned"
}

# Test custom delimiters
test_custom_delimiters() {
    log_info "Testing custom delimiters..."

    # Create a mock response with custom delimiters
    local mock_response="Reasoning here.

<<<START>>>
Custom delimiter content here.
Multiple lines work too.
<<<END>>>

More content after."

    # Create a temporary Python script to test custom delimiters
    cat > "$TEMP_DIR/test_custom.py" << EOF
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from claude_codex_bridge.bridge_server import parse_codex_output

mock_output = '''$mock_response'''

result = parse_codex_output(
    mock_output,
    "diff",
    start_delimiter="<<<START>>>",
    end_delimiter="<<<END>>>",
    strict=True
)

print("Status:", result["status"])
print("Content:", repr(result["content"]))
EOF

    # Run the custom delimiter test
    cd "$PROJECT_ROOT"
    local custom_result=$(uv run python "$TEMP_DIR/test_custom.py" 2>&1)

    # Verify custom delimiter results
    assert_contains "$custom_result" "Status: success" "Custom delimiters work"
    assert_contains "$custom_result" "Custom delimiter content" "Extracted custom content"
    assert_not_contains "$custom_result" "Reasoning here" "Filtered reasoning with custom delimiters"
}

# Test backward compatibility with single delimiter
test_backward_compatibility() {
    log_info "Testing backward compatibility with single delimiter..."

    # Create a mock response with old-style single delimiter
    local mock_response="Some reasoning here.
=x=x=x=x=x=x=x=
Final content after single delimiter.
This should all be included."

    # Create a temporary Python script to test backward compatibility
    cat > "$TEMP_DIR/test_backward.py" << EOF
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from claude_codex_bridge.bridge_server import parse_codex_output

mock_output = '''$mock_response'''

result = parse_codex_output(
    mock_output,
    "diff",
    delimiter="=x=x=x=x=x=x=x=",
    strict=True
)

print("Status:", result["status"])
print("Content:", repr(result["content"]))
EOF

    # Run the backward compatibility test
    cd "$PROJECT_ROOT"
    local backward_result=$(uv run python "$TEMP_DIR/test_backward.py" 2>&1)

    # Verify backward compatibility results
    assert_contains "$backward_result" "Status: success" "Backward compatibility works"
    assert_contains "$backward_result" "Final content after" "Single delimiter extraction"
    assert_not_contains "$backward_result" "Some reasoning" "Filtered reasoning with single delimiter"
}

# Test content type detection on extracted content
test_content_type_detection() {
    log_info "Testing content type detection on extracted content..."

    # Create a mock response with diff content inside delimiters
    local mock_response="This is reasoning that should be ignored.

--[=[
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 def test():
-    return \"old\"
+    return \"new\"
]=]--

More trailing content."

    # Create a temporary Python script to test content type detection
    cat > "$TEMP_DIR/test_detection.py" << EOF
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from claude_codex_bridge.bridge_server import parse_codex_output

mock_output = '''$mock_response'''

result = parse_codex_output(
    mock_output,
    "diff",
    start_delimiter="--[=[",
    end_delimiter="]=]--",
    strict=True
)

print("Status:", result["status"])
print("Type:", result["detected_type"])
print("Content contains diff:", "--- a/test.py" in result["content"])
EOF

    # Run the content type detection test
    cd "$PROJECT_ROOT"
    local detection_result=$(uv run python "$TEMP_DIR/test_detection.py" 2>&1)

    # Verify content type detection results
    assert_contains "$detection_result" "Status: success" "Content type detection works"
    assert_contains "$detection_result" "Type: diff" "Detected diff type correctly"
    assert_contains "$detection_result" "Content contains diff: True" "Diff content extracted"
}

# Main test execution
main() {
    log_info "Starting E2E tests for wrapper-style delimiter extraction"
    log_info "Test directory: $TEMP_DIR"
    log_info "Log file: $LOG_FILE"

    cd "$PROJECT_ROOT"

    # Check prerequisites
    if ! command -v uv >/dev/null 2>&1; then
        log_error "uv is not installed or not in PATH"
        exit 1
    fi

    # Run tests
    local failed_tests=0
    local total_tests=6

    test_wrapper_delimiter_extraction || ((failed_tests++))
    test_strict_mode_error || ((failed_tests++))
    test_non_strict_fallback || ((failed_tests++))
    test_custom_delimiters || ((failed_tests++))
    test_backward_compatibility || ((failed_tests++))
    test_content_type_detection || ((failed_tests++))

    # Summary
    local passed_tests=$((total_tests - failed_tests))
    log_info "Test Results:"
    log_success "$passed_tests/$total_tests tests passed"

    if [[ $failed_tests -gt 0 ]]; then
        log_error "$failed_tests/$total_tests tests failed"
        log_info "Check log file for details: $LOG_FILE"
        exit 1
    else
        log_success "All tests passed! 🎉"
        exit 0
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

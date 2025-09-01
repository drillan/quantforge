#!/bin/bash
# Run all tests and generate report

set -e

echo "=== QuantForge Test Suite ==="
echo "Date: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo "=== Running Core Tests ==="
cd core
if cargo test --all 2>&1 | tee ../core_test_results.txt; then
    echo -e "${GREEN}✓ Core tests passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Core tests failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Run ignored tests (slow tests)
echo ""
echo "=== Running Core Slow Tests ==="
if cargo test --all -- --ignored 2>&1 | tee -a ../core_test_results.txt; then
    echo -e "${GREEN}✓ Core slow tests passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Core slow tests failed (non-critical)${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
cd ..

echo ""
echo "=== Running Python Unit Tests ==="
if uv run pytest tests/unit/ -v --tb=short 2>&1 | tee python_unit_test_results.txt; then
    echo -e "${GREEN}✓ Python unit tests passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Python unit tests failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "=== Running Python Integration Tests ==="
if uv run pytest tests/integration/ -v --tb=short 2>&1 | tee python_integration_test_results.txt; then
    echo -e "${GREEN}✓ Python integration tests passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Python integration tests failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "=== Running Python Property Tests ==="
if uv run pytest tests/property/ -v --tb=short 2>&1 | tee python_property_test_results.txt; then
    echo -e "${GREEN}✓ Python property tests passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Python property tests failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "=== Running E2E Tests ==="
if uv run pytest tests/e2e/ -v --tb=short 2>&1 | tee e2e_test_results.txt; then
    echo -e "${GREEN}✓ E2E tests passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ E2E tests failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "=== Running Benchmarks ==="
cd core
if cargo bench --no-run 2>&1 | tee -a ../benchmark_results.txt; then
    echo -e "${GREEN}✓ Benchmarks compiled${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Benchmarks failed to compile${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
cd ..

echo ""
echo "=== Quality Checks ==="

# Python quality
echo "Running ruff..."
if uv run ruff check . 2>&1 | tee ruff_results.txt; then
    echo -e "${GREEN}✓ Ruff check passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Ruff found issues${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo "Running mypy..."
if uv run mypy python/ 2>&1 | tee mypy_results.txt; then
    echo -e "${GREEN}✓ Type checking passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Type checking found issues${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Rust quality
echo "Running cargo fmt check..."
cd core
if cargo fmt -- --check 2>&1 | tee -a ../rust_format_results.txt; then
    echo -e "${GREEN}✓ Rust formatting correct${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Rust formatting issues${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo "Running cargo clippy..."
if cargo clippy --all-targets --all-features -- -D warnings 2>&1 | tee -a ../rust_clippy_results.txt; then
    echo -e "${GREEN}✓ Clippy check passed${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}⚠ Clippy found issues${NC}"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))
cd ..

echo ""
echo "======================================="
echo "           TEST SUMMARY                "
echo "======================================="
echo -e "Total:   $TOTAL_TESTS"
echo -e "Passed:  ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:  ${RED}$FAILED_TESTS${NC}"
echo -e "Success Rate: $((PASSED_TESTS * 100 / TOTAL_TESTS))%"
echo "======================================="

# Generate markdown report
echo "Generating TEST_REPORT.md..."
python scripts/generate_test_report.py

if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}Some tests failed. Please review the results.${NC}"
    exit 1
else
    echo -e "${GREEN}All critical tests passed!${NC}"
    exit 0
fi
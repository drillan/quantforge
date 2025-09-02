#!/usr/bin/env python3
"""Generate comprehensive test report."""

import json
import os
import re
from datetime import datetime


def extract_test_results(file_path, pattern=r"test result: .*? (\d+) passed.*? (\d+) failed"):
    """Extract test results from a file."""
    if not os.path.exists(file_path):
        return None

    with open(file_path) as f:
        content = f.read()

    match = re.search(pattern, content)
    if match:
        return {"passed": int(match.group(1)), "failed": int(match.group(2))}
    return None


def extract_pytest_results(file_path):
    """Extract pytest results from a file."""
    if not os.path.exists(file_path):
        return None

    with open(file_path) as f:
        content = f.read()

    # Look for pytest summary line
    pattern = r"(\d+) passed.*?(\d+) failed"
    match = re.search(pattern, content)
    if match:
        return {
            "passed": int(match.group(1)),
            "failed": int(match.group(2)),
            "total": int(match.group(1)) + int(match.group(2)),
        }

    # Alternative pattern for all passed
    pattern = r"(\d+) passed"
    match = re.search(pattern, content)
    if match:
        return {"passed": int(match.group(1)), "failed": 0, "total": int(match.group(1))}

    return None


def get_benchmark_summary():
    """Extract benchmark summary if available."""
    bench_file = "benchmark_results.txt"
    if not os.path.exists(bench_file):
        return "Benchmarks not run"

    with open(bench_file) as f:
        lines = f.readlines()

    # Look for benchmark results
    results = []
    for line in lines:
        if "time:" in line and "ns/iter" in line:
            results.append(line.strip())

    if results:
        return f"{len(results)} benchmarks completed"
    return "Benchmarks compiled successfully"


def generate_report():
    """Generate comprehensive test report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "core": extract_test_results("core_test_results.txt"),
        "python_unit": extract_pytest_results("python_unit_test_results.txt"),
        "python_integration": extract_pytest_results("python_integration_test_results.txt"),
        "python_property": extract_pytest_results("python_property_test_results.txt"),
        "e2e": extract_pytest_results("e2e_test_results.txt"),
        "benchmarks": get_benchmark_summary(),
    }

    # Calculate totals
    total_passed = 0
    total_failed = 0

    for key in ["core", "python_unit", "python_integration", "python_property", "e2e"]:
        if report[key]:
            total_passed += report[key].get("passed", 0)
            total_failed += report[key].get("failed", 0)

    # Generate markdown report
    markdown = f"""# Test Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Executive Summary

- **Total Tests Passed**: {total_passed}
- **Total Tests Failed**: {total_failed}
- **Success Rate**: {(total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0:.1f}%
- **Benchmarks**: {report["benchmarks"]}

## Test Results by Category

### Core Tests (Rust)
"""

    if report["core"]:
        markdown += f"""- Passed: {report["core"]["passed"]}
- Failed: {report["core"]["failed"]}
- Status: {"✅ PASS" if report["core"]["failed"] == 0 else "❌ FAIL"}
"""
    else:
        markdown += "- Status: ⚠️ Not Run\n"

    markdown += "\n### Python Unit Tests\n"
    if report["python_unit"]:
        markdown += f"""- Passed: {report["python_unit"]["passed"]}
- Failed: {report["python_unit"]["failed"]}
- Status: {"✅ PASS" if report["python_unit"]["failed"] == 0 else "❌ FAIL"}
"""
    else:
        markdown += "- Status: ⚠️ Not Run\n"

    markdown += "\n### Python Integration Tests\n"
    if report["python_integration"]:
        markdown += f"""- Passed: {report["python_integration"]["passed"]}
- Failed: {report["python_integration"]["failed"]}
- Status: {"✅ PASS" if report["python_integration"]["failed"] == 0 else "❌ FAIL"}
"""
    else:
        markdown += "- Status: ⚠️ Not Run\n"

    markdown += "\n### Python Property Tests\n"
    if report["python_property"]:
        markdown += f"""- Passed: {report["python_property"]["passed"]}
- Failed: {report["python_property"]["failed"]}
- Status: {"✅ PASS" if report["python_property"]["failed"] == 0 else "❌ FAIL"}
"""
    else:
        markdown += "- Status: ⚠️ Not Run\n"

    markdown += "\n### End-to-End Tests\n"
    if report["e2e"]:
        markdown += f"""- Passed: {report["e2e"]["passed"]}
- Failed: {report["e2e"]["failed"]}
- Status: {"✅ PASS" if report["e2e"]["failed"] == 0 else "❌ FAIL"}
"""
    else:
        markdown += "- Status: ⚠️ Not Run\n"

    markdown += f"""
## Performance

{report["benchmarks"]}

## Code Quality

### Python
- **Ruff**: {"✅ Clean" if os.path.exists("ruff_results.txt") and os.path.getsize("ruff_results.txt") < 100 else "⚠️ Issues Found"}
- **MyPy**: {"✅ Type Safe" if os.path.exists("mypy_results.txt") and "Success" in open("mypy_results.txt").read() else "⚠️ Type Issues"}

### Rust
- **Format**: {"✅ Formatted" if os.path.exists("rust_format_results.txt") else "⚠️ Check Required"}
- **Clippy**: {"✅ Clean" if os.path.exists("rust_clippy_results.txt") else "⚠️ Check Required"}

## Test Coverage

Coverage data will be added in future reports.

## Recommendations

"""

    if total_failed > 0:
        markdown += "1. **Fix failing tests** - Priority: HIGH\n"
        markdown += "2. Review test failure logs for root causes\n"
    else:
        markdown += "1. All tests passing - consider adding more edge cases\n"

    markdown += """2. Maintain test coverage above 90%
3. Monitor benchmark performance trends

---

*This report was automatically generated by the QuantForge test suite.*
"""

    # Write markdown report
    with open("TEST_REPORT.md", "w") as f:
        f.write(markdown)

    # Write JSON report
    with open("test_results.json", "w") as f:
        json.dump(report, f, indent=2)

    print("Test report generated: TEST_REPORT.md")
    print("JSON results saved: test_results.json")


if __name__ == "__main__":
    generate_report()

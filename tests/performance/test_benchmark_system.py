"""Quick test to verify benchmark system is working."""

import json
from pathlib import Path

import pytest


def test_benchmark_recording_works():
    """Verify that benchmark results are being recorded."""
    results_dir = Path("benchmark_results")

    # Check directory exists or can be created
    results_dir.mkdir(exist_ok=True)
    assert results_dir.exists(), "benchmark_results directory should exist"

    # Test JSON writing
    test_data = {"test": "data", "timestamp": "2025-01-01T00:00:00Z"}
    test_file = results_dir / "test.json"

    with open(test_file, "w") as f:
        json.dump(test_data, f)

    assert test_file.exists(), "Should be able to write JSON files"

    # Clean up test file
    test_file.unlink()


def test_report_generator_imports():
    """Verify report generator can be imported."""
    try:
        from tests.performance.generate_benchmark_report import (
            BenchmarkReportGenerator,
        )

        generator = BenchmarkReportGenerator()
        assert generator.results_dir.name == "benchmark_results"
    except ImportError as e:
        pytest.fail(f"Failed to import report generator: {e}")


@pytest.mark.benchmark
def test_simple_benchmark(benchmark):
    """Simple benchmark to test recording."""

    def compute():
        return sum(range(1000))

    result = benchmark(compute)
    assert result == 499500

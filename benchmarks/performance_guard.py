#!/usr/bin/env python3
"""Performance guard for continuous integration.

Checks benchmark results against baseline to prevent performance regressions.
"""

import json
import sys
from pathlib import Path
from typing import Any


class PerformanceGuard:
    """Guards against performance regressions."""

    def __init__(self, baseline_path: Path | None = None, results_path: Path | None = None):
        """Initialize performance guard."""
        base_dir = Path(__file__).parent
        self.baseline_path = baseline_path or (base_dir / "results" / "baseline.json")
        self.results_path = results_path or (base_dir / "results" / "latest.json")

    def check(self, tolerance: float = 0.2) -> tuple[bool, list[str]]:
        """Check performance against baseline.
        
        Args:
            tolerance: Maximum allowed regression (0.2 = 20% slower allowed)
            
        Returns:
            (passed, list of failure messages)
        """
        # For now, return success if baseline doesn't exist
        if not self.baseline_path.exists():
            print(f"Warning: No baseline found at {self.baseline_path}")
            return True, []
        
        if not self.results_path.exists():
            print(f"Warning: No results found at {self.results_path}")
            return True, []
        
        with open(self.baseline_path) as f:
            baseline = json.load(f)
        
        with open(self.results_path) as f:
            results = json.load(f)
        
        failures = []
        
        # Compare metrics
        for test_name, baseline_metrics in baseline.get("metrics", {}).items():
            result_metrics = results.get("metrics", {}).get(test_name, {})
            
            for metric_name, baseline_value in baseline_metrics.items():
                if metric_name in result_metrics:
                    result_value = result_metrics[metric_name]
                    regression = (result_value - baseline_value) / baseline_value
                    
                    if regression > tolerance:
                        failures.append(
                            f"{test_name}.{metric_name}: "
                            f"{result_value:.0f}ns vs baseline {baseline_value:.0f}ns "
                            f"({regression:.1%} regression)"
                        )
        
        return len(failures) == 0, failures


def main() -> None:
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check benchmark performance")
    parser.add_argument("--tolerance", type=float, default=0.2, help="Max allowed regression")
    
    args = parser.parse_args()
    
    guard = PerformanceGuard()
    passed, failures = guard.check(tolerance=args.tolerance)
    
    if passed:
        print("✅ Performance check passed")
        sys.exit(0)
    else:
        print("❌ Performance regressions detected:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)


if __name__ == "__main__":
    main()
"""pytest benchmark configuration and recording.

Provides automatic recording of benchmark results to history.jsonl.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import pytest
import quantforge


class BenchmarkRecorder:
    """Records pytest benchmark results to history.jsonl (simple version)."""
    
    def __init__(self):
        self.results_dir = Path("benchmark_results")
        self.results_dir.mkdir(exist_ok=True)
        self.benchmarks = []
        
    def add_benchmark(self, name: str, stats: Dict[str, Any]) -> None:
        """Add a benchmark result."""
        self.benchmarks.append({
            "name": name,
            "stats": stats
        })
        
    def save_results(self) -> Optional[Dict[str, Any]]:
        """Save benchmark results to history.jsonl and latest.json."""
        if not self.benchmarks:
            return None
            
        record = {
            "version": quantforge.__version__,
            "git_commit": self._get_git_commit(),
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "environment": self._get_environment(),
            "benchmarks": self.benchmarks
        }
        
        # Append to history.jsonl
        history_file = self.results_dir / "history.jsonl"
        with open(history_file, "a") as f:
            f.write(json.dumps(record) + "\n")
        
        # Update latest.json
        latest_file = self.results_dir / "latest.json"
        with open(latest_file, "w") as f:
            json.dump(record, f, indent=2)
            
        return record
    
    def _get_git_commit(self) -> str:
        """Get current git commit hash."""
        try:
            return subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "unknown"
    
    def _get_environment(self) -> Dict[str, Any]:
        """Get environment information."""
        import platform
        try:
            import psutil
            memory_gb = round(psutil.virtual_memory().total / (1024**3), 1)
            cpu_count = psutil.cpu_count(logical=False)
        except ImportError:
            memory_gb = "unknown"
            cpu_count = "unknown"
        
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_count": cpu_count,
            "memory_gb": memory_gb
        }


@pytest.fixture(scope="session")
def benchmark_recorder():
    """Session-scoped benchmark recorder."""
    return BenchmarkRecorder()


def pytest_benchmark_compare_machine_info(config, benchmarksession, machine_info, compared_benchmark):
    """Hook to customize machine info in benchmark output."""
    machine_info['quantforge_version'] = quantforge.__version__
    return machine_info


def pytest_sessionfinish(session, exitstatus):
    """Hook called after all tests have run."""
    # If benchmark tests were run, save results
    if hasattr(session.config, '_benchmarksession'):
        recorder = BenchmarkRecorder()
        
        # Extract benchmark results from the session
        benchmarksession = session.config._benchmarksession
        if benchmarksession and hasattr(benchmarksession, 'benchmarks'):
            for benchmark in benchmarksession.benchmarks:
                recorder.add_benchmark(
                    name=benchmark.name,
                    stats={
                        'min': benchmark.stats.min,
                        'max': benchmark.stats.max,
                        'mean': benchmark.stats.mean,
                        'stddev': benchmark.stats.stddev,
                        'rounds': benchmark.stats.rounds,
                        'iterations': benchmark.stats.iterations if hasattr(benchmark.stats, 'iterations') else None,
                    }
                )
            
            # Save results
            result = recorder.save_results()
            if result:
                print(f"\n✅ Benchmark results saved to benchmark_results/history.jsonl")
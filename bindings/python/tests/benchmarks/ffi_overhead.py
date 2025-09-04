"""FFI呼び出しコスト測定ベンチマーク

Bindings層のオーバーヘッドを測定:
- Python → Rust FFI呼び出しコスト
- 引数マーシャリング時間
- 戻り値変換時間
"""

import contextlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import quantforge as qf


class FFIOverheadBenchmark:
    """FFI呼び出しオーバーヘッドの測定"""

    def __init__(self):
        self.results = []
        self.layer = "bindings/python"

    def benchmark_single_call(self, iterations: int = 100000) -> dict[str, float]:
        """単一呼び出しのオーバーヘッド測定"""

        # テストパラメータ
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2

        # ウォームアップ
        for _ in range(1000):
            qf.black_scholes.call_price(s, k, t, r, sigma)

        # 測定
        times = []
        for _ in range(10):
            start = time.perf_counter()
            for _ in range(iterations // 10):
                qf.black_scholes.call_price(s, k, t, r, sigma)
            end = time.perf_counter()
            times.append((end - start) / (iterations // 10))

        return {
            'mean': float(np.mean(times)),
            'std': float(np.std(times)),
            'min': float(np.min(times)),
            'max': float(np.max(times)),
            'median': float(np.median(times)),
            'iterations': iterations
        }

    def benchmark_argument_marshalling(self) -> dict[str, float]:
        """引数マーシャリングのコスト測定"""

        results = {}

        # 小さい引数セット（5個）
        args_small = (100.0, 100.0, 1.0, 0.05, 0.2)
        start = time.perf_counter()
        for _ in range(100000):
            qf.black_scholes.call_price(*args_small)
        end = time.perf_counter()
        results['args_5'] = (end - start) / 100000

        # より多い引数（Americanオプション想定）
        # 注: 実装されていない場合はスキップ
        try:
            # args_large = (100.0, 100.0, 1.0, 0.05, 0.2, 100)
            # american.call_price(*args_large)
            results['args_6'] = 0.0  # プレースホルダー
        except Exception:
            results['args_6'] = 0.0

        return results

    def benchmark_return_conversion(self) -> dict[str, float]:
        """戻り値変換のコスト測定"""

        results = {}

        # スカラー戻り値
        start = time.perf_counter()
        for _ in range(100000):
            _ = qf.black_scholes.call_price(100.0, 100.0, 1.0, 0.05, 0.2)
        end = time.perf_counter()
        results['scalar_return'] = (end - start) / 100000

        # 構造体戻り値（Greeks）
        start = time.perf_counter()
        for _ in range(10000):
            _ = qf.black_scholes.greeks(100.0, 100.0, 1.0, 0.05, 0.2, True)
        end = time.perf_counter()
        results['struct_return'] = (end - start) / 10000

        return results

    def benchmark_error_handling(self) -> dict[str, float]:
        """エラーハンドリングのオーバーヘッド測定"""

        results = {}

        # 正常ケース
        start = time.perf_counter()
        for _ in range(100000):
            with contextlib.suppress(Exception):
                qf.black_scholes.call_price(100.0, 100.0, 1.0, 0.05, 0.2)
        end = time.perf_counter()
        results['normal_case'] = (end - start) / 100000

        # エラーケース（負の価格）
        error_count = 0
        start = time.perf_counter()
        for _ in range(10000):
            try:
                qf.black_scholes.call_price(-100.0, 100.0, 1.0, 0.05, 0.2)
            except ValueError:
                error_count += 1
        end = time.perf_counter()
        results['error_case'] = (end - start) / 10000
        results['errors_caught'] = error_count

        return results

    def run_all_benchmarks(self) -> dict[str, Any]:
        """全ベンチマークを実行"""

        print("Running FFI Overhead Benchmarks...")

        results = {
            'version': 'v2.0.0',
            'layer': self.layer,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'python_version': self._get_python_version(),
                'quantforge_version': getattr(qf, '__version__', 'unknown')
            },
            'benchmarks': {
                'single_call': self.benchmark_single_call(),
                'argument_marshalling': self.benchmark_argument_marshalling(),
                'return_conversion': self.benchmark_return_conversion(),
                'error_handling': self.benchmark_error_handling()
            }
        }

        return results

    def _get_python_version(self) -> str:
        """Pythonバージョンを取得"""
        import sys
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def save_results(self, results: dict[str, Any]):
        """結果を保存"""

        # 保存先ディレクトリ
        results_dir = Path('benchmark_results/bindings/python')
        results_dir.mkdir(parents=True, exist_ok=True)

        # latest.jsonとして保存
        latest_path = results_dir / 'latest.json'
        with open(latest_path, 'w') as f:
            json.dump(results, f, indent=2)

        # historyにも保存
        history_dir = results_dir / 'history'
        history_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        history_path = history_dir / f'ffi_overhead_{timestamp}.json'
        with open(history_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to {latest_path} and {history_path}")


if __name__ == '__main__':
    benchmark = FFIOverheadBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.save_results(results)

    # サマリー表示
    print("\n=== FFI Overhead Summary ===")
    print(f"Single call overhead: {results['benchmarks']['single_call']['mean']*1e9:.2f} ns")
    print(f"Argument marshalling (5 args): {results['benchmarks']['argument_marshalling']['args_5']*1e9:.2f} ns")
    print(f"Scalar return conversion: {results['benchmarks']['return_conversion']['scalar_return']*1e9:.2f} ns")
    print(f"Struct return conversion: {results['benchmarks']['return_conversion']['struct_return']*1e6:.2f} µs")
    error_overhead = results['benchmarks']['error_handling']['error_case']
    normal_case = results['benchmarks']['error_handling']['normal_case']
    print(f"Error handling overhead: {(error_overhead - normal_case)*1e6:.2f} µs")

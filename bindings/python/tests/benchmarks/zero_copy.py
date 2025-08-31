"""ゼロコピー最適化の検証ベンチマーク

NumPy配列のゼロコピー渡しが正しく動作しているか検証:
- メモリアロケーション回数
- データコピー時間
- 大規模配列での性能
"""

import time
import numpy as np
import quantforge as qf
from typing import Dict, Any
import json
from pathlib import Path
from datetime import datetime
import tracemalloc


class ZeroCopyBenchmark:
    """ゼロコピー最適化の検証"""
    
    def __init__(self):
        self.layer = "bindings/python"
        
    def benchmark_array_passing(self, size: int = 1000000) -> Dict[str, Any]:
        """配列渡しのベンチマーク"""
        
        # テストデータ準備
        spots = np.random.uniform(80, 120, size)
        strikes = np.full(size, 100.0)
        times = np.full(size, 1.0)
        rates = np.full(size, 0.05)
        sigmas = np.random.uniform(0.1, 0.3, size)
        
        results = {}
        
        # C-contiguous配列（最適ケース）
        spots_c = np.ascontiguousarray(spots)
        start = time.perf_counter()
        _ = qf.black_scholes.call_price_batch(
            spots=spots_c,
            strikes=strikes,
            times=times,
            rates=rates,
            sigmas=sigmas
        )
        end = time.perf_counter()
        results['c_contiguous'] = end - start
        
        # F-contiguous配列（列優先）
        spots_f = np.asfortranarray(spots)
        start = time.perf_counter()
        _ = qf.black_scholes.call_price_batch(
            spots=spots_f,
            strikes=strikes,
            times=times,
            rates=rates,
            sigmas=sigmas
        )
        end = time.perf_counter()
        results['f_contiguous'] = end - start
        
        # 非連続配列（ストライド付き）
        spots_strided = spots[::2]  # 1つ飛ばし
        strikes_strided = strikes[::2]
        times_strided = times[::2]
        rates_strided = rates[::2]
        sigmas_strided = sigmas[::2]
        
        start = time.perf_counter()
        _ = qf.black_scholes.call_price_batch(
            spots=spots_strided,
            strikes=strikes_strided,
            times=times_strided,
            rates=rates_strided,
            sigmas=sigmas_strided
        )
        end = time.perf_counter()
        results['strided'] = end - start
        
        results['size'] = size
        results['overhead_ratio'] = results['f_contiguous'] / results['c_contiguous']
        
        return results
    
    def benchmark_memory_allocation(self) -> Dict[str, Any]:
        """メモリアロケーションの測定"""
        
        results = {}
        sizes = [1000, 10000, 100000, 1000000]
        
        for size in sizes:
            # テストデータ
            spots = np.random.uniform(80, 120, size)
            strikes = np.full(size, 100.0)
            times = np.full(size, 1.0)
            rates = np.full(size, 0.05)
            sigmas = np.full(size, 0.2)
            
            # メモリトレース開始
            tracemalloc.start()
            snapshot_before = tracemalloc.take_snapshot()
            
            # バッチ処理実行
            _ = qf.black_scholes.call_price_batch(
                spots=spots,
                strikes=strikes,
                times=times,
                rates=rates,
                sigmas=sigmas
            )
            
            snapshot_after = tracemalloc.take_snapshot()
            tracemalloc.stop()
            
            # メモリ使用量の差分
            top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
            total_allocated = sum(stat.size_diff for stat in top_stats if stat.size_diff > 0)
            
            results[f'size_{size}'] = {
                'allocated_bytes': total_allocated,
                'allocated_mb': total_allocated / (1024 * 1024),
                'per_element_bytes': total_allocated / size if size > 0 else 0
            }
        
        return results
    
    def benchmark_broadcasting(self) -> Dict[str, Any]:
        """Broadcasting性能の測定"""
        
        results = {}
        size = 100000
        
        # テストケース1: 全配列
        spots = np.random.uniform(80, 120, size)
        strikes = np.random.uniform(90, 110, size)
        times = np.random.uniform(0.1, 2.0, size)
        rates = np.random.uniform(0.01, 0.1, size)
        sigmas = np.random.uniform(0.1, 0.3, size)
        
        start = time.perf_counter()
        _ = qf.black_scholes.call_price_batch(
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            sigmas=sigmas
        )
        end = time.perf_counter()
        results['all_arrays'] = end - start
        
        # テストケース2: 一部スカラー
        start = time.perf_counter()
        _ = qf.black_scholes.call_price_batch(
            spots=spots,
            strikes=100.0,  # スカラー
            times=1.0,       # スカラー
            rates=0.05,      # スカラー
            sigmas=sigmas
        )
        end = time.perf_counter()
        results['mixed_scalar'] = end - start
        
        # テストケース3: ほぼスカラー
        start = time.perf_counter()
        _ = qf.black_scholes.call_price_batch(
            spots=spots,
            strikes=100.0,
            times=1.0,
            rates=0.05,
            sigmas=0.2  # 全部スカラー except spots
        )
        end = time.perf_counter()
        results['mostly_scalar'] = end - start
        
        results['speedup_mixed'] = results['all_arrays'] / results['mixed_scalar']
        results['speedup_mostly'] = results['all_arrays'] / results['mostly_scalar']
        
        return results
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """全ベンチマークを実行"""
        
        print("Running Zero-Copy Benchmarks...")
        
        results = {
            'version': 'v2.0.0',
            'layer': self.layer,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'numpy_version': np.__version__
            },
            'benchmarks': {
                'array_passing': self.benchmark_array_passing(),
                'memory_allocation': self.benchmark_memory_allocation(),
                'broadcasting': self.benchmark_broadcasting()
            }
        }
        
        return results
    
    def save_results(self, results: Dict[str, Any]):
        """結果を保存"""
        
        results_dir = Path('benchmark_results/bindings/python')
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # 既存のlatest.jsonがあれば読み込んで追加
        latest_path = results_dir / 'latest.json'
        if latest_path.exists():
            with open(latest_path, 'r') as f:
                existing = json.load(f)
            # zero_copyベンチマークを追加
            existing['benchmarks']['zero_copy'] = results['benchmarks']
            results = existing
        
        with open(latest_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # historyにも保存
        history_dir = results_dir / 'history'
        history_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        history_path = history_dir / f'zero_copy_{timestamp}.json'
        with open(history_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {latest_path} and {history_path}")


if __name__ == '__main__':
    benchmark = ZeroCopyBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.save_results(results)
    
    # サマリー表示
    print("\n=== Zero-Copy Summary ===")
    array_results = results['benchmarks']['array_passing']
    print(f"C-contiguous (optimal): {array_results['c_contiguous']*1000:.2f} ms")
    print(f"F-contiguous overhead: {(array_results['overhead_ratio']-1)*100:.1f}%")
    
    broadcast_results = results['benchmarks']['broadcasting']
    print(f"Broadcasting speedup (mixed): {broadcast_results['speedup_mixed']:.2f}x")
    print(f"Broadcasting speedup (mostly scalar): {broadcast_results['speedup_mostly']:.2f}x")
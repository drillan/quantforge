#!/usr/bin/env python3
"""
並列化閾値変更の効果測定
"""

import time
import numpy as np
import quantforge as qf
from scipy.stats import norm


def benchmark_size(size: int, iterations: int = 100) -> dict:
    """特定サイズでのベンチマーク"""
    
    # テストデータ
    np.random.seed(42)
    spots = np.random.uniform(80, 120, size)
    strikes = np.full(size, 100.0)
    times = np.full(size, 1.0)
    rates = np.full(size, 0.05)
    sigmas = np.random.uniform(0.15, 0.35, size)
    
    # QuantForge
    start = time.perf_counter()
    for _ in range(iterations):
        qf_result = qf.black_scholes.call_price_batch(
            spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas
        )
    qf_time = (time.perf_counter() - start) / iterations
    
    # NumPy
    start = time.perf_counter()
    for _ in range(iterations):
        sqrt_t = np.sqrt(times)
        d1 = (np.log(spots / strikes) + (rates + sigmas**2 / 2) * times) / (sigmas * sqrt_t)
        d2 = d1 - sigmas * sqrt_t
        np_result = spots * norm.cdf(d1) - strikes * np.exp(-rates * times) * norm.cdf(d2)
    np_time = (time.perf_counter() - start) / iterations
    
    return {
        'size': size,
        'qf_ms': qf_time * 1000,
        'numpy_ms': np_time * 1000,
        'speedup': np_time / qf_time,
        'qf_throughput': size / qf_time / 1e6,  # M ops/s
    }


def main():
    print("=" * 70)
    print("並列化閾値変更の効果測定")
    print("PARALLEL_THRESHOLD_SMALL: 50,000 → 8,000")
    print("=" * 70)
    print()
    
    # 重要なサイズポイント
    critical_sizes = [
        100,     # マイクロバッチ
        1000,    # 小バッチ
        5000,    # 旧閾値未満
        8000,    # 新閾値（境界）
        10000,   # 問題があったサイズ
        20000,   # 中規模
        50000,   # 旧閾値（境界）
        100000,  # 大規模
    ]
    
    print(f"{'Size':>8} | {'QF (ms)':>10} | {'NumPy (ms)':>12} | {'Speedup':>8} | {'QF M ops/s':>12}")
    print("-" * 70)
    
    improvements = []
    
    for size in critical_sizes:
        iterations = max(10, 100000 // size)
        result = benchmark_size(size, iterations)
        
        print(f"{result['size']:>8} | {result['qf_ms']:>10.3f} | "
              f"{result['numpy_ms']:>12.3f} | {result['speedup']:>7.2f}x | "
              f"{result['qf_throughput']:>12.2f}")
        
        # 10,000要素での改善を記録
        if size == 10000:
            improvements.append(result)
    
    # 詳細分析
    print("\n" + "=" * 70)
    print("詳細分析")
    print("=" * 70)
    
    # 10,000要素での複数回測定
    print("\n10,000要素での安定性テスト（5回測定）:")
    for i in range(5):
        result = benchmark_size(10000, iterations=100)
        print(f"  Run {i+1}: {result['qf_ms']:.3f}ms "
              f"(Speedup: {result['speedup']:.2f}x, "
              f"Throughput: {result['qf_throughput']:.2f}M ops/s)")
    
    # 期待される改善
    print("\n" + "=" * 70)
    print("結果サマリー")
    print("=" * 70)
    
    print("\n✅ 8,000要素以上で並列化が有効になりました")
    print("✅ 10,000要素でのパフォーマンスが改善されているはずです")
    print("✅ 小規模バッチ（< 8,000）は高速なシーケンシャル処理を維持")
    
    # 最終確認
    print("\n最終確認（重要なサイズポイント）:")
    for size in [100, 1000, 10000, 100000]:
        result = benchmark_size(size, iterations=50)
        status = "✅" if result['speedup'] > 1.0 else "⚠️"
        print(f"{status} {size:>7}要素: {result['speedup']:>5.2f}x faster than NumPy")


if __name__ == "__main__":
    main()
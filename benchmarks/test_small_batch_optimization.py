#!/usr/bin/env python3
"""
小バッチ最適化の効果測定ベンチマーク
"""

import time
import numpy as np
import quantforge as qf
from scipy.stats import norm


def benchmark_batch_size(size: int, iterations: int = 1000) -> dict:
    """特定サイズでのベンチマーク実行"""
    
    # テストデータ生成
    np.random.seed(42)
    spots = np.random.uniform(80, 120, size)
    strikes = np.full(size, 100.0)
    times = np.full(size, 1.0)
    rates = np.full(size, 0.05)
    sigmas = np.random.uniform(0.15, 0.35, size)
    
    # QuantForge実装の測定
    start = time.perf_counter()
    for _ in range(iterations):
        qf_result = qf.black_scholes.call_price_batch(
            spots=spots,
            strikes=strikes,
            times=times,
            rates=rates,
            sigmas=sigmas
        )
    qf_time = (time.perf_counter() - start) / iterations
    
    # NumPy/SciPy実装の測定
    start = time.perf_counter()
    for _ in range(iterations):
        sqrt_t = np.sqrt(times)
        d1 = (np.log(spots / strikes) + (rates + sigmas**2 / 2) * times) / (sigmas * sqrt_t)
        d2 = d1 - sigmas * sqrt_t
        numpy_result = spots * norm.cdf(d1) - strikes * np.exp(-rates * times) * norm.cdf(d2)
    numpy_time = (time.perf_counter() - start) / iterations
    
    # 精度確認（最初の10要素）
    max_diff = np.max(np.abs(qf_result[:10] - numpy_result[:10]))
    
    return {
        'size': size,
        'qf_time_us': qf_time * 1e6,
        'numpy_time_us': numpy_time * 1e6,
        'speedup': numpy_time / qf_time,
        'qf_throughput': size / qf_time,
        'numpy_throughput': size / numpy_time,
        'max_diff': max_diff,
        'accurate': max_diff < 1e-6
    }


def main():
    """メインベンチマーク実行"""
    
    print("=" * 60)
    print("小バッチ最適化ベンチマーク")
    print("=" * 60)
    print()
    
    # ウォームアップ
    print("ウォームアップ中...")
    for _ in range(100):
        benchmark_batch_size(100, iterations=1)
    
    # テストサイズ
    test_sizes = [10, 50, 100, 200, 500, 1000, 2000, 5000, 10000]
    
    print("\n結果:")
    print("-" * 60)
    print(f"{'Size':>8} | {'QF (μs)':>10} | {'NumPy (μs)':>10} | {'Speedup':>8} | {'Accurate':>8}")
    print("-" * 60)
    
    results = []
    for size in test_sizes:
        # サイズに応じて反復回数を調整
        iterations = max(100, 10000 // size)
        
        result = benchmark_batch_size(size, iterations)
        results.append(result)
        
        print(f"{result['size']:>8} | {result['qf_time_us']:>10.2f} | {result['numpy_time_us']:>10.2f} | "
              f"{result['speedup']:>8.2f}x | {'✓' if result['accurate'] else '✗':>8}")
    
    # 100件バッチの詳細分析
    print("\n" + "=" * 60)
    print("100件バッチの詳細分析")
    print("=" * 60)
    
    result_100 = next((r for r in results if r['size'] == 100), None)
    if result_100:
        print(f"QuantForge: {result_100['qf_time_us']:.2f}μs")
        print(f"NumPy: {result_100['numpy_time_us']:.2f}μs")
        print(f"Speedup: {result_100['speedup']:.2f}x")
        print(f"Throughput: {result_100['qf_throughput']:.0f} ops/s")
        
        # 旧データとの比較（既知の値）
        old_qf_time = 12.29  # μs (旧実装)
        old_numpy_time = 80.04  # μs
        
        print(f"\n旧実装との比較:")
        print(f"旧QuantForge: {old_qf_time:.2f}μs")
        print(f"新QuantForge: {result_100['qf_time_us']:.2f}μs")
        print(f"改善率: {(old_qf_time - result_100['qf_time_us']) / old_qf_time * 100:.1f}%")
        
        print(f"\nNumPy比:")
        print(f"旧実装: {old_numpy_time / old_qf_time:.2f}x")
        print(f"新実装: {result_100['speedup']:.2f}x")
    
    # グラフ作成（オプション）
    try:
        import matplotlib.pyplot as plt
        
        sizes = [r['size'] for r in results]
        qf_times = [r['qf_time_us'] for r in results]
        numpy_times = [r['numpy_time_us'] for r in results]
        speedups = [r['speedup'] for r in results]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # 実行時間
        ax1.plot(sizes, qf_times, 'o-', label='QuantForge (optimized)', linewidth=2)
        ax1.plot(sizes, numpy_times, 's-', label='NumPy/SciPy', linewidth=2)
        ax1.set_xlabel('Batch Size')
        ax1.set_ylabel('Execution Time (μs)')
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Execution Time Comparison')
        
        # スピードアップ
        ax2.plot(sizes, speedups, 'o-', color='green', linewidth=2)
        ax2.axhline(y=1.0, color='k', linestyle='--', alpha=0.3)
        ax2.axhline(y=6.5, color='r', linestyle='--', alpha=0.3, label='Target (6.5x)')
        ax2.set_xlabel('Batch Size')
        ax2.set_ylabel('Speedup vs NumPy')
        ax2.set_xscale('log')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Performance Improvement')
        
        # 100件バッチをハイライト
        for ax in [ax1, ax2]:
            ax.axvline(x=100, color='orange', linestyle=':', alpha=0.5)
            ax.text(100, ax.get_ylim()[0], '100', ha='center', va='bottom', color='orange')
        
        plt.tight_layout()
        plt.savefig('small_batch_optimization_results.png', dpi=150)
        print(f"\nグラフを small_batch_optimization_results.png に保存しました")
        
    except ImportError:
        print("\nmatplotlibがインストールされていないため、グラフは作成されませんでした")


if __name__ == "__main__":
    main()
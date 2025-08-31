#!/usr/bin/env python3
"""
大規模バッチのパフォーマンス分析ツール
並列化閾値の最適化とボトルネック特定
"""

import time
import numpy as np
import quantforge as qf
from scipy.stats import norm
from typing import Dict, List, Tuple
import sys


def measure_batch_performance(model: str, size: int, iterations: int = 100) -> Dict:
    """特定サイズでのパフォーマンス測定"""
    
    # テストデータ生成
    np.random.seed(42)
    spots = np.random.uniform(80, 120, size)
    strikes = np.full(size, 100.0)
    times = np.full(size, 1.0)
    rates = np.full(size, 0.05)
    sigmas = np.random.uniform(0.15, 0.35, size)
    
    # モデル別の処理
    if model == "BlackScholes":
        # ウォームアップ
        for _ in range(5):
            _ = qf.black_scholes.call_price_batch(
                spots=spots[:100], strikes=strikes[:100], 
                times=times[:100], rates=rates[:100], sigmas=sigmas[:100]
            )
        
        # 実測
        start = time.perf_counter()
        for _ in range(iterations):
            result = qf.black_scholes.call_price_batch(
                spots=spots, strikes=strikes, times=times, rates=rates, sigmas=sigmas
            )
        elapsed = (time.perf_counter() - start) / iterations
        
    elif model == "NumPy":
        # ウォームアップ
        for _ in range(5):
            sqrt_t = np.sqrt(times[:100])
            d1 = (np.log(spots[:100] / strikes[:100]) + (rates[:100] + sigmas[:100]**2 / 2) * times[:100]) / (sigmas[:100] * sqrt_t)
            d2 = d1 - sigmas[:100] * sqrt_t
            _ = spots[:100] * norm.cdf(d1) - strikes[:100] * np.exp(-rates[:100] * times[:100]) * norm.cdf(d2)
        
        # 実測
        start = time.perf_counter()
        for _ in range(iterations):
            sqrt_t = np.sqrt(times)
            d1 = (np.log(spots / strikes) + (rates + sigmas**2 / 2) * times) / (sigmas * sqrt_t)
            d2 = d1 - sigmas * sqrt_t
            result = spots * norm.cdf(d1) - strikes * np.exp(-rates * times) * norm.cdf(d2)
        elapsed = (time.perf_counter() - start) / iterations
    
    else:
        raise ValueError(f"Unknown model: {model}")
    
    return {
        'model': model,
        'size': size,
        'time_ms': elapsed * 1000,
        'throughput': size / elapsed,
        'ns_per_option': elapsed * 1e9 / size
    }


def find_optimal_threshold() -> Tuple[int, float]:
    """並列化の最適閾値を探索"""
    
    print("並列化閾値の最適点を探索中...")
    print("-" * 60)
    
    # テストサイズ（1,000から100,000まで）
    test_sizes = [
        1000, 2000, 3000, 5000, 7000,
        10000, 15000, 20000, 30000, 40000,
        50000, 60000, 70000, 80000, 90000, 100000
    ]
    
    results = []
    best_threshold = 50000
    best_ratio = 0
    
    for size in test_sizes:
        # 反復回数をサイズに応じて調整
        iterations = max(10, 100000 // size)
        
        qf_result = measure_batch_performance("BlackScholes", size, iterations)
        np_result = measure_batch_performance("NumPy", size, iterations)
        
        ratio = np_result['time_ms'] / qf_result['time_ms']
        results.append((size, ratio, qf_result['time_ms'], np_result['time_ms']))
        
        print(f"{size:>7}: QF {qf_result['time_ms']:>7.2f}ms, "
              f"NumPy {np_result['time_ms']:>7.2f}ms, "
              f"Ratio: {ratio:>5.2f}x")
        
        # 比率が1.0を超えた最小のサイズを記録
        if ratio > 1.0 and ratio > best_ratio:
            best_ratio = ratio
            if size < best_threshold:
                best_threshold = size
    
    return best_threshold, results


def analyze_scaling() -> None:
    """スケーリング特性の分析"""
    
    print("\n" + "=" * 70)
    print("スケーリング特性分析")
    print("=" * 70)
    
    sizes = [100, 1000, 10000, 100000, 1000000]
    
    print(f"{'Size':>10} | {'QF (ms)':>10} | {'NumPy (ms)':>12} | {'Speedup':>8} | {'Efficiency':>10}")
    print("-" * 70)
    
    base_speedup = None
    
    for size in sizes:
        iterations = max(5, 10000 // size)
        
        qf_result = measure_batch_performance("BlackScholes", size, iterations)
        np_result = measure_batch_performance("NumPy", size, iterations)
        
        speedup = np_result['time_ms'] / qf_result['time_ms']
        
        if base_speedup is None:
            base_speedup = speedup
            efficiency = 100.0
        else:
            efficiency = (speedup / base_speedup) * 100
        
        print(f"{size:>10} | {qf_result['time_ms']:>10.2f} | {np_result['time_ms']:>12.2f} | "
              f"{speedup:>7.2f}x | {efficiency:>9.1f}%")


def profile_memory_usage() -> None:
    """メモリ使用量のプロファイリング"""
    
    print("\n" + "=" * 70)
    print("メモリ効率分析")
    print("=" * 70)
    
    sizes = [10000, 100000, 1000000]
    
    for size in sizes:
        # メモリ使用量の概算
        input_memory = size * 8 * 5  # 5 arrays * 8 bytes per f64
        output_memory = size * 8  # 1 output array
        total_memory = (input_memory + output_memory) / (1024 * 1024)  # MB
        
        print(f"Size {size:>8}: ~{total_memory:>6.1f} MB")
        
        # 実行時間の測定
        result = measure_batch_performance("BlackScholes", size, iterations=5)
        throughput_gb = (total_memory / 1024) / (result['time_ms'] / 1000)
        
        print(f"  処理速度: {result['throughput']:>12.0f} options/sec")
        print(f"  データスループット: {throughput_gb:>6.2f} GB/s")


def main():
    """メイン実行"""
    
    print("=" * 70)
    print("大規模バッチパフォーマンス分析")
    print("=" * 70)
    print()
    
    # 1. 最適閾値の探索
    optimal_threshold, results = find_optimal_threshold()
    
    print(f"\n推奨並列化閾値: {optimal_threshold:,} 要素")
    print(f"理由: このサイズ以上でNumPyに対して優位性を示す")
    
    # 2. クロスオーバーポイントの特定
    crossover_point = None
    for size, ratio, qf_time, np_time in results:
        if ratio >= 1.0 and crossover_point is None:
            crossover_point = size
            break
    
    if crossover_point:
        print(f"クロスオーバーポイント: {crossover_point:,} 要素")
        print(f"（このサイズ以上でQuantForgeがNumPyより高速）")
    
    # 3. スケーリング特性の分析
    analyze_scaling()
    
    # 4. メモリ効率の分析
    profile_memory_usage()
    
    # 5. 推奨事項
    print("\n" + "=" * 70)
    print("推奨事項")
    print("=" * 70)
    
    current_threshold = 50000  # 現在の PARALLEL_THRESHOLD_SMALL
    
    if optimal_threshold < current_threshold:
        print(f"✅ 並列化閾値を {current_threshold:,} から {optimal_threshold:,} に下げることを推奨")
        print(f"   期待効果: {optimal_threshold:,}〜{current_threshold:,} 要素で性能向上")
    else:
        print(f"⚠️  現在の閾値 {current_threshold:,} は適切")
    
    print("\n追加の最適化案:")
    print("1. チャンクサイズの動的調整（L1/L2キャッシュサイズに基づく）")
    print("2. NUMA対応のメモリアロケーション")
    print("3. ワークスティーリングの最適化")
    
    # 6. 詳細な分析結果
    print("\n" + "=" * 70)
    print("詳細分析結果")
    print("=" * 70)
    
    # 10,000要素での詳細分析
    print("\n10,000要素での詳細分析:")
    for _ in range(3):
        result = measure_batch_performance("BlackScholes", 10000, iterations=100)
        print(f"  実行時間: {result['time_ms']:.3f}ms "
              f"({result['throughput']/1e6:.2f}M ops/s)")


if __name__ == "__main__":
    main()
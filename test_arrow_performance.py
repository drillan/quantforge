#!/usr/bin/env python3
"""Apache Arrow Native パフォーマンステスト"""

import time
import numpy as np
import pyarrow as pa
from quantforge import arrow_native

# 定数定義（ハードコード禁止）
TEST_SIZE = 10_000
PERFORMANCE_TARGET_MICROS = 170
SPOT_PRICE = 100.0
STRIKE_PRICE = 105.0
TIME_TO_MATURITY = 1.0
RISK_FREE_RATE = 0.05
VOLATILITY = 0.2
EXPECTED_CALL_PRICE = 8.021352235143176
TOLERANCE = 1e-10

def test_arrow_call_price_performance():
    """Arrow Native実装のパフォーマンス測定"""
    
    # PyArrow配列を作成
    spots = pa.array([SPOT_PRICE] * TEST_SIZE, type=pa.float64())
    strikes = pa.array([STRIKE_PRICE] * TEST_SIZE, type=pa.float64())
    times = pa.array([TIME_TO_MATURITY] * TEST_SIZE, type=pa.float64())
    rates = pa.array([RISK_FREE_RATE] * TEST_SIZE, type=pa.float64())
    sigmas = pa.array([VOLATILITY] * TEST_SIZE, type=pa.float64())
    
    # ウォームアップ（JIT最適化のため）
    for _ in range(5):
        _ = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
    
    # パフォーマンス測定（10回の平均）
    durations = []
    for _ in range(10):
        start = time.perf_counter()
        result = arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)
        end = time.perf_counter()
        durations.append((end - start) * 1_000_000)  # マイクロ秒に変換
    
    avg_duration = sum(durations) / len(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    print(f"パフォーマンステスト結果:")
    print(f"  テストサイズ: {TEST_SIZE:,} 要素")
    print(f"  平均実行時間: {avg_duration:.2f} μs")
    print(f"  最小実行時間: {min_duration:.2f} μs")
    print(f"  最大実行時間: {max_duration:.2f} μs")
    print(f"  目標: < {PERFORMANCE_TARGET_MICROS} μs")
    
    # 正確性検証
    result_np = np.array(result)
    first_value = result_np[0] if isinstance(result_np, np.ndarray) else result[0]
    accuracy_ok = abs(first_value - EXPECTED_CALL_PRICE) < TOLERANCE
    
    print(f"\n正確性検証:")
    print(f"  計算結果: {first_value:.12f}")
    print(f"  期待値:   {EXPECTED_CALL_PRICE:.12f}")
    print(f"  誤差:     {abs(first_value - EXPECTED_CALL_PRICE):.2e}")
    print(f"  検証結果: {'✅ PASS' if accuracy_ok else '❌ FAIL'}")
    
    # パフォーマンス判定
    performance_ok = min_duration < PERFORMANCE_TARGET_MICROS
    print(f"\nパフォーマンス判定:")
    print(f"  結果: {'✅ PASS' if performance_ok else '❌ FAIL'}")
    
    if not performance_ok:
        print(f"  ⚠️ 目標未達: {min_duration:.2f} μs > {PERFORMANCE_TARGET_MICROS} μs")
    
    return performance_ok and accuracy_ok

def test_numpy_fallback_performance():
    """NumPyフォールバックのパフォーマンス測定（比較用）"""
    
    # NumPy配列を作成
    spots = np.full(TEST_SIZE, SPOT_PRICE)
    strikes = np.full(TEST_SIZE, STRIKE_PRICE)
    times = np.full(TEST_SIZE, TIME_TO_MATURITY)
    rates = np.full(TEST_SIZE, RISK_FREE_RATE)
    sigmas = np.full(TEST_SIZE, VOLATILITY)
    
    # ウォームアップ
    for _ in range(5):
        _ = arrow_native.call_price_native(spots, strikes, times, rates, sigmas)
    
    # パフォーマンス測定
    durations = []
    for _ in range(10):
        start = time.perf_counter()
        result = arrow_native.call_price_native(spots, strikes, times, rates, sigmas)
        end = time.perf_counter()
        durations.append((end - start) * 1_000_000)
    
    avg_duration = sum(durations) / len(durations)
    
    print(f"\nNumPyフォールバック性能:")
    print(f"  平均実行時間: {avg_duration:.2f} μs")
    
    return avg_duration

if __name__ == "__main__":
    print("=" * 60)
    print("Apache Arrow Native FFI パフォーマンステスト")
    print("=" * 60)
    
    # Arrow Native実装をテスト
    arrow_ok = test_arrow_call_price_performance()
    
    # NumPyフォールバックと比較
    numpy_duration = test_numpy_fallback_performance()
    
    print("\n" + "=" * 60)
    if arrow_ok:
        print("✅ すべてのテストに合格しました！")
    else:
        print("❌ パフォーマンス目標を達成できませんでした")
    print("=" * 60)
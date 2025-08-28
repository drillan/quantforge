"""QuantForge基本使用例.

このスクリプトは、QuantForgeライブラリの基本的な使用方法を示します。
Black-Scholesモデルによるオプション価格計算の単一計算とバッチ計算の例を含みます。
"""

import time

import numpy as np
from quantforge import models


def demonstrate_single_calculation() -> None:
    """単一オプション価格計算のデモンストレーション."""
    print("1. 単一オプション価格計算:")
    s = 100.0  # スポット価格
    k = 100.0  # 権利行使価格
    t = 1.0  # 満期（年）
    r = 0.05  # リスクフリーレート
    v = 0.2  # ボラティリティ

    price = models.call_price(s, k, t, r, v)
    print(f"   スポット価格: ${s:.2f}")
    print(f"   権利行使価格: ${k:.2f}")
    print(f"   満期: {t:.1f}年")
    print(f"   金利: {r:.1%}")
    print(f"   ボラティリティ: {v:.1%}")
    print(f"   → コール価格: ${price:.6f}\n")


def demonstrate_batch_calculation() -> None:
    """バッチ計算のデモンストレーション."""
    print("2. バッチ計算（複数スポット価格）:")
    k = 100.0  # 権利行使価格
    t = 1.0  # 満期（年）
    r = 0.05  # リスクフリーレート
    v = 0.2  # ボラティリティ

    spots = np.linspace(80, 120, 5)
    prices = models.call_price_batch(spots, k, t, r, v)

    for spot, price in zip(spots, prices, strict=False):
        moneyness = "ITM" if spot > k else "ATM" if spot == k else "OTM"
        print(f"   S=${spot:.0f} ({moneyness:3s}): ${price:.6f}")
    print()


def run_performance_test() -> None:
    """パフォーマンステストの実行."""
    print("3. パフォーマンステスト:")

    # 単一計算の速度
    n_single = 10000
    start = time.perf_counter()
    for _ in range(n_single):
        models.call_price(100.0, 100.0, 1.0, 0.05, 0.2)
    single_time = time.perf_counter() - start
    print(f"   単一計算: {n_single:,}回 in {single_time:.3f}秒")
    print(f"   → {single_time / n_single * 1e9:.0f} ns/計算")

    # バッチ計算の速度
    n_batch = 100_000
    spots_large = np.random.uniform(80, 120, n_batch)
    start = time.perf_counter()
    _ = models.call_price_batch(spots_large, 100.0, 1.0, 0.05, 0.2)
    batch_time = time.perf_counter() - start
    print(f"   バッチ計算: {n_batch:,}件 in {batch_time:.3f}秒")
    print(f"   → {batch_time / n_batch * 1e9:.0f} ns/計算")
    print(f"   → {n_batch / batch_time:.0f} 計算/秒")


def main() -> None:
    """メイン実行関数."""
    print("=== QuantForge Black-Scholes計算エンジン ===\n")

    demonstrate_single_calculation()
    demonstrate_batch_calculation()
    run_performance_test()


if __name__ == "__main__":
    main()

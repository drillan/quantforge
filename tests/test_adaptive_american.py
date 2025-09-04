#!/usr/bin/env python3
"""適応的American option実装のテスト"""

import sys

sys.path.insert(0, '.')

# 現在の実装で適応的実装が利用可能かテスト
# 注: 現時点ではRust側の実装のみで、Python bindingはまだ

def test_adaptive_implementation_concept():
    """適応的実装のコンセプト検証"""

    import quantforge

    # Test cases with different moneyness and maturity
    test_cases = [
        # (S, K, T, description)
        (100, 100, 1.0, "ATM, medium term"),
        (70, 100, 1.0, "Deep OTM"),
        (130, 100, 1.0, "Deep ITM"),
        (100, 100, 0.05, "ATM, short term"),
        (100, 100, 3.0, "ATM, long term"),
    ]

    r = 0.05
    q = 0.0
    sigma = 0.2

    print("Adaptive American Option Pricing Concept Test")
    print("=" * 60)

    for s, k, t, desc in test_cases:
        # 現在のBAW実装を使用（適応的dampeningはRust内部で適用される予定）
        put_price = quantforge.american.put_price(s, k, t, r, q, sigma)
        european = quantforge.merton.put_price(s, k, t, r, q, sigma)
        premium = put_price - european
        premium_pct = (premium / european * 100) if european > 0 else 0

        print(f"\n{desc}:")
        print(f"  S={s}, K={k}, T={t}")
        print(f"  American put: {put_price:.4f}")
        print(f"  European put: {european:.4f}")
        print(f"  Early exercise premium: {premium:.4f} ({premium_pct:.1f}%)")

        # 基本検証
        assert put_price >= european - 1e-10, "American < European"
        assert put_price >= max(k - s, 0), "Below intrinsic value"

def test_dampening_factor_ranges():
    """Dampening factorの妥当性検証"""

    # 理論的なdampening factor範囲
    BASE_DAMPENING = 0.695
    MIN_DAMPENING = 0.60
    MAX_DAMPENING = 0.80

    # モネーネス別の期待されるdampening調整
    adjustments = {
        'ATM (0.9-1.1)': 1.00,
        'Near ATM (0.8-1.2)': 1.03,
        'Deep OTM (<0.8)': 1.08,
        'Deep ITM (>1.2)': 0.95,
    }

    print("\nDampening Factor Analysis")
    print("=" * 60)
    print(f"Base dampening factor: {BASE_DAMPENING}")
    print(f"Allowed range: {MIN_DAMPENING} - {MAX_DAMPENING}")
    print("\nMoneyness adjustments:")

    for region, factor in adjustments.items():
        adjusted = BASE_DAMPENING * factor
        clamped = max(MIN_DAMPENING, min(MAX_DAMPENING, adjusted))
        print(f"  {region}: x{factor} = {adjusted:.3f} → {clamped:.3f}")

def test_parameter_sensitivity():
    """パラメータ感度分析"""

    import quantforge

    # Base case
    s_base = 100.0
    k = 100.0
    t = 1.0
    r = 0.05
    q = 0.0
    sigma = 0.2

    base_price = quantforge.american.put_price(s_base, k, t, r, q, sigma)

    print("\nParameter Sensitivity Analysis")
    print("=" * 60)
    print(f"Base case price: {base_price:.4f}")

    # Spot price sensitivity
    print("\nSpot price sensitivity:")
    for delta_s in [-20, -10, 0, 10, 20]:
        s = s_base + delta_s
        price = quantforge.american.put_price(s, k, t, r, q, sigma)
        change = (price - base_price) / base_price * 100
        print(f"  S={s:3.0f}: {price:6.4f} ({change:+6.2f}%)")

    # Time sensitivity
    print("\nTime to maturity sensitivity:")
    for t_test in [0.1, 0.25, 0.5, 1.0, 2.0]:
        price = quantforge.american.put_price(s_base, k, t_test, r, q, sigma)
        print(f"  T={t_test:3.1f}: {price:6.4f}")

    # Volatility sensitivity
    print("\nVolatility sensitivity:")
    for sigma_test in [0.1, 0.15, 0.2, 0.3, 0.4]:
        price = quantforge.american.put_price(s_base, k, t, r, q, sigma_test)
        change = (price - base_price) / base_price * 100
        print(f"  σ={sigma_test:3.1f}: {price:6.4f} ({change:+6.2f}%)")

if __name__ == "__main__":
    test_adaptive_implementation_concept()
    test_dampening_factor_ranges()
    test_parameter_sensitivity()

    print("\n" + "=" * 60)
    print("Adaptive American option testing complete!")
    print("Note: Full adaptive implementation is in Rust (american_adaptive.rs)")
    print("Python bindings will be added in Phase 3")

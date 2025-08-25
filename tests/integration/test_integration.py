"""Python統合テスト."""

import numpy as np
import pytest


def test_calculate_call_price() -> None:
    """単一計算のテスト."""
    # This will be imported once the module is built
    from quantforge import calculate_call_price

    # At-the-money option
    s = 100.0
    k = 100.0
    t = 1.0
    r = 0.05
    v = 0.2

    price = calculate_call_price(s, k, t, r, v)

    # 参照値との比較
    expected = 10.450583572185565
    assert abs(price - expected) < 1e-5  # 累積正規分布関数の近似精度に合わせて調整


def test_calculate_call_price_batch() -> None:
    """バッチ計算のテスト."""
    from quantforge import calculate_call_price_batch

    spots = np.array([90.0, 100.0, 110.0], dtype=np.float64)
    k = 100.0
    t = 1.0
    r = 0.05
    v = 0.2

    prices = calculate_call_price_batch(spots, k, t, r, v)

    assert len(prices) == 3
    assert isinstance(prices, np.ndarray)

    # ITM, ATM, OTMの価格関係を確認
    assert prices[0] < prices[1] < prices[2]


def test_invalid_inputs() -> None:
    """無効な入力のテスト."""
    from quantforge import calculate_call_price

    # 負の価格
    with pytest.raises(ValueError, match="Spot price must be positive"):
        calculate_call_price(-100.0, 100.0, 1.0, 0.05, 0.2)

    # 負の時間
    with pytest.raises(ValueError, match="Time to maturity must be positive"):
        calculate_call_price(100.0, 100.0, -1.0, 0.05, 0.2)

    # 負のボラティリティ
    with pytest.raises(ValueError, match="Volatility must be positive"):
        calculate_call_price(100.0, 100.0, 1.0, 0.05, -0.2)


def test_edge_cases() -> None:
    """エッジケースのテスト."""
    from quantforge import calculate_call_price

    # 満期直前
    price = calculate_call_price(100.0, 90.0, 0.001, 0.05, 0.2)
    assert price > 10.0  # Deep ITM

    # 高ボラティリティ
    price = calculate_call_price(100.0, 100.0, 1.0, 0.05, 2.0)
    assert price > 0.0

    # ゼロ金利
    price = calculate_call_price(100.0, 100.0, 1.0, 0.0, 0.2)
    assert price > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Python統合テスト."""

import numpy as np
import pytest
from quantforge.models import black_scholes


def test_calculate_call_price() -> None:
    """単一計算のテスト."""
    # At-the-money option
    s = 100.0
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2

    price = black_scholes.call_price(s, k, t, r, sigma)

    # 参照値との比較
    expected = 10.450583572185565
    assert abs(price - expected) < 1e-5  # 累積正規分布関数の近似精度に合わせて調整


def test_call_price_batch() -> None:
    """バッチ計算のテスト."""

    spots = np.array([90.0, 100.0, 110.0], dtype=np.float64)
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2

    prices = black_scholes.call_price_batch(spots, k, t, r, sigma)

    assert len(prices) == 3
    assert isinstance(prices, np.ndarray)

    # ITM, ATM, OTMの価格関係を確認
    assert prices[0] < prices[1] < prices[2]


def test_invalid_inputs() -> None:
    """無効な入力のテスト."""

    # 負の価格
    with pytest.raises(ValueError, match="Invalid spot price"):
        black_scholes.call_price(-100.0, 100.0, 1.0, 0.05, 0.2)

    # 負の時間
    with pytest.raises(ValueError, match="Invalid time"):
        black_scholes.call_price(100.0, 100.0, -1.0, 0.05, 0.2)

    # 負のボラティリティ
    with pytest.raises(ValueError, match="Invalid volatility"):
        black_scholes.call_price(100.0, 100.0, 1.0, 0.05, -0.2)


def test_edge_cases() -> None:
    """エッジケースのテスト."""

    # 満期直前
    price = black_scholes.call_price(100.0, 90.0, 0.001, 0.05, 0.2)
    assert price > 10.0  # Deep ITM

    # 高ボラティリティ
    price = black_scholes.call_price(100.0, 100.0, 1.0, 0.05, 2.0)
    assert price > 0.0

    # ゼロ金利
    price = black_scholes.call_price(100.0, 100.0, 1.0, 0.0, 0.2)
    assert price > 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

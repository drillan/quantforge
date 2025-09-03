"""Python統合テスト."""

import numpy as np
import pytest
from quantforge import black_scholes
from conftest import arrow, create_test_array, INPUT_ARRAY_TYPES


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


@pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
def test_call_price_batch(array_type: str) -> None:
    """バッチ計算のテスト（NumPyとPyArrow両方）."""

    spots = create_test_array([90.0, 100.0, 110.0], array_type)
    k = 100.0
    t = 1.0
    r = 0.05
    sigma = 0.2

    prices = black_scholes.call_price_batch(spots, k, t, r, sigma)

    assert len(prices) == 3
    # Arrow配列であることを確認
    arrow.assert_type(prices)

    # ITM, ATM, OTMの価格関係を確認
    prices_list = arrow.to_list(prices)
    assert prices_list[0] < prices_list[1] < prices_list[2]


def test_invalid_inputs() -> None:
    """無効な入力のテスト."""

    # 負の価格
    with pytest.raises(ValueError, match="spot must be positive"):
        black_scholes.call_price(-100.0, 100.0, 1.0, 0.05, 0.2)

    # 負の時間
    with pytest.raises(ValueError, match="time must be positive"):
        black_scholes.call_price(100.0, 100.0, -1.0, 0.05, 0.2)

    # 負のボラティリティ
    with pytest.raises(ValueError, match="sigma must be positive"):
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

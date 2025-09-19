"""プットオプションの統合テスト"""

import os
import sys

import numpy as np
import pytest
from quantforge import black_scholes  # type: ignore[import-untyped]

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from conftest import INPUT_ARRAY_TYPES, PRACTICAL_TOLERANCE, arrow, create_test_array


class PutOptionTestData:
    """テスト用の共通パラメータと期待値"""

    SPOT_ATM = 100.0
    SPOT_ITM = 90.0
    SPOT_OTM = 110.0
    STRIKE = 100.0
    TIME = 1.0
    RATE = 0.05
    SIGMA = 0.2
    ATM_EXPECTED = 5.573526022657734

    @staticmethod
    def calculate_put(spot: float) -> float:
        """共通のプット価格計算"""
        return black_scholes.put_price(
            spot, PutOptionTestData.STRIKE, PutOptionTestData.TIME, PutOptionTestData.RATE, PutOptionTestData.SIGMA
        )


def test_put_single_calculation() -> None:
    """単一プット価格計算のテスト"""
    # ATMプット
    price = PutOptionTestData.calculate_put(PutOptionTestData.SPOT_ATM)
    assert abs(price - PutOptionTestData.ATM_EXPECTED) < PRACTICAL_TOLERANCE

    # ITMプット (S < K)
    itm_price = PutOptionTestData.calculate_put(PutOptionTestData.SPOT_ITM)
    assert itm_price > price  # ITMはATMより高い

    # OTMプット (S > K)
    otm_price = PutOptionTestData.calculate_put(PutOptionTestData.SPOT_OTM)
    assert otm_price < price  # OTMはATMより低い


@pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
def test_put_batch_calculation(array_type: str) -> None:
    """バッチプット価格計算のテスト（NumPyとPyArrow両方）"""
    spots = create_test_array(
        [PutOptionTestData.SPOT_ITM, PutOptionTestData.SPOT_ATM, PutOptionTestData.SPOT_OTM], array_type
    )
    prices = black_scholes.put_price_batch(
        spots, PutOptionTestData.STRIKE, PutOptionTestData.TIME, PutOptionTestData.RATE, PutOptionTestData.SIGMA
    )

    assert len(prices) == 3
    arrow.assert_type(prices)  # Arrow配列であることを確認

    # ITM > ATM > OTM
    prices_list = arrow.to_list(prices)
    assert prices_list[0] > prices_list[1] > prices_list[2]


def test_put_call_parity() -> None:
    """Put-Callパリティのテスト"""
    s = PutOptionTestData.SPOT_ATM
    k = PutOptionTestData.STRIKE
    t = PutOptionTestData.TIME
    r = PutOptionTestData.RATE
    sigma = PutOptionTestData.SIGMA

    call = black_scholes.call_price(s, k, t, r, sigma)
    put = black_scholes.put_price(s, k, t, r, sigma)

    # C - P = S - K*exp(-r*T)
    parity_lhs = call - put
    parity_rhs = s - k * np.exp(-r * t)

    assert abs(parity_lhs - parity_rhs) < 1e-7  # 数値精度レベルで一致


@pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
def test_put_large_batch_performance(array_type: str) -> None:
    """大規模バッチのパフォーマンステスト（NumPyとPyArrow両方）"""
    n = 100000
    spots_np = np.random.uniform(50, 150, n)
    spots = create_test_array(spots_np.tolist(), array_type)

    # エラーなく実行できることを確認
    prices = black_scholes.put_price_batch(
        spots, PutOptionTestData.STRIKE, PutOptionTestData.TIME, PutOptionTestData.RATE, PutOptionTestData.SIGMA
    )

    assert len(prices) == n
    arrow.assert_type(prices)  # Arrow配列であることを確認

    # 全て非負かつ上限以下
    arrow.assert_comparison(prices, "all_positive")
    prices_list = arrow.to_list(prices)
    upper_bound = PutOptionTestData.STRIKE * np.exp(-PutOptionTestData.RATE * PutOptionTestData.TIME)
    assert all(p <= upper_bound for p in prices_list)


def test_put_edge_cases() -> None:
    """エッジケースのテスト"""
    # Deep ITM (S << K)
    deep_itm_spot = 10.0
    deep_itm = black_scholes.put_price(
        deep_itm_spot, PutOptionTestData.STRIKE, PutOptionTestData.TIME, PutOptionTestData.RATE, PutOptionTestData.SIGMA
    )
    intrinsic = PutOptionTestData.STRIKE * np.exp(-PutOptionTestData.RATE * PutOptionTestData.TIME) - deep_itm_spot
    assert deep_itm >= intrinsic * 0.99  # ほぼ内在価値

    # Deep OTM (S >> K)
    deep_otm_spot = 500.0
    deep_otm = black_scholes.put_price(
        deep_otm_spot, PutOptionTestData.STRIKE, PutOptionTestData.TIME, PutOptionTestData.RATE, PutOptionTestData.SIGMA
    )
    assert deep_otm < 0.001  # ほぼゼロ

    # 満期直前（最小時間は0.001）
    near_expiry_time = 0.001
    near_expiry = black_scholes.put_price(
        PutOptionTestData.SPOT_ITM,
        PutOptionTestData.STRIKE,
        near_expiry_time,
        PutOptionTestData.RATE,
        PutOptionTestData.SIGMA,
    )
    assert abs(near_expiry - (PutOptionTestData.STRIKE - PutOptionTestData.SPOT_ITM)) < 0.1  # ほぼ内在価値


def test_put_input_validation() -> None:
    """入力検証のテスト"""
    with pytest.raises(ValueError):
        # 負のスポット価格
        black_scholes.put_price(
            -PutOptionTestData.SPOT_ATM,
            PutOptionTestData.STRIKE,
            PutOptionTestData.TIME,
            PutOptionTestData.RATE,
            PutOptionTestData.SIGMA,
        )

    with pytest.raises(ValueError):
        # 負のボラティリティ
        black_scholes.put_price(
            PutOptionTestData.SPOT_ATM,
            PutOptionTestData.STRIKE,
            PutOptionTestData.TIME,
            PutOptionTestData.RATE,
            -PutOptionTestData.SIGMA,
        )

    with pytest.raises((ValueError, Exception)):  # Arrow raises Exception for NaN values
        # NaN入力
        spots = np.array([100.0, np.nan, 110.0])
        black_scholes.put_price_batch(spots, 100.0, 1.0, 0.05, 0.2)

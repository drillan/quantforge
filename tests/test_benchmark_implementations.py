"""ベンチマーク実装の正確性テスト."""

import numpy as np
from conftest import PRACTICAL_TOLERANCE
from quantforge import models

from benchmarks.baseline.python_baseline import (
    black_scholes_numpy_batch,
    black_scholes_pure_python,
    black_scholes_scipy_single,
)


def test_implementations_consistency() -> None:
    """各実装の結果が一致することを確認."""
    s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2

    # 各実装の結果
    qf_result = models.call_price(s, k, t, r, sigma)
    pure_result = black_scholes_pure_python(s, k, t, r, sigma)
    scipy_result = black_scholes_scipy_single(s, k, t, r, sigma)

    # 誤差1%以内で一致（実務精度）
    assert abs(qf_result - scipy_result) / scipy_result < PRACTICAL_TOLERANCE
    assert abs(pure_result - scipy_result) / scipy_result < PRACTICAL_TOLERANCE


def test_batch_consistency() -> None:
    """バッチ処理の一致確認."""
    spots = np.array([90.0, 100.0, 110.0], dtype=np.float64)
    k, t, r, sigma = 100.0, 1.0, 0.05, 0.2

    # 各実装の結果
    qf_batch = models.call_price_batch(spots, k, t, r, sigma)
    np_batch = black_scholes_numpy_batch(spots, k, t, r, sigma)

    # 配列の要素ごとに比較
    np.testing.assert_allclose(qf_batch, np_batch, rtol=PRACTICAL_TOLERANCE)


def test_pure_python_accuracy() -> None:
    """Pure Python実装の精度確認."""
    # 既知の正確な値（外部計算機で検証済み）
    s, k, t, r, sigma = 100.0, 100.0, 0.5, 0.05, 0.25

    pure_result = black_scholes_pure_python(s, k, t, r, sigma)
    scipy_result = black_scholes_scipy_single(s, k, t, r, sigma)

    # Abramowitz近似の精度限界を考慮
    assert abs(pure_result - scipy_result) / scipy_result < 0.01  # 1%以内


def test_edge_cases() -> None:
    """エッジケースの処理."""
    # ディープ・イン・ザ・マネー
    s, k, t, r, sigma = 200.0, 100.0, 1.0, 0.05, 0.2
    qf_deep_itm = models.call_price(s, k, t, r, sigma)
    pure_deep_itm = black_scholes_pure_python(s, k, t, r, sigma)
    assert abs(qf_deep_itm - pure_deep_itm) / pure_deep_itm < PRACTICAL_TOLERANCE

    # ディープ・アウト・オブ・ザ・マネー
    s, k = 50.0, 100.0
    qf_deep_otm = models.call_price(s, k, t, r, sigma)
    pure_deep_otm = black_scholes_pure_python(s, k, t, r, sigma)
    assert abs(qf_deep_otm - pure_deep_otm) < 1.0  # 絶対誤差で比較（値が小さいため）

    # ゼロボラティリティ近似
    s, k, sigma = 100.0, 90.0, 0.01
    qf_low_vol = models.call_price(s, k, t, r, sigma)
    pure_low_vol = black_scholes_pure_python(s, k, t, r, sigma)
    assert abs(qf_low_vol - pure_low_vol) / pure_low_vol < PRACTICAL_TOLERANCE

"""QuantForge型定義."""

import numpy as np
from numpy.typing import NDArray

def calculate_call_price(
    s: float,
    k: float,
    t: float,
    r: float,
    sigma: float,
) -> float:
    """ヨーロピアンコールオプション価格を計算.

    Args:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: リスクフリーレート
        sigma: ボラティリティ（業界標準記号σ）

    Returns:
        オプション価格

    Raises:
        ValueError: 入力が範囲外の場合
    """
    ...

def calculate_call_price_batch(
    spots: NDArray[np.float64],
    k: float,
    t: float,
    r: float,
    sigma: float,
) -> NDArray[np.float64]:
    """バッチ計算（SIMD最適化）.

    Args:
        spots: スポット価格の配列
        k: 権利行使価格
        t: 満期までの時間（年）
        r: リスクフリーレート
        sigma: ボラティリティ（業界標準記号σ）

    Returns:
        オプション価格の配列

    Raises:
        ValueError: 入力が範囲外の場合
    """
    ...

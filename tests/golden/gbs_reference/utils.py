"""数学関数ユーティリティ（GBS_2025.pyから抽出）."""

import math
from scipy.stats import norm


def assert_close(value_a: float, value_b: float, precision: float = 1e-10) -> bool:
    """2つの浮動小数点数の近似比較.
    
    Args:
        value_a: 比較値1
        value_b: 比較値2
        precision: 許容誤差（デフォルト: 1e-10）
    
    Returns:
        値が十分に近い場合True
    """
    if value_a < 1000000.0 and value_b < 1000000.0:
        diff = abs(value_a - value_b)
    else:
        diff = abs((value_a - value_b) / value_a) if value_a != 0 else abs(value_b)
    
    return diff < precision
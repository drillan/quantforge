"""Black-Scholesの各種Python実装."""

import math

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm


def erf_approx(x: float) -> float:
    """誤差関数の近似計算（Abramowitz and Stegun近似）."""
    # Pure Python用の累積正規分布関数の実装
    # erfの多項式近似を使用
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911

    sign = 1 if x >= 0 else -1
    x = abs(x)

    t = 1.0 / (1.0 + p * x)
    t2 = t * t
    t3 = t2 * t
    t4 = t3 * t
    t5 = t4 * t
    y = 1.0 - ((((a5 * t5 + a4 * t4) + a3 * t3) + a2 * t2) + a1 * t) * math.exp(-x * x)

    return sign * y


def norm_cdf_pure(x: float) -> float:
    """累積正規分布関数（Pure Python実装）."""
    return 0.5 * (1.0 + erf_approx(x / math.sqrt(2.0)))


def black_scholes_pure_python(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """純Python実装（外部ライブラリなし）."""
    # mathモジュールのみ使用
    sqrt_t = math.sqrt(t)
    d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t

    # 累積正規分布関数を自前実装
    nd1 = norm_cdf_pure(d1)
    nd2 = norm_cdf_pure(d2)

    return s * nd1 - k * math.exp(-r * t) * nd2


def black_scholes_scipy_single(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """SciPy実装（一般的な実装）."""
    d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    result: float = float(s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2))
    return result


def black_scholes_numpy_batch(
    spots: NDArray[np.float64], k: float, t: float, r: float, sigma: float
) -> NDArray[np.float64]:
    """NumPy実装（バッチ処理最適化）."""
    sqrt_t = np.sqrt(t)
    d1 = (np.log(spots / k) + (r + 0.5 * sigma**2) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t
    result: NDArray[np.float64] = spots * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    return result


def black_scholes_pure_python_batch(spots: list[float], k: float, t: float, r: float, sigma: float) -> list[float]:
    """Pure Pythonバッチ処理（リスト内包表記）."""
    return [black_scholes_pure_python(s, k, t, r, sigma) for s in spots]

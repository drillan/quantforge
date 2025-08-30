"""Python基準実装 - インプライドボラティリティ計算.

全モデル（Black-Scholes, Black76, Merton, American）のIV計算基準実装。
業界標準のscipy.optimize.brentqおよびNewton-Raphson法を使用。
"""

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm


def black_scholes_price_scipy(s: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> float:
    """Black-Scholes価格計算（SciPy版）.

    Args:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        sigma: ボラティリティ
        is_call: コールオプションの場合True

    Returns:
        オプション価格
    """
    d1 = (np.log(s / k) + (r + sigma**2 / 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)

    if is_call:
        return s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)  # type: ignore[no-any-return]
    else:
        return k * np.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)  # type: ignore[no-any-return]


def black76_price(f: float, k: float, t: float, r: float, sigma: float, is_call: bool = True) -> float:
    """Black76価格計算.

    Args:
        f: 先物価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        sigma: ボラティリティ
        is_call: コールオプションの場合True

    Returns:
        オプション価格
    """
    d1 = (np.log(f / k) + (sigma**2 / 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    discount = np.exp(-r * t)

    if is_call:
        return discount * (f * norm.cdf(d1) - k * norm.cdf(d2))  # type: ignore[no-any-return]
    else:
        return discount * (k * norm.cdf(-d2) - f * norm.cdf(-d1))  # type: ignore[no-any-return]


def merton_price(s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True) -> float:
    """Merton価格計算（配当利回り考慮）.

    Args:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        q: 配当利回り
        sigma: ボラティリティ
        is_call: コールオプションの場合True

    Returns:
        オプション価格
    """
    d1 = (np.log(s / k) + (r - q + sigma**2 / 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)

    if is_call:
        return s * np.exp(-q * t) * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)  # type: ignore[no-any-return]
    else:
        return k * np.exp(-r * t) * norm.cdf(-d2) - s * np.exp(-q * t) * norm.cdf(-d1)  # type: ignore[no-any-return]


def american_price_approx(
    s: float, k: float, t: float, r: float, q: float, sigma: float, is_call: bool = True
) -> float:
    """American価格の近似計算（Bjerksund-Stensland）.

    簡略化のためEuropean価格を使用（実際はより複雑な近似が必要）.

    Args:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        q: 配当利回り
        sigma: ボラティリティ
        is_call: コールオプションの場合True

    Returns:
        オプション価格
    """
    # 簡略化: European価格を返す（実際のAmerican価格はより高い）
    european_price = merton_price(s, k, t, r, q, sigma, is_call)

    # 早期行使プレミアムの簡単な近似
    if not is_call and q > 0:
        # プットの場合、配当があると早期行使価値が上がる
        intrinsic = max(k - s, 0)
        return max(european_price * 1.1, intrinsic)  # 10%のプレミアムを追加
    return european_price


def vega_scipy(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """Vega計算（Black-Scholes）.

    Args:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        sigma: ボラティリティ

    Returns:
        Vega（ボラティリティ感応度）
    """
    d1 = (np.log(s / k) + (r + sigma**2 / 2) * t) / (sigma * np.sqrt(t))
    return s * norm.pdf(d1) * np.sqrt(t)  # type: ignore[no-any-return]


def vega_merton(s: float, k: float, t: float, r: float, q: float, sigma: float) -> float:
    """Vega計算（Merton）.

    Args:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        q: 配当利回り
        sigma: ボラティリティ

    Returns:
        Vega（ボラティリティ感応度）
    """
    d1 = (np.log(s / k) + (r - q + sigma**2 / 2) * t) / (sigma * np.sqrt(t))
    return s * np.exp(-q * t) * norm.pdf(d1) * np.sqrt(t)  # type: ignore[no-any-return]


def implied_volatility_scipy(price: float, s: float, k: float, t: float, r: float, is_call: bool = True) -> float:
    """Brent法によるIV計算（Black-Scholes）.

    Args:
        price: オプション価格
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        is_call: コールオプションの場合True

    Returns:
        インプライドボラティリティ
    """

    def objective(sigma: float) -> float:
        return black_scholes_price_scipy(s, k, t, r, sigma, is_call) - price

    try:
        return brentq(objective, 0.001, 10.0, xtol=1e-6)
    except ValueError:
        return np.nan


def black76_iv_scipy(price: float, f: float, k: float, t: float, r: float, is_call: bool = True) -> float:
    """Black76のIV計算.

    Args:
        price: オプション価格
        f: 先物価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        is_call: コールオプションの場合True

    Returns:
        インプライドボラティリティ
    """

    def objective(sigma: float) -> float:
        return black76_price(f, k, t, r, sigma, is_call) - price

    try:
        return brentq(objective, 0.001, 10.0, xtol=1e-6)
    except ValueError:
        return np.nan


def merton_iv_scipy(price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool = True) -> float:
    """MertonモデルのIV計算.

    Args:
        price: オプション価格
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        q: 配当利回り
        is_call: コールオプションの場合True

    Returns:
        インプライドボラティリティ
    """

    def objective(sigma: float) -> float:
        return merton_price(s, k, t, r, q, sigma, is_call) - price

    try:
        return brentq(objective, 0.001, 10.0, xtol=1e-6)
    except ValueError:
        return np.nan


def american_iv_scipy(price: float, s: float, k: float, t: float, r: float, q: float, is_call: bool = True) -> float:
    """AmericanモデルのIV計算（簡略版）.

    Args:
        price: オプション価格
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        q: 配当利回り
        is_call: コールオプションの場合True

    Returns:
        インプライドボラティリティ
    """

    def objective(sigma: float) -> float:
        return american_price_approx(s, k, t, r, q, sigma, is_call) - price

    try:
        return brentq(objective, 0.001, 10.0, xtol=1e-6)
    except ValueError:
        return np.nan


def implied_volatility_newton(
    price: float,
    s: float,
    k: float,
    t: float,
    r: float,
    is_call: bool = True,
    max_iter: int = 20,
) -> float:
    """Newton-Raphson法によるIV計算（Black-Scholes）.

    Args:
        price: オプション価格
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        is_call: コールオプションの場合True
        max_iter: 最大反復回数

    Returns:
        インプライドボラティリティ
    """
    sigma = 0.2  # 初期値

    for _ in range(max_iter):
        bs_price = black_scholes_price_scipy(s, k, t, r, sigma, is_call)
        vega_val = vega_scipy(s, k, t, r, sigma)

        if abs(vega_val) < 1e-10:
            break

        diff = bs_price - price
        if abs(diff) < 1e-6:
            return sigma

        sigma = sigma - diff / vega_val
        sigma = max(0.001, min(sigma, 10.0))  # 境界制約

    return sigma


def implied_volatility_batch_scipy(
    prices: np.ndarray,
    spots: np.ndarray,
    strikes: np.ndarray,
    times: np.ndarray,
    rates: np.ndarray,
    is_calls: np.ndarray,
    model: str = "bs",
    dividends: np.ndarray | None = None,
) -> np.ndarray:
    """バッチIV計算（ループ版）- 全モデル対応.

    Args:
        prices: オプション価格の配列
        spots: スポット価格の配列（Black76の場合は先物価格）
        strikes: 権利行使価格の配列
        times: 満期までの時間の配列
        rates: 無リスク金利の配列
        is_calls: コール/プットフラグの配列
        model: モデル名（'bs', 'black76', 'merton', 'american'）
        dividends: 配当利回りの配列（MertonとAmericanで使用）

    Returns:
        インプライドボラティリティの配列
    """
    n = len(prices)
    ivs = np.empty(n)

    for i in range(n):
        if model == "bs":
            ivs[i] = implied_volatility_scipy(prices[i], spots[i], strikes[i], times[i], rates[i], is_calls[i])
        elif model == "black76":
            ivs[i] = black76_iv_scipy(prices[i], spots[i], strikes[i], times[i], rates[i], is_calls[i])
        elif model == "merton":
            if dividends is None:
                raise ValueError("Dividends required for Merton model")
            ivs[i] = merton_iv_scipy(
                prices[i],
                spots[i],
                strikes[i],
                times[i],
                rates[i],
                dividends[i],
                is_calls[i],
            )
        elif model == "american":
            if dividends is None:
                raise ValueError("Dividends required for American model")
            ivs[i] = american_iv_scipy(
                prices[i],
                spots[i],
                strikes[i],
                times[i],
                rates[i],
                dividends[i],
                is_calls[i],
            )
        else:
            raise ValueError(f"Unknown model: {model}")

    return ivs


def implied_volatility_batch_newton(
    prices: np.ndarray,
    spots: np.ndarray,
    strikes: np.ndarray,
    times: np.ndarray,
    rates: np.ndarray,
    is_calls: np.ndarray,
    max_iter: int = 20,
) -> np.ndarray:
    """バッチIV計算（Newton-Raphson法）.

    Args:
        prices: オプション価格の配列
        spots: スポット価格の配列
        strikes: 権利行使価格の配列
        times: 満期までの時間の配列
        rates: 無リスク金利の配列
        is_calls: コール/プットフラグの配列
        max_iter: 最大反復回数

    Returns:
        インプライドボラティリティの配列
    """
    n = len(prices)
    ivs = np.empty(n)

    for i in range(n):
        ivs[i] = implied_volatility_newton(prices[i], spots[i], strikes[i], times[i], rates[i], is_calls[i], max_iter)

    return ivs

"""実践シナリオのベンチマークスクリプト.

小規模（3実装比較）と大規模（SciPy vs QuantForge）の両方を測定。
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# プロジェクトルートからの相対パスでresultsディレクトリを定義
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = BASE_DIR / "benchmarks" / "results"

import numpy as np

# Baseline implementations
from benchmarks.baseline.iv_baseline import black_scholes_price_scipy
from benchmarks.baseline.python_baseline import black_scholes_pure_python, norm_cdf_pure


def pure_python_implied_volatility(price: float, s: float, k: float, t: float, r: float, is_call: bool = True) -> float:
    """Pure Python実装のIV計算（Newton-Raphson法）.

    mathモジュールとerfベースのnorm_cdfのみ使用。
    """
    import math

    sigma = 0.2  # 初期値
    max_iter = 20

    for _ in range(max_iter):
        # Pure PythonでBS価格を計算
        bs_price = black_scholes_pure_python(s, k, t, r, sigma)

        # Pure PythonでVegaを計算
        sqrt_t = math.sqrt(t)
        d1 = (math.log(s / k) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
        vega_val = s * norm_cdf_pure(d1) * sqrt_t / (math.sqrt(2 * math.pi)) * math.exp(-d1 * d1 / 2)

        if abs(vega_val) < 1e-10:
            break

        diff = bs_price - price
        if abs(diff) < 1e-6:
            return sigma

        sigma = sigma - diff / vega_val
        sigma = max(0.001, min(sigma, 10.0))

    return sigma


def benchmark_volatility_surface_small() -> dict[str, float]:
    """ボラティリティサーフェス構築（小規模: 10×10 = 100点）."""

    # グリッド生成
    strikes = np.linspace(80, 120, 10)
    maturities = np.linspace(0.1, 2.0, 10)
    k_grid, t_grid = np.meshgrid(strikes, maturities)
    k_flat = k_grid.flatten()
    t_flat = t_grid.flatten()

    # その他のパラメータ
    spot = 100.0
    rate = 0.05
    s_flat = np.full_like(k_flat, spot)
    r_flat = np.full_like(k_flat, rate)

    # 市場価格をシミュレート（既知のボラティリティから）
    true_vol = 0.2
    market_prices = np.array(
        [black_scholes_price_scipy(s_flat[i], k_flat[i], t_flat[i], r_flat[i], true_vol) for i in range(len(k_flat))]
    )

    results = {}

    # 1. Pure Python実装（forループ）
    start = time.perf_counter()
    for i in range(len(market_prices)):
        pure_python_implied_volatility(market_prices[i], s_flat[i], k_flat[i], t_flat[i], r_flat[i])
    pure_python_time = time.perf_counter() - start
    results["pure_python_ms"] = pure_python_time * 1000

    # 2. NumPy+SciPy実装（ベクトル化）
    from benchmarks.baseline.iv_vectorized import implied_volatility_newton_vectorized

    start = time.perf_counter()
    implied_volatility_newton_vectorized(
        market_prices, s_flat, k_flat, t_flat, r_flat, np.full(len(market_prices), True)
    )
    numpy_scipy_time = time.perf_counter() - start
    results["numpy_scipy_ms"] = numpy_scipy_time * 1000

    # 3. QuantForge実装（並列バッチ）
    try:
        from quantforge.models import black_scholes  # type: ignore[import-not-found]

        if hasattr(black_scholes, "implied_volatility_batch"):
            start = time.perf_counter()
            black_scholes.implied_volatility_batch(
                market_prices, s_flat, k_flat, t_flat, r_flat, np.full(len(market_prices), True)
            )
            qf_time = time.perf_counter() - start
            results["quantforge_ms"] = qf_time * 1000
    except ImportError:
        results["quantforge_ms"] = 0.0

    return results


def benchmark_volatility_surface_large() -> dict[str, float]:
    """ボラティリティサーフェス構築（大規模: 100×100 = 10,000点）."""

    # グリッド生成
    strikes = np.linspace(50, 150, 100)
    maturities = np.linspace(0.1, 3.0, 100)
    k_grid, t_grid = np.meshgrid(strikes, maturities)
    k_flat = k_grid.flatten()
    t_flat = t_grid.flatten()

    # その他のパラメータ
    spot = 100.0
    rate = 0.05
    s_flat = np.full_like(k_flat, spot)
    r_flat = np.full_like(k_flat, rate)

    # 市場価格をシミュレート
    true_vol = 0.2
    market_prices = np.array(
        [black_scholes_price_scipy(s_flat[i], k_flat[i], t_flat[i], r_flat[i], true_vol) for i in range(len(k_flat))]
    )

    results = {}

    # 1. NumPy+SciPy実装（ベクトル化）
    from benchmarks.baseline.iv_vectorized import implied_volatility_newton_vectorized

    start = time.perf_counter()
    implied_volatility_newton_vectorized(
        market_prices, s_flat, k_flat, t_flat, r_flat, np.full(len(market_prices), True)
    )
    numpy_scipy_time = time.perf_counter() - start
    results["numpy_scipy_ms"] = numpy_scipy_time * 1000

    # 2. QuantForge実装（並列バッチ）
    try:
        from quantforge.models import black_scholes

        if hasattr(black_scholes, "implied_volatility_batch"):
            start = time.perf_counter()
            black_scholes.implied_volatility_batch(
                market_prices, s_flat, k_flat, t_flat, r_flat, np.full(len(market_prices), True)
            )
            qf_time = time.perf_counter() - start
            results["quantforge_ms"] = qf_time * 1000
    except ImportError:
        results["quantforge_ms"] = 0.0

    # Pure Pythonは時間がかかりすぎるため除外

    return results


def benchmark_portfolio_risk_small() -> dict[str, float]:
    """ポートフォリオリスク計算（小規模: 100オプション）."""

    n = 100
    np.random.seed(42)

    # ポートフォリオパラメータ
    spots = np.random.uniform(80, 120, n)
    strikes = np.random.uniform(80, 120, n)
    times = np.random.uniform(0.1, 2.0, n)
    rates = np.full(n, 0.05)
    sigmas = np.random.uniform(0.1, 0.4, n)
    is_calls = np.full(n, True)  # すべてコールオプション

    results = {}

    # 1. Pure Python実装（forループ、有限差分）
    start = time.perf_counter()
    for i in range(n):
        # 価格計算
        price = black_scholes_pure_python(spots[i], strikes[i], times[i], rates[i], sigmas[i])
        # 簡易的なGreeks計算（有限差分）
        h = 0.01
        price_up = black_scholes_pure_python(spots[i] + h, strikes[i], times[i], rates[i], sigmas[i])
        _ = (price_up - price) / h  # Delta計算（結果は使用しない）
    pure_python_time = time.perf_counter() - start
    results["pure_python_ms"] = pure_python_time * 1000

    # 2. NumPy+SciPy実装（ベクトル化）
    from benchmarks.baseline.iv_vectorized import black_scholes_vectorized, vega_vectorized

    start = time.perf_counter()
    # ベクトル化された価格計算
    prices = black_scholes_vectorized(spots, strikes, times, rates, sigmas, is_calls)
    # ベクトル化されたVega計算
    _ = vega_vectorized(spots, strikes, times, rates, sigmas)  # Vega計算（結果は使用しない）
    # Deltaの有限差分（ベクトル化）
    h = 0.01
    prices_up = black_scholes_vectorized(spots + h, strikes, times, rates, sigmas, is_calls)
    _ = (prices_up - prices) / h  # Delta計算（結果は使用しない）
    numpy_scipy_time = time.perf_counter() - start
    results["numpy_scipy_ms"] = numpy_scipy_time * 1000

    # 3. QuantForge実装（並列バッチ）
    try:
        from quantforge.models import black_scholes

        if hasattr(black_scholes, "greeks_batch"):
            start = time.perf_counter()
            _ = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, is_calls)  # Greeks計算
            qf_time = time.perf_counter() - start
            results["quantforge_ms"] = qf_time * 1000
    except ImportError:
        results["quantforge_ms"] = 0.0

    return results


def benchmark_portfolio_risk_large() -> dict[str, float]:
    """ポートフォリオリスク計算（大規模: 10,000オプション）."""

    n = 10000
    np.random.seed(42)

    # ポートフォリオパラメータ
    spots = np.random.uniform(80, 120, n)
    strikes = np.random.uniform(80, 120, n)
    times = np.random.uniform(0.1, 2.0, n)
    rates = np.full(n, 0.05)
    sigmas = np.random.uniform(0.1, 0.4, n)
    is_calls = np.full(n, True)  # すべてコールオプション

    results = {}

    # 1. NumPy+SciPy実装（ベクトル化）
    from benchmarks.baseline.iv_vectorized import black_scholes_vectorized, vega_vectorized

    start = time.perf_counter()
    # ベクトル化された価格計算
    prices = black_scholes_vectorized(spots, strikes, times, rates, sigmas, is_calls)
    # ベクトル化されたVega計算
    _ = vega_vectorized(spots, strikes, times, rates, sigmas)  # Vega計算（結果は使用しない）
    # Deltaの有限差分（ベクトル化）
    h = 0.01
    prices_up = black_scholes_vectorized(spots + h, strikes, times, rates, sigmas, is_calls)
    _ = (prices_up - prices) / h  # Delta計算（結果は使用しない）
    numpy_scipy_time = time.perf_counter() - start
    results["numpy_scipy_ms"] = numpy_scipy_time * 1000

    # 2. QuantForge実装（並列バッチ）
    try:
        from quantforge.models import black_scholes

        if hasattr(black_scholes, "greeks_batch"):
            start = time.perf_counter()
            _ = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, is_calls)  # Greeks計算
            qf_time = time.perf_counter() - start
            results["quantforge_ms"] = qf_time * 1000
    except ImportError:
        results["quantforge_ms"] = 0.0

    # Pure Pythonは時間がかかりすぎるため除外

    return results


def main() -> None:
    """メインエントリーポイント."""

    print("🚀 実践シナリオベンチマーク開始...")

    results: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "volatility_surface": {"small": {}, "large": {}},
        "portfolio_risk": {"small": {}, "large": {}},
    }

    # ボラティリティサーフェス
    print("\n📊 ボラティリティサーフェス構築...")
    print("  小規模（10×10 = 100点）測定中...")
    results["volatility_surface"]["small"] = benchmark_volatility_surface_small()

    print("  大規模（100×100 = 10,000点）測定中...")
    results["volatility_surface"]["large"] = benchmark_volatility_surface_large()

    # ポートフォリオリスク
    print("\n📊 ポートフォリオリスク計算...")
    print("  小規模（100オプション）測定中...")
    results["portfolio_risk"]["small"] = benchmark_portfolio_risk_small()

    print("  大規模（10,000オプション）測定中...")
    results["portfolio_risk"]["large"] = benchmark_portfolio_risk_large()

    # 結果保存
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_DIR / "practical_scenarios.json", "w") as f:
        json.dump(results, f, indent=2)

    # サマリー表示
    print("\n=== 実践シナリオ結果サマリー ===")

    print("\nボラティリティサーフェス（小規模 100点）:")
    vol_small = results["volatility_surface"]["small"]
    if vol_small.get("pure_python_ms"):
        print(f"  Pure Python: {vol_small['pure_python_ms']:.1f} ms")
    if vol_small.get("numpy_scipy_ms"):
        print(f"  NumPy+SciPy (vectorized): {vol_small['numpy_scipy_ms']:.1f} ms")
    if vol_small.get("quantforge_ms"):
        print(f"  QuantForge: {vol_small['quantforge_ms']:.1f} ms")

    print("\nボラティリティサーフェス（大規模 10,000点）:")
    vol_large = results["volatility_surface"]["large"]
    if vol_large.get("numpy_scipy_ms"):
        print(f"  NumPy+SciPy (vectorized): {vol_large['numpy_scipy_ms']:.1f} ms")
    if vol_large.get("quantforge_ms"):
        print(f"  QuantForge: {vol_large['quantforge_ms']:.1f} ms")

    print("\nポートフォリオリスク（小規模 100オプション）:")
    risk_small = results["portfolio_risk"]["small"]
    if risk_small.get("pure_python_ms"):
        print(f"  Pure Python: {risk_small['pure_python_ms']:.1f} ms")
    if risk_small.get("numpy_scipy_ms"):
        print(f"  NumPy+SciPy (vectorized): {risk_small['numpy_scipy_ms']:.1f} ms")
    if risk_small.get("quantforge_ms"):
        print(f"  QuantForge: {risk_small['quantforge_ms']:.1f} ms")

    print("\nポートフォリオリスク（大規模 10,000オプション）:")
    risk_large = results["portfolio_risk"]["large"]
    if risk_large.get("numpy_scipy_ms"):
        print(f"  NumPy+SciPy (vectorized): {risk_large['numpy_scipy_ms']:.1f} ms")
    if risk_large.get("quantforge_ms"):
        print(f"  QuantForge: {risk_large['quantforge_ms']:.1f} ms")

    print("\n✅ 実践シナリオベンチマーク完了")


if __name__ == "__main__":
    main()

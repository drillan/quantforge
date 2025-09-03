"""Black-Scholes計算の包括的統合テスト."""

import numpy as np
import pytest
from quantforge import black_scholes
from scipy import stats

from tests.conftest import PRACTICAL_TOLERANCE, THEORETICAL_TOLERANCE


@pytest.mark.integration
class TestBlackScholesIntegration:
    """Black-Scholes価格計算の統合テスト."""

    def test_reference_values(self) -> None:
        """業界標準の参照値との比較."""
        # erfベース高精度実装による正確な値に更新（2025-01-25）
        test_cases = [
            # (S, K, T, r, σ, expected_price)
            (100.0, 100.0, 1.0, 0.05, 0.20, 10.450583572185567),
            (100.0, 100.0, 0.5, 0.05, 0.20, 6.888728577680624),
            (100.0, 100.0, 2.0, 0.05, 0.20, 16.126779724978633),
            (100.0, 90.0, 1.0, 0.05, 0.20, 16.699448408416004),
            (100.0, 110.0, 1.0, 0.05, 0.20, 6.040088129724239),
            (100.0, 100.0, 1.0, 0.10, 0.20, 13.269676584660893),
            (100.0, 100.0, 1.0, 0.05, 0.30, 14.231254785985819),
            (100.0, 100.0, 1.0, 0.05, 0.10, 6.804957708822144),
        ]

        for s, k, t, r, v, expected in test_cases:
            price = black_scholes.call_price(s, k, t, r, v)
            # norm_cdfの実装精度を考慮した検証
            assert abs(price - expected) < THEORETICAL_TOLERANCE, f"価格不一致: S={s}, K={k}, T={t}, r={r}, σ={v}"

    def test_moneyness_relationship(self) -> None:
        """マネーネスによる価格関係のテスト."""
        t = 1.0
        r = 0.05
        sigma = 0.2

        # ITM (In The Money)
        itm_price = black_scholes.call_price(110.0, 100.0, t, r, sigma)

        # ATM (At The Money)
        atm_price = black_scholes.call_price(100.0, 100.0, t, r, sigma)

        # OTM (Out of The Money)
        otm_price = black_scholes.call_price(90.0, 100.0, t, r, sigma)

        # ITM > ATM > OTM
        assert itm_price > atm_price > otm_price, "マネーネスによる価格順序が不正"

        # ITMは本質的価値以上
        intrinsic_itm = 110.0 - 100.0 * np.exp(-r * t)
        assert itm_price >= intrinsic_itm, "ITMが本質的価値を下回る"

    def test_time_decay(self) -> None:
        """時間減衰（シータ）のテスト."""
        s = 100.0
        k = 100.0
        r = 0.05
        sigma = 0.2

        times = [2.0, 1.5, 1.0, 0.5, 0.25, 0.1]
        prices = [black_scholes.call_price(s, k, t, r, sigma) for t in times]

        # 満期が近づくと価格は減少（ATMの場合）
        for i in range(1, len(prices)):
            assert prices[i] < prices[i - 1], f"時間減衰が不正: {times[i]}"

    def test_volatility_impact(self) -> None:
        """ボラティリティの影響（ベガ）のテスト."""
        s = 100.0
        k = 100.0
        t = 1.0
        r = 0.05

        vols = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
        prices = [black_scholes.call_price(s, k, t, r, vol) for vol in vols]

        # ボラティリティが増加すると価格も増加
        for i in range(1, len(prices)):
            assert prices[i] > prices[i - 1], f"ボラティリティ感応度が不正: {vols[i]}"

    def test_interest_rate_impact(self) -> None:
        """金利の影響（ロー）のテスト."""
        s = 100.0
        k = 100.0
        t = 1.0
        sigma = 0.2

        rates = [-0.02, 0.0, 0.02, 0.05, 0.10, 0.15]
        prices = [black_scholes.call_price(s, k, t, r, sigma) for r in rates]

        # 金利が増加するとコール価格も増加
        for i in range(1, len(prices)):
            assert prices[i] > prices[i - 1], f"金利感応度が不正: {rates[i]}"

    def test_deep_itm_otm(self) -> None:
        """Deep ITM/OTMの極限値テスト."""
        t = 1.0
        r = 0.05
        sigma = 0.2

        # Deep ITM: 価格 ≈ S - K*exp(-rT)
        deep_itm = black_scholes.call_price(200.0, 50.0, t, r, sigma)
        intrinsic = 200.0 - 50.0 * np.exp(-r * t)
        assert abs(deep_itm - intrinsic) < 0.01, "Deep ITMが本質的価値に収束していない"

        # Deep OTM: 価格 ≈ 0
        deep_otm = black_scholes.call_price(50.0, 200.0, t, r, sigma)
        assert deep_otm < 0.001, "Deep OTMがゼロに収束していない"

    def test_batch_vs_single_consistency(self) -> None:
        """バッチ処理と単一処理の一貫性テスト."""
        np.random.seed(42)
        n = 1000

        spots = np.random.uniform(50, 150, n)
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        # バッチ処理
        batch_prices = black_scholes.call_price_batch(spots, k, t, r, sigma)

        # 単一処理との比較（サンプリング）
        sample_indices = np.random.choice(n, 100, replace=False)
        for idx in sample_indices:
            single_price = black_scholes.call_price(spots[idx], k, t, r, sigma)
            # Convert Arrow scalar to Python float if needed
            batch_val = batch_prices[idx]
            if hasattr(batch_val, "as_py"):
                batch_val = batch_val.as_py()
            assert abs(float(batch_val) - single_price) < PRACTICAL_TOLERANCE, f"バッチと単一の不一致: {idx}"

    def test_large_scale_batch(self) -> None:
        """大規模バッチ処理のテスト."""
        n = 1000000
        spots = np.random.uniform(50, 150, n)
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        prices = black_scholes.call_price_batch(spots, k, t, r, sigma)

        assert len(prices) == n, "バッチサイズが不正"

        # Convert Arrow result to numpy if needed
        if hasattr(prices, "to_numpy"):
            prices_np = prices.to_numpy()
        else:
            prices_np = np.array([float(p.as_py()) if hasattr(p, "as_py") else float(p) for p in prices])

        assert np.all(prices_np >= 0), "負の価格が存在"
        assert np.all(np.isfinite(prices_np)), "無限大またはNaNが存在"

        # 統計的性質の確認
        mean_price = np.mean(prices_np)
        std_price = np.std(prices_np)
        assert 15 < mean_price < 20, f"平均価格が異常: {mean_price}"  # erf実装での正確な値: ~17
        assert std_price > 0, "価格の分散がゼロ"

    def test_price_continuity(self) -> None:
        """価格の連続性テスト."""
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        # スポット価格の小さな変化
        spots = np.linspace(99.9, 100.1, 21)
        prices = [black_scholes.call_price(s, k, t, r, sigma) for s in spots]

        # 価格変化の滑らかさを確認
        for i in range(1, len(prices)):
            price_diff = abs(prices[i] - prices[i - 1])
            spot_diff = spots[i] - spots[i - 1]
            # デルタは通常0から1の範囲
            delta_approx = price_diff / spot_diff
            assert 0 <= delta_approx <= 1.1, f"価格変化が不連続: {i}"

    def test_term_structure(self) -> None:
        """満期構造のテスト."""
        s = 100.0
        k = 100.0
        r = 0.05
        sigma = 0.2

        # 満期までの時間
        terms = np.logspace(-3, 1, 50)  # 0.001から10年
        prices = [black_scholes.call_price(s, k, t, r, sigma) for t in terms]

        # 満期が長いほど価格は高い（一般的に）
        for i in range(1, len(prices)):
            assert prices[i] >= prices[i - 1] - PRACTICAL_TOLERANCE, f"満期構造が不正: {terms[i]}"

        # 長期限での収束
        long_term_price = prices[-1]
        assert long_term_price < s, "長期限で株価を超える"

    def test_volatility_smile_preparation(self) -> None:
        """ボラティリティスマイル検証の準備."""
        s = 100.0
        t = 1.0
        r = 0.05

        # 異なる行使価格での暗黙のボラティリティ（将来の実装用）
        strikes = [80, 90, 100, 110, 120]
        base_vol = 0.2

        prices = []
        for k in strikes:
            # 現在は固定ボラティリティ
            price = black_scholes.call_price(s, k, t, r, base_vol)
            prices.append(price)

        # 価格は行使価格に対して単調減少
        for i in range(1, len(prices)):
            assert prices[i] < prices[i - 1], f"価格順序が不正: K={strikes[i]}"


@pytest.mark.integration
class TestBlackScholesAccuracy:
    """Black-Scholes計算精度の詳細テスト."""

    def test_comparison_with_scipy(self) -> None:
        """SciPy実装との詳細比較."""
        np.random.seed(42)
        n_tests = 1000

        max_rel_error = 0.0
        max_abs_error = 0.0

        for _ in range(n_tests):
            s = np.random.uniform(50, 150)
            k = np.random.uniform(50, 150)
            t = np.random.uniform(0.01, 5.0)
            r = np.random.uniform(-0.05, 0.15)
            sigma = np.random.uniform(0.05, 0.5)

            # QuantForge実装
            qf_price = black_scholes.call_price(s, k, t, r, sigma)

            # SciPy参照実装
            d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
            d2 = d1 - sigma * np.sqrt(t)
            scipy_price = s * stats.norm.cdf(d1) - k * np.exp(-r * t) * stats.norm.cdf(d2)

            abs_error = abs(qf_price - scipy_price)
            rel_error = abs_error / max(scipy_price, PRACTICAL_TOLERANCE)

            max_abs_error = max(max_abs_error, abs_error)
            max_rel_error = max(max_rel_error, rel_error)

        # 精度要件: 相対誤差（理論精度レベル）
        assert max_rel_error < THEORETICAL_TOLERANCE, f"最大相対誤差が大きすぎる: {max_rel_error}"
        assert max_abs_error < 0.001, f"最大絶対誤差が大きすぎる: {max_abs_error}"

    def test_numerical_stability_extreme_cases(self) -> None:
        """極端なケースでの数値安定性."""
        test_cases = [
            # 非常に短い満期
            (100.0, 100.0, 0.001, 0.05, 0.2),
            # 非常に長い満期
            (100.0, 100.0, 50.0, 0.05, 0.2),
            # 非常に低いボラティリティ
            (100.0, 100.0, 1.0, 0.05, 0.005),
            # 非常に高いボラティリティ
            (100.0, 100.0, 1.0, 0.05, 5.0),
            # 極端なマネーネス
            (1000.0, 1.0, 1.0, 0.05, 0.2),
            (1.0, 1000.0, 1.0, 0.05, 0.2),
        ]

        for s, k, t, r, v in test_cases:
            price = black_scholes.call_price(s, k, t, r, v)
            assert np.isfinite(price), f"無限大またはNaN: S={s}, K={k}, T={t}, r={r}, σ={v}"
            assert price >= 0, f"負の価格: S={s}, K={k}, T={t}, r={r}, σ={v}"

            # 価格境界のチェック
            intrinsic = max(s - k * np.exp(-r * t), 0)
            assert price >= intrinsic - PRACTICAL_TOLERANCE, f"本質的価値を下回る: {price} < {intrinsic}"
            assert price <= s, f"株価を超える: {price} > {s}"

    def test_greeks_finite_difference(self) -> None:
        """有限差分によるグリークスの近似テスト."""
        s = 100.0
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        base_price = black_scholes.call_price(s, k, t, r, sigma)

        # デルタ（∂C/∂S）
        ds = 0.01
        price_up = black_scholes.call_price(s + ds, k, t, r, sigma)
        delta = (price_up - base_price) / ds
        assert 0 <= delta <= 1, f"デルタが範囲外: {delta}"

        # ベガ（∂C/∂σ）
        dv = 0.001
        price_vol_up = black_scholes.call_price(s, k, t, r, sigma + dv)
        vega = (price_vol_up - base_price) / dv
        assert vega > 0, f"ベガが負: {vega}"

        # シータ（-∂C/∂T）
        dt = 0.01
        price_time_down = black_scholes.call_price(s, k, t - dt, r, sigma)
        theta = -(base_price - price_time_down) / dt
        # ATMオプションのシータは通常負
        assert theta < 0, f"シータが正: {theta}"

        # ロー（∂C/∂r）
        dr = 0.001
        price_rate_up = black_scholes.call_price(s, k, t, r + dr, sigma)
        rho = (price_rate_up - base_price) / dr
        assert rho > 0, f"ローが負: {rho}"


@pytest.mark.integration
class TestMarketScenarios:
    """実際の市場シナリオのテスト."""

    def test_equity_index_options(self) -> None:
        """株価指数オプションのシナリオ."""
        # S&P 500のような指数オプション
        s = 4500.0  # 現在の指数レベル
        strikes = [4000, 4250, 4500, 4750, 5000]  # 様々な行使価格
        t = 30 / 365  # 30日満期
        r = 0.045  # 現在の金利水準
        sigma = 0.15  # 暗黙のボラティリティ

        prices = []
        for k in strikes:
            price = black_scholes.call_price(s, k, t, r, sigma)
            prices.append(price)

            # 価格の妥当性チェック
            intrinsic = max(s - k, 0)
            assert price >= intrinsic, f"本質的価値を下回る: K={k}"
            assert price <= s, f"理論上限を超える: K={k}"  # コールの最大値はスポット価格

        # 価格は行使価格に対して単調減少
        for i in range(1, len(prices)):
            assert prices[i] < prices[i - 1], f"価格順序が不正: K={strikes[i]}"

    def test_fx_options(self) -> None:
        """外国為替オプションのシナリオ."""
        # USD/JPY オプション
        s = 150.0  # 現在のレート
        k = 150.0  # ATM
        t = 90 / 365  # 3ヶ月満期
        r_domestic = 0.05  # USD金利
        r_foreign = -0.001  # JPY金利（負金利）
        v = 0.10  # FXボラティリティ

        # 調整後の金利（r - r_foreign）
        r_adjusted = r_domestic - r_foreign

        price = black_scholes.call_price(s, k, t, r_adjusted, v)

        # FXオプションの特性確認
        assert price > 0, "FXオプション価格が負"
        assert price < s * 0.1, "FXオプション価格が高すぎる（10%以上）"

    def test_commodity_options(self) -> None:
        """商品オプションのシナリオ."""
        # 原油オプション
        s = 75.0  # バレル当たり価格
        k = 80.0  # OTM コール
        t = 180 / 365  # 6ヶ月満期
        r = 0.04
        sigma = 0.35  # 商品の高ボラティリティ

        price = black_scholes.call_price(s, k, t, r, sigma)

        # 商品オプションの特性
        assert price > 0, "商品オプション価格が負"
        # 高ボラティリティのため、OTMでも価値がある
        assert price > 1.0, "高ボラティリティ商品のOTM価値が低すぎる"

    def test_stress_scenarios(self) -> None:
        """ストレスシナリオのテスト."""
        # 市場ストレス時のパラメータ
        scenarios = [
            # (名前, S, K, T, r, σ)
            ("パンデミック", 100.0, 100.0, 1.0, 0.001, 0.80),  # 超高ボラティリティ
            ("金融危機", 100.0, 100.0, 1.0, -0.02, 0.60),  # 負金利、高ボラティリティ
            ("バブル崩壊", 50.0, 100.0, 1.0, 0.05, 0.40),  # 大幅下落後
            ("流動性危機", 100.0, 100.0, 0.01, 0.05, 0.50),  # 超短期、高ボラティリティ
        ]

        for name, s, k, t, r, sigma in scenarios:
            price = black_scholes.call_price(s, k, t, r, sigma)
            assert np.isfinite(price), f"{name}: 価格が無限大またはNaN"
            assert price >= 0, f"{name}: 価格が負"

            # ストレス時でも価格境界は守られる
            intrinsic = max(s - k * np.exp(-r * t), 0)
            assert price >= intrinsic - PRACTICAL_TOLERANCE, f"{name}: 本質的価値を下回る"

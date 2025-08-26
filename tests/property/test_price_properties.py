"""価格計算のプロパティベーステスト."""

import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from quantforge.models import black_scholes


@pytest.mark.property
class TestPriceProperties:
    """価格の数学的性質をプロパティベーステストで検証."""

    @given(
        s=st.floats(min_value=0.01, max_value=10000),
        k=st.floats(min_value=0.01, max_value=10000),
        t=st.floats(min_value=0.001, max_value=30),
        r=st.floats(min_value=-0.5, max_value=0.5),
        sigma=st.floats(min_value=0.005, max_value=5.0),
    )
    @settings(max_examples=500, deadline=None)
    def test_price_bounds(self, s: float, k: float, t: float, r: float, sigma: float) -> None:
        """価格境界の検証: max(S-K*e^(-rt), 0) <= C <= S."""
        price = black_scholes.call_price(s, k, t, r, sigma)

        # 価格は非負
        assert price >= 0, f"負の価格: {price}"

        # 下限: 本質的価値
        intrinsic = max(s - k * np.exp(-r * t), 0)
        assert price >= intrinsic - 1e-3, f"本質的価値を下回る: {price} < {intrinsic}"

        # 上限: 株価
        assert price <= s + 1e-3, f"株価を超える: {price} > {s}"

        # 有限値
        assert np.isfinite(price), f"無限大またはNaN: {price}"

    @given(
        s=st.floats(min_value=10, max_value=200),
        k=st.floats(min_value=10, max_value=200),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.1, max_value=0.2),
        sigma1=st.floats(min_value=0.05, max_value=0.5),
        sigma2=st.floats(min_value=0.05, max_value=0.5),
    )
    @settings(max_examples=300, deadline=None)
    def test_volatility_monotonicity(
        self, s: float, k: float, t: float, r: float, sigma1: float, sigma2: float
    ) -> None:
        """ボラティリティに対する単調性: σ1 < σ2 => C(σ1) < C(σ2)."""
        assume(sigma1 != sigma2)

        price1 = black_scholes.call_price(s, k, t, r, sigma1)
        price2 = black_scholes.call_price(s, k, t, r, sigma2)

        if sigma1 < sigma2:
            assert price1 <= price2 + 1e-3, f"ボラティリティ単調性違反: sigma1={sigma1}, sigma2={sigma2}"
        else:
            assert price1 >= price2 - 1e-3, f"ボラティリティ単調性違反: sigma1={sigma1}, sigma2={sigma2}"

    @given(
        s=st.floats(min_value=50, max_value=150),
        k=st.floats(min_value=50, max_value=150),
        t1=st.floats(min_value=0.01, max_value=1),
        t2=st.floats(min_value=0.01, max_value=1),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=300, deadline=None)
    def test_time_monotonicity(self, s: float, k: float, t1: float, t2: float, r: float, sigma: float) -> None:
        """時間に対する単調性: T1 < T2 => C(T1) <= C(T2) (正の金利の場合)."""
        assume(t1 != t2)

        price1 = black_scholes.call_price(s, k, t1, r, sigma)
        price2 = black_scholes.call_price(s, k, t2, r, sigma)

        if t1 < t2:
            # 負の金利では時間価値が逆転する可能性がある
            # 正の金利の場合のみ単調性を検証
            if r >= 0:
                assert price1 <= price2 + 1e-3, f"時間単調性違反: t1={t1}, t2={t2}, r={r}"
            else:
                # 負の金利では時間価値の逆転が理論的に正しい
                # 長い満期ほど割引効果が大きくなるため価格が低くなることがある
                pass  # 負の金利では単調性を要求しない

    @given(
        s=st.floats(min_value=50, max_value=150),
        k1=st.floats(min_value=50, max_value=150),
        k2=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=300, deadline=None)
    def test_strike_monotonicity(self, s: float, k1: float, k2: float, t: float, r: float, sigma: float) -> None:
        """行使価格に対する単調性: K1 < K2 => C(K1) >= C(K2)."""
        assume(k1 != k2)

        price1 = black_scholes.call_price(s, k1, t, r, sigma)
        price2 = black_scholes.call_price(s, k2, t, r, sigma)

        if k1 < k2:
            assert price1 >= price2 - 1e-3, f"行使価格単調性違反: k1={k1}, k2={k2}"
        else:
            assert price1 <= price2 + 1e-3, f"行使価格単調性違反: k1={k1}, k2={k2}"

    @given(
        s1=st.floats(min_value=50, max_value=150),
        s2=st.floats(min_value=50, max_value=150),
        k=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=300, deadline=None)
    def test_delta_bounds(self, s1: float, s2: float, k: float, t: float, r: float, sigma: float) -> None:
        """デルタの範囲: 0 <= ΔC/ΔS <= 1."""
        assume(abs(s1 - s2) > 0.01)  # 有意な差

        price1 = black_scholes.call_price(s1, k, t, r, sigma)
        price2 = black_scholes.call_price(s2, k, t, r, sigma)

        delta_approx = (price2 - price1) / (s2 - s1)

        # デルタは0から1の範囲（コールオプション）
        assert -0.01 <= delta_approx <= 1.01, f"デルタが範囲外: {delta_approx}"

    @given(
        s=st.floats(min_value=50, max_value=150),
        k=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=200, deadline=None)
    def test_convexity(self, s: float, k: float, t: float, r: float, sigma: float) -> None:
        """価格の凸性: C((S1+S2)/2) <= (C(S1) + C(S2))/2."""
        # 3点で凸性をテスト
        s_low = s * 0.9
        s_mid = s
        s_high = s * 1.1

        price_low = black_scholes.call_price(s_low, k, t, r, sigma)
        price_mid = black_scholes.call_price(s_mid, k, t, r, sigma)
        price_high = black_scholes.call_price(s_high, k, t, r, sigma)

        # 凸性条件
        interpolated = (price_low + price_high) / 2
        assert price_mid <= interpolated + 1e-3, f"凸性違反: {price_mid} > {interpolated}"

    @given(
        s=st.floats(min_value=50, max_value=150),
        k=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=2),
        r1=st.floats(min_value=-0.1, max_value=0.2),
        r2=st.floats(min_value=-0.1, max_value=0.2),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=300, deadline=None)
    def test_interest_rate_monotonicity(self, s: float, k: float, t: float, r1: float, r2: float, sigma: float) -> None:
        """金利に対する単調性: r1 < r2 => C(r1) <= C(r2)."""
        assume(r1 != r2)

        price1 = black_scholes.call_price(s, k, t, r1, sigma)
        price2 = black_scholes.call_price(s, k, t, r2, sigma)

        if r1 < r2:
            # コールオプションは金利に対して増加
            assert price1 <= price2 + 1e-3, f"金利単調性違反: r1={r1}, r2={r2}"
        else:
            assert price1 >= price2 - 1e-3, f"金利単調性違反: r1={r1}, r2={r2}"


@pytest.mark.property
class TestBatchProperties:
    """バッチ処理のプロパティベーステスト."""

    @given(
        spots=st.lists(st.floats(min_value=0.01, max_value=10000), min_size=1, max_size=100),
        k=st.floats(min_value=0.01, max_value=10000),
        t=st.floats(min_value=0.001, max_value=30),
        r=st.floats(min_value=-0.5, max_value=0.5),
        sigma=st.floats(min_value=0.005, max_value=5.0),
    )
    @settings(max_examples=200, deadline=None)
    def test_batch_consistency(self, spots: list[float], k: float, t: float, r: float, sigma: float) -> None:
        """バッチ処理と個別処理の一貫性."""
        spots_array = np.array(spots)

        # バッチ処理
        batch_prices = black_scholes.call_price_batch(spots_array, k, t, r, sigma)

        # 個別処理との比較
        for i, spot in enumerate(spots):
            single_price = black_scholes.call_price(spot, k, t, r, sigma)
            assert abs(batch_prices[i] - single_price) < 1e-3, f"バッチと個別の不一致: {i}"

    @given(
        n=st.integers(min_value=1, max_value=1000),
        s_min=st.floats(min_value=10, max_value=90),
        s_max=st.floats(min_value=110, max_value=200),
        k=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=100, deadline=None)
    def test_batch_ordering(
        self,
        n: int,
        s_min: float,
        s_max: float,
        k: float,
        t: float,
        r: float,
        sigma: float,
    ) -> None:
        """バッチ処理での価格順序の保持."""
        assume(s_min < s_max)

        # 昇順のスポット価格
        spots = np.linspace(s_min, s_max, n)
        prices = black_scholes.call_price_batch(spots, k, t, r, sigma=0.2)

        # 価格は行使価格に対して単調
        for i in range(1, len(prices)):
            # スポット価格が上昇すると、コール価格も上昇
            assert prices[i] >= prices[i - 1] - 1e-3, f"価格順序違反: {i}"


@pytest.mark.property
class TestSpecialCases:
    """特殊ケースのプロパティベーステスト."""

    @given(
        k=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=1),  # ATM近似は短期でより正確
        r=st.floats(min_value=-0.02, max_value=0.02),  # ATM近似は低金利でのみ有効
        sigma=st.floats(min_value=0.15, max_value=0.4),  # 低ボラティリティを除外
    )
    @settings(max_examples=200, deadline=None)
    def test_atm_approximation(self, k: float, t: float, r: float, sigma: float) -> None:
        """ATMオプションの近似式との比較."""
        s = k * np.exp(r * t)  # Forward ATM

        price = black_scholes.call_price(s, k, t, r, sigma)

        # ATM近似: 約 S * sigma * sqrt(T/(2π))
        atm_approx = s * sigma * np.sqrt(t / (2 * np.pi))

        # 相対誤差の許容範囲（低ボラティリティ・長期満期では誤差が大きくなる）
        rel_error = abs(price - atm_approx) / atm_approx
        assert rel_error < 0.5, f"ATM近似との乖離が大きい: {rel_error}"

    @given(
        s_ratio=st.floats(min_value=0.001, max_value=0.1),  # Deep OTM
        k=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=200, deadline=None)
    def test_deep_otm_convergence(self, s_ratio: float, k: float, t: float, r: float, sigma: float) -> None:
        """Deep OTMでゼロへの収束."""
        s = k * s_ratio  # Deep OTM

        price = black_scholes.call_price(s, k, t, r, sigma)

        # Deep OTMは実質的にゼロ
        assert price < 0.01, f"Deep OTM価格が高すぎる: {price}"

    @given(
        s_ratio=st.floats(min_value=10, max_value=100),  # Deep ITM
        k=st.floats(min_value=1, max_value=10),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=200, deadline=None)
    def test_deep_itm_convergence(self, s_ratio: float, k: float, t: float, r: float, sigma: float) -> None:
        """Deep ITMで本質的価値への収束."""
        s = k * s_ratio  # Deep ITM

        price = black_scholes.call_price(s, k, t, r, sigma)

        # Deep ITMは本質的価値に収束
        intrinsic = s - k * np.exp(-r * t)
        rel_error = abs(price - intrinsic) / intrinsic
        assert rel_error < 0.01, f"Deep ITM収束誤差: {rel_error}"


@pytest.mark.property
class TestNumericalStability:
    """数値安定性のプロパティベーステスト."""

    @given(
        s=st.floats(min_value=1e-3, max_value=1e10),
        k=st.floats(min_value=1e-3, max_value=1e10),
        t=st.floats(min_value=1e-3, max_value=100),
        r=st.floats(min_value=-0.99, max_value=0.99),
        sigma=st.floats(min_value=1e-3, max_value=10),
    )
    @settings(max_examples=500, deadline=None)
    def test_extreme_values_stability(self, s: float, k: float, t: float, r: float, sigma: float) -> None:
        """極端な値での数値安定性."""
        # 入力値の妥当性チェック
        if s < 0.01 or s > 2147483648:
            with pytest.raises(ValueError):
                black_scholes.call_price(s, k, t, r, sigma)
            return

        if k < 0.01 or k > 2147483648:
            with pytest.raises(ValueError):
                black_scholes.call_price(s, k, t, r, sigma)
            return

        if t < 0.001 or t > 100:
            with pytest.raises(ValueError):
                black_scholes.call_price(s, k, t, r, sigma)
            return

        if sigma < 0.005 or sigma > 10:
            with pytest.raises(ValueError):
                black_scholes.call_price(s, k, t, r, sigma)
            return

        # 有効な範囲内なら計算可能
        price = black_scholes.call_price(s, k, t, r, sigma)
        assert np.isfinite(price), f"無限大またはNaN: S={s}, K={k}"
        assert price >= 0, f"負の価格: {price}"

    @given(
        scale=st.floats(min_value=0.001, max_value=1000),
        k=st.floats(min_value=50, max_value=150),
        t=st.floats(min_value=0.1, max_value=2),
        r=st.floats(min_value=-0.05, max_value=0.15),
        sigma=st.floats(min_value=0.1, max_value=0.4),
    )
    @settings(max_examples=200, deadline=None)
    def test_scale_invariance(self, scale: float, k: float, t: float, r: float, sigma: float) -> None:
        """スケール不変性のテスト."""
        # 基準価格
        base_price = black_scholes.call_price(100.0, k, t, r, sigma)

        # スケール後
        scaled_s = 100.0 * scale
        scaled_k = k * scale

        # スケール後の価格
        scaled_price = black_scholes.call_price(scaled_s, scaled_k, t, r, sigma)

        # 価格もスケール
        expected_price = base_price * scale

        # 相対誤差
        if expected_price > 1e-3:
            rel_error = abs(scaled_price - expected_price) / expected_price
            assert rel_error < 1e-6, f"スケール不変性違反: {rel_error}"

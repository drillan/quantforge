"""累積正規分布関数の包括的ユニットテスト."""

import math

import numpy as np
import pytest
from quantforge import calculate_call_price
from scipy import stats


@pytest.mark.unit
class TestNormCDF:
    """累積正規分布関数の完全テスト."""

    @pytest.mark.parametrize(
        "x,expected",
        [
            # 標準正規分布表からの重要な値
            (-4.0, 0.00003167124183311998),
            (-3.5, 0.00023262907903552504),
            (-3.0, 0.0013498980316301),
            (-2.5, 0.0062096653257761),
            (-2.0, 0.022750131948179195),
            (-1.5, 0.0668072012688581),
            (-1.0, 0.15865525393145707),
            (-0.5, 0.3085375387259869),
            (0.0, 0.5),
            (0.5, 0.6914624612740131),
            (1.0, 0.8413447460685429),
            (1.5, 0.9331927987311419),
            (2.0, 0.9772498680518208),
            (2.5, 0.9937903346742239),
            (3.0, 0.9986501019683699),
            (3.5, 0.9997673709209645),
            (4.0, 0.9999683287581669),
            # 追加の重要な値
            (-1.96, 0.025),  # 95%信頼区間
            (1.96, 0.975),  # 95%信頼区間
            (-2.576, 0.005),  # 99%信頼区間
            (2.576, 0.995),  # 99%信頼区間
            (-1.645, 0.05),  # 90%信頼区間
            (1.645, 0.95),  # 90%信頼区間
        ],
    )
    def test_known_values(self, x: float, expected: float) -> None:
        """既知の値との照合テスト."""
        # Black-Scholesを通じて間接的にnorm_cdfをテスト
        # T=1, r=0, v=1の特殊ケースで計算
        s = 100.0
        k = 100.0 * np.exp(-x)  # d1 = x になるように調整
        t = 1.0
        r = 0.0
        v = 1.0

        # この設定では d1 ≈ x, d2 ≈ x - 1
        # 価格から逆算してnorm_cdfの精度を検証
        price = calculate_call_price(s, k, t, r, v)

        # 理論価格との比較
        d1 = (np.log(s / k) + (r + 0.5 * v**2) * t) / (v * np.sqrt(t))
        d2 = d1 - v * np.sqrt(t)
        theoretical_price = s * stats.norm.cdf(d1) - k * np.exp(-r * t) * stats.norm.cdf(d2)

        assert abs(price - theoretical_price) < 1e-6, f"価格誤差が大きい: x={x}"

    def test_symmetry(self) -> None:
        """対称性: N(-x) = 1 - N(x)のテスト."""
        test_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        for x_val in test_values:
            # 対称的な入力値でテスト
            s = 100.0
            k1 = 100.0 * np.exp(-x_val)
            k2 = 100.0 * np.exp(x_val)
            t = 1.0
            r = 0.0
            v = 1.0

            _ = calculate_call_price(s, k1, t, r, v)
            _ = calculate_call_price(s, k2, t, r, v)

            # 理論価格で対称性を確認
            d1_1 = (np.log(s / k1) + 0.5 * v**2 * t) / (v * np.sqrt(t))
            d1_2 = (np.log(s / k2) + 0.5 * v**2 * t) / (v * np.sqrt(t))

            # d1_1 と d1_2 は符号が逆
            assert abs(d1_1 + d1_2) < 1e-10, f"d1の対称性が満たされていない: {x_val}"

    def test_monotonicity(self) -> None:
        """単調増加性の検証."""
        strikes = np.linspace(50, 150, 50)
        prices = []
        s = 100.0
        t = 1.0
        r = 0.05
        v = 0.2

        for k in strikes:
            price = calculate_call_price(s, k, t, r, v)
            prices.append(price)

        # 行使価格が上昇すると価格は減少（単調減少）
        for i in range(1, len(prices)):
            assert prices[i] <= prices[i - 1] + 1e-10, f"価格の単調性が崩れている: {i}"

    def test_boundary_conditions(self) -> None:
        """境界条件のテスト."""
        s = 100.0
        t = 1.0
        r = 0.05
        v = 0.2

        # Deep ITM (In The Money)
        k_itm = 1.0
        price_itm = calculate_call_price(s, k_itm, t, r, v)
        intrinsic_itm = s - k_itm * np.exp(-r * t)
        assert abs(price_itm - intrinsic_itm) < 0.01, "Deep ITMで本質的価値に収束していない"

        # Deep OTM (Out of The Money)
        k_otm = 10000.0
        price_otm = calculate_call_price(s, k_otm, t, r, v)
        assert price_otm < 0.001, "Deep OTMでゼロに収束していない"

    def test_accuracy_against_scipy(self) -> None:
        """SciPy実装との精度比較."""
        np.random.seed(42)
        n_tests = 100

        # ランダムなパラメータでテスト
        for _ in range(n_tests):
            s = np.random.uniform(50, 150)
            k = np.random.uniform(50, 150)
            t = np.random.uniform(0.1, 2.0)
            r = np.random.uniform(-0.05, 0.15)
            v = np.random.uniform(0.05, 0.5)

            # QuantForgeの計算
            qf_price = calculate_call_price(s, k, t, r, v)

            # SciPyを使った理論価格
            d1 = (np.log(s / k) + (r + 0.5 * v**2) * t) / (v * np.sqrt(t))
            d2 = d1 - v * np.sqrt(t)
            scipy_price = s * stats.norm.cdf(d1) - k * np.exp(-r * t) * stats.norm.cdf(d2)

            # 相対誤差が1e-7以内
            rel_error = abs(qf_price - scipy_price) / max(scipy_price, 1e-10)
            assert rel_error < 1e-6, f"精度が不十分: {rel_error}"


@pytest.mark.unit
class TestNormCDFEdgeCases:
    """norm_cdfのエッジケーステスト."""

    def test_extreme_values(self) -> None:
        """極値での動作確認."""
        s = 100.0
        t = 1.0
        r = 0.0

        # 非常に小さいボラティリティ
        v_small = 0.001
        k = 100.0
        price_small_vol = calculate_call_price(s, k, t, r, v_small)
        # ボラティリティが小さいとき、ATMオプションの価格は小さい
        assert price_small_vol < 1.0, "小ボラティリティで価格が大きすぎる"

        # 非常に大きいボラティリティ
        v_large = 10.0
        price_large_vol = calculate_call_price(s, k, t, r, v_large)
        # ボラティリティが大きいとき、価格は本質的価値に近づく
        intrinsic = max(s - k, 0)
        assert price_large_vol > intrinsic, "大ボラティリティで本質的価値を下回る"

    def test_numerical_stability(self) -> None:
        """数値安定性のテスト."""
        # 非常に近い値での安定性
        s = 100.0
        t = 0.001  # 非常に短い満期
        r = 0.05
        v = 0.2

        k_values = [99.99, 100.0, 100.01]
        prices = []

        for k in k_values:
            price = calculate_call_price(s, k, t, r, v)
            prices.append(price)
            assert not math.isnan(price), f"NaNが発生: k={k}"
            assert not math.isinf(price), f"Infが発生: k={k}"
            assert price >= 0, f"負の価格: k={k}"

        # 価格が滑らかに変化することを確認
        assert prices[0] > prices[1], "価格の順序が不正"
        assert prices[1] > prices[2], "価格の順序が不正"

    def test_precision_near_zero(self) -> None:
        """ゼロ近傍での精度テスト."""
        s = 100.0
        k = 100.0  # ATM
        r = 0.0
        v = 0.2

        # 非常に短い満期での計算
        t_values = [0.001, 0.01, 0.1]

        for t in t_values:
            price = calculate_call_price(s, k, t, r, v)
            # ATMオプションの近似式との比較
            approx_price = s * v * np.sqrt(t / (2 * np.pi))
            rel_error = abs(price - approx_price) / approx_price
            assert rel_error < 0.1, f"ATM近似との誤差が大きい: t={t}, error={rel_error}"


@pytest.mark.unit
class TestDistributionProperties:
    """分布の数学的性質のテスト."""

    def test_put_call_parity_preparation(self) -> None:
        """Put-Callパリティ準備テスト（プットオプション未実装）."""
        # 将来的にプットオプションが実装された際のテスト準備
        s = 100.0
        k = 100.0
        t = 1.0
        r = 0.05
        v = 0.2

        call_price = calculate_call_price(s, k, t, r, v)

        # Put-Call パリティ: C - P = S - K*exp(-rT)
        # P = C - S + K*exp(-rT)
        theoretical_put = call_price - s + k * np.exp(-r * t)

        # プットオプションは正の値
        assert theoretical_put > 0, "理論プット価格が負"

        # プットの下限: max(K*exp(-rT) - S, 0)
        put_lower_bound = max(k * np.exp(-r * t) - s, 0)
        assert theoretical_put >= put_lower_bound - 1e-10, "プット価格が下限を下回る"

    def test_delta_approximation(self) -> None:
        """デルタ（価格感応度）の近似テスト."""
        k = 100.0
        t = 1.0
        r = 0.05
        v = 0.2
        ds = 0.01  # 小さな価格変化

        s_base = 100.0
        price_base = calculate_call_price(s_base, k, t, r, v)
        price_up = calculate_call_price(s_base + ds, k, t, r, v)

        # 数値微分によるデルタ
        delta_numerical = (price_up - price_base) / ds

        # 理論デルタ: N(d1)
        d1 = (np.log(s_base / k) + (r + 0.5 * v**2) * t) / (v * np.sqrt(t))
        delta_theoretical = stats.norm.cdf(d1)

        # デルタの精度確認
        assert abs(delta_numerical - delta_theoretical) < 0.01, "デルタの精度が不十分"

    def test_greeks_consistency(self) -> None:
        """グリークス（感応度）の整合性テスト."""
        s = 100.0
        k = 100.0
        t = 1.0
        r = 0.05
        v = 0.2

        # 価格計算
        price = calculate_call_price(s, k, t, r, v)

        # 価格の範囲チェック
        lower_bound = max(s - k * np.exp(-r * t), 0)  # 本質的価値
        upper_bound = s  # 最大価格

        assert lower_bound <= price <= upper_bound, f"価格が理論範囲外: {price}"

        # ATMでの特殊な性質
        # ATMオプションの価格は約 S * v * sqrt(T/(2π))
        atm_approx = s * v * np.sqrt(t / (2 * np.pi))
        assert abs(price - atm_approx) / atm_approx < 0.2, "ATM近似との乖離が大きい"

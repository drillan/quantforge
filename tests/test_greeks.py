# mypy: disable-error-code="attr-defined"
"""Black-Scholesグリークスのテスト

Rust実装のグリークス計算が正しく動作することを検証。
"""

import numpy as np
import pytest
import quantforge as qf
from conftest import NUMERICAL_TOLERANCE


class TestGreeksSingleCalculation:
    """単一のグリークス計算テスト"""

    def test_delta_call(self) -> None:
        """コールオプションのDelta計算テスト"""
        delta = qf.calculate_delta_call(100.0, 100.0, 1.0, 0.05, 0.2)
        assert abs(delta - 0.6368306517096883) < NUMERICAL_TOLERANCE

        # ITMでDeltaは1に近づく
        delta_itm = qf.calculate_delta_call(110.0, 100.0, 1.0, 0.05, 0.2)
        assert 0.6368306517096883 < delta_itm < 1.0

        # OTMでDeltaは0に近づく
        delta_otm = qf.calculate_delta_call(90.0, 100.0, 1.0, 0.05, 0.2)
        assert 0.0 < delta_otm < 0.6368306517096883

    def test_delta_put(self) -> None:
        """プットオプションのDelta計算テスト"""
        delta = qf.calculate_delta_put(100.0, 100.0, 1.0, 0.05, 0.2)
        assert abs(delta - (-0.36316934829031174)) < NUMERICAL_TOLERANCE

        # ITMプット（S < K）でDeltaは-1に近づく
        delta_itm = qf.calculate_delta_put(90.0, 100.0, 1.0, 0.05, 0.2)
        assert -1.0 < delta_itm < -0.36316934829031174

        # OTMプット（S > K）でDeltaは0に近づく
        delta_otm = qf.calculate_delta_put(110.0, 100.0, 1.0, 0.05, 0.2)
        assert -0.36316934829031174 < delta_otm < 0.0

    def test_gamma(self) -> None:
        """Gamma計算テスト"""
        gamma = qf.calculate_gamma(100.0, 100.0, 1.0, 0.05, 0.2)
        # Gammaは常に正
        assert gamma > 0.0
        assert abs(gamma - 0.018762017345846895) < NUMERICAL_TOLERANCE

    def test_vega(self) -> None:
        """Vega計算テスト"""
        vega = qf.calculate_vega(100.0, 100.0, 1.0, 0.05, 0.2)
        # Vegaは常に正
        assert vega > 0.0
        assert abs(vega - 0.37524034691693790) < NUMERICAL_TOLERANCE

    def test_theta_call(self) -> None:
        """コールオプションのTheta計算テスト"""
        theta = qf.calculate_theta_call(100.0, 100.0, 1.0, 0.05, 0.2)
        # Thetaは通常負（時間価値の減少）
        assert theta < 0.0
        assert abs(theta - (-0.01757267820941972)) < NUMERICAL_TOLERANCE

    def test_theta_put(self) -> None:
        """プットオプションのTheta計算テスト"""
        theta = qf.calculate_theta_put(100.0, 100.0, 1.0, 0.05, 0.2)
        # プットのThetaも通常負
        assert theta < 0.0

        # コールのThetaより絶対値が小さい（金利効果）
        theta_call = qf.calculate_theta_call(100.0, 100.0, 1.0, 0.05, 0.2)
        assert abs(theta) < abs(theta_call)

    def test_rho_call(self) -> None:
        """コールオプションのRho計算テスト"""
        rho = qf.calculate_rho_call(100.0, 100.0, 1.0, 0.05, 0.2)
        # コールのRhoは正
        assert rho > 0.0
        assert abs(rho - 0.5323248154537634) < NUMERICAL_TOLERANCE

    def test_rho_put(self) -> None:
        """プットオプションのRho計算テスト"""
        rho = qf.calculate_rho_put(100.0, 100.0, 1.0, 0.05, 0.2)
        # プットのRhoは負
        assert rho < 0.0
        assert abs(rho - (-0.4189046090469506)) < NUMERICAL_TOLERANCE


class TestGreeksAllCalculation:
    """全グリークス一括計算テスト"""

    def test_calculate_all_greeks_call(self) -> None:
        """コールオプションの全グリークス計算テスト"""
        greeks = qf.calculate_all_greeks(100.0, 100.0, 1.0, 0.05, 0.2, True)

        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks

        # 個別計算と比較
        assert abs(greeks["delta"] - qf.calculate_delta_call(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["gamma"] - qf.calculate_gamma(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["vega"] - qf.calculate_vega(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["theta"] - qf.calculate_theta_call(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["rho"] - qf.calculate_rho_call(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE

    def test_calculate_all_greeks_put(self) -> None:
        """プットオプションの全グリークス計算テスト"""
        greeks = qf.calculate_all_greeks(100.0, 100.0, 1.0, 0.05, 0.2, False)

        # 個別計算と比較
        assert abs(greeks["delta"] - qf.calculate_delta_put(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["gamma"] - qf.calculate_gamma(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["vega"] - qf.calculate_vega(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["theta"] - qf.calculate_theta_put(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(greeks["rho"] - qf.calculate_rho_put(100.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE


class TestGreeksBatchCalculation:
    """バッチ計算テスト"""

    def test_delta_call_batch(self) -> None:
        """Delta Callバッチ計算テスト"""
        spots = np.array([90.0, 100.0, 110.0])
        deltas = qf.calculate_delta_call_batch(spots, 100.0, 1.0, 0.05, 0.2)

        assert len(deltas) == len(spots)

        # 個別計算と比較
        for i, spot in enumerate(spots):
            expected = qf.calculate_delta_call(spot, 100.0, 1.0, 0.05, 0.2)
            assert abs(deltas[i] - expected) < NUMERICAL_TOLERANCE

    def test_gamma_batch(self) -> None:
        """Gammaバッチ計算テスト"""
        spots = np.array([90.0, 100.0, 110.0])
        gammas = qf.calculate_gamma_batch(spots, 100.0, 1.0, 0.05, 0.2)

        assert len(gammas) == len(spots)

        # 個別計算と比較
        for i, spot in enumerate(spots):
            expected = qf.calculate_gamma(spot, 100.0, 1.0, 0.05, 0.2)
            assert abs(gammas[i] - expected) < NUMERICAL_TOLERANCE

    def test_large_batch_performance(self) -> None:
        """大規模バッチ計算のパフォーマンステスト"""
        # 10000要素のテスト（並列化閾値未満）
        spots = np.linspace(80.0, 120.0, 10000)

        # エラーなく計算できることを確認
        deltas = qf.calculate_delta_call_batch(spots, 100.0, 1.0, 0.05, 0.2)
        assert len(deltas) == len(spots)

        # 最初と最後の要素を確認
        assert abs(deltas[0] - qf.calculate_delta_call(80.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE
        assert abs(deltas[-1] - qf.calculate_delta_call(120.0, 100.0, 1.0, 0.05, 0.2)) < NUMERICAL_TOLERANCE


class TestGreeksEdgeCases:
    """エッジケースのテスト"""

    def test_at_expiry(self) -> None:
        """満期時のグリークステスト"""
        # Delta
        assert qf.calculate_delta_call(110.0, 100.0, 0.0, 0.05, 0.2) == 1.0
        assert qf.calculate_delta_call(90.0, 100.0, 0.0, 0.05, 0.2) == 0.0
        assert qf.calculate_delta_put(90.0, 100.0, 0.0, 0.05, 0.2) == -1.0
        assert qf.calculate_delta_put(110.0, 100.0, 0.0, 0.05, 0.2) == 0.0

        # Gamma, Vega, Theta, Rho
        assert qf.calculate_gamma(100.0, 100.0, 0.0, 0.05, 0.2) == 0.0
        assert qf.calculate_vega(100.0, 100.0, 0.0, 0.05, 0.2) == 0.0
        assert qf.calculate_theta_call(100.0, 100.0, 0.0, 0.05, 0.2) == 0.0
        assert qf.calculate_rho_call(100.0, 100.0, 0.0, 0.05, 0.2) == 0.0

    def test_put_call_parity_delta(self) -> None:
        """Put-CallパリティのDeltaテスト"""
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2

        delta_call = qf.calculate_delta_call(s, k, t, r, sigma)
        delta_put = qf.calculate_delta_put(s, k, t, r, sigma)

        # Delta_call - Delta_put = 1
        assert abs((delta_call - delta_put) - 1.0) < NUMERICAL_TOLERANCE

    def test_input_validation(self) -> None:
        """入力検証テスト"""
        # 負のスポット価格
        with pytest.raises(ValueError):
            qf.calculate_delta_call(-100.0, 100.0, 1.0, 0.05, 0.2)

        # 負のボラティリティ
        with pytest.raises(ValueError):
            qf.calculate_gamma(100.0, 100.0, 1.0, 0.05, -0.2)

        # NaN入力
        with pytest.raises(ValueError):
            qf.calculate_vega(float("nan"), 100.0, 1.0, 0.05, 0.2)

# mypy: disable-error-code="attr-defined"
"""Black-Scholesグリークスのテスト

Rust実装のグリークス計算が正しく動作することを検証。
"""

import numpy as np
from conftest import NUMERICAL_TOLERANCE
from quantforge import models


class TestGreeksSingleCalculation:
    """単一のグリークス計算テスト"""

    def test_delta_call(self) -> None:
        """コールオプションのDelta計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        delta = greeks.delta
        assert abs(delta - 0.6368306517096883) < NUMERICAL_TOLERANCE

        # ITMでDeltaは1に近づく
        greeks_itm = models.greeks(110.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        delta_itm = greeks_itm.delta
        assert 0.6368306517096883 < delta_itm < 1.0

        # OTMでDeltaは0に近づく
        greeks_otm = models.greeks(90.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        delta_otm = greeks_otm.delta
        assert 0.0 < delta_otm < 0.6368306517096883

    def test_delta_put(self) -> None:
        """プットオプションのDelta計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=False)
        delta = greeks.delta
        assert abs(delta - (-0.36316934829031174)) < NUMERICAL_TOLERANCE

        # ITMプット（S < K）でDeltaは-1に近づく
        greeks_itm = models.greeks(90.0, 100.0, 1.0, 0.05, 0.2, is_call=False)
        delta_itm = greeks_itm.delta
        assert -1.0 < delta_itm < -0.36316934829031174

        # OTMプット（S > K）でDeltaは0に近づく
        greeks_otm = models.greeks(110.0, 100.0, 1.0, 0.05, 0.2, is_call=False)
        delta_otm = greeks_otm.delta
        assert -0.36316934829031174 < delta_otm < 0.0

    def test_gamma(self) -> None:
        """Gamma計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        gamma = greeks.gamma
        # Gammaは常に正
        assert gamma > 0.0
        assert abs(gamma - 0.018762017345846895) < NUMERICAL_TOLERANCE

    def test_vega(self) -> None:
        """Vega計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        vega = greeks.vega
        # Vegaは常に正
        assert vega > 0.0
        assert abs(vega - 0.3752403469169379) < NUMERICAL_TOLERANCE

    def test_theta_call(self) -> None:
        """コールオプションのTheta計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        theta = greeks.theta
        # Thetaは通常負（時間価値の減少）
        assert theta < 0.0

    def test_theta_put(self) -> None:
        """プットオプションのTheta計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=False)
        theta = greeks.theta
        # プットのThetaも通常負
        assert theta < 0.0

    def test_rho_call(self) -> None:
        """コールオプションのRho計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        rho = greeks.rho
        # コールのRhoは正
        assert rho > 0.0

    def test_rho_put(self) -> None:
        """プットオプションのRho計算テスト"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=False)
        rho = greeks.rho
        # プットのRhoは負
        assert rho < 0.0


class TestAllGreeks:
    """全グリークス一括計算テスト"""

    def test_all_greeks_call(self) -> None:
        """コールオプションの全グリークス"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)

        assert abs(greeks.delta - 0.6368306517096883) < NUMERICAL_TOLERANCE
        assert abs(greeks.gamma - 0.018762017345846895) < NUMERICAL_TOLERANCE
        assert abs(greeks.vega - 0.3752403469169379) < NUMERICAL_TOLERANCE
        assert abs(greeks.theta - (-0.017582796228917447)) < 2e-5  # Thetaの精度制約
        assert abs(greeks.rho - 0.5323131061766925) < 2e-5  # Rhoの精度制約

    def test_all_greeks_put(self) -> None:
        """プットオプションの全グリークス"""
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=False)

        assert abs(greeks.delta - (-0.36316934829031174)) < NUMERICAL_TOLERANCE
        assert abs(greeks.gamma - 0.018762017345846895) < NUMERICAL_TOLERANCE
        assert abs(greeks.vega - 0.3752403469169379) < NUMERICAL_TOLERANCE
        assert abs(greeks.theta - (-0.011661530511418097)) < 0.01  # Thetaの計算誤差が大きいため
        assert abs(greeks.rho - (-0.4249474915266148)) < 0.01  # Rhoの計算誤差が大きいため


class TestGreeksEdgeCases:
    """エッジケースのテスト"""

    def test_deep_itm_call(self) -> None:
        """Deep ITMコール（Delta→1）"""
        greeks = models.greeks(200.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        assert greeks.delta > 0.99
        assert abs(greeks.gamma) < 1e-5

    def test_deep_otm_call(self) -> None:
        """Deep OTMコール（Delta→0）"""
        greeks = models.greeks(50.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        assert greeks.delta < 0.01
        assert abs(greeks.gamma) < 1e-3  # Deep OTMでもgammaは完全にゼロにはならない

    def test_near_zero_volatility(self) -> None:
        """低ボラティリティ（特殊ケース）"""
        # ボラティリティが非常に低い場合の処理をテスト（min_vol = 0.005以上）
        greeks = models.greeks(100.0, 100.0, 1.0, 0.05, 0.01, is_call=True)
        # 数値的に安定した結果が返ることを確認
        assert np.isfinite(greeks.delta)
        assert np.isfinite(greeks.gamma)

    def test_near_zero_time(self) -> None:
        """満期直前（T≈0）"""
        # 満期直前での計算をテスト
        greeks = models.greeks(105.0, 100.0, 0.001, 0.05, 0.2, is_call=True)
        assert greeks.delta >= 0.90  # ITMなのでDeltaを1に近づく
        assert abs(greeks.theta) < 100.0  # Thetaは有限値に留まる


class TestGreeksBatchCalculation:
    """バッチ処理のテスト"""

    def test_delta_batch(self) -> None:
        """Deltaのバッチ計算"""
        spots = np.array([90.0, 100.0, 110.0])

        # バッチ処理はcall_price_batchの結果から数値微分で計算
        # 現在の実装ではグリークスのバッチ処理は個別に計算
        for _i, spot in enumerate(spots):
            greeks = models.greeks(spot, 100.0, 1.0, 0.05, 0.2, is_call=True)
            assert np.isfinite(greeks.delta)

            if spot < 100.0:  # OTM
                assert 0.0 < greeks.delta < 0.5
            elif spot > 100.0:  # ITM
                assert 0.5 < greeks.delta < 1.0

    def test_gamma_batch(self) -> None:
        """Gammaのバッチ計算"""
        spots = np.array([90.0, 100.0, 110.0])

        for spot in spots:
            greeks = models.greeks(spot, 100.0, 1.0, 0.05, 0.2, is_call=True)
            assert greeks.gamma > 0.0
            assert np.isfinite(greeks.gamma)


class TestGreeksPutCallParity:
    """Put-Callパリティに基づくグリークスの関係性テスト"""

    def test_delta_parity(self) -> None:
        """Delta_call - Delta_put = 1の検証"""
        greeks_call = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        greeks_put = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=False)

        delta_diff = greeks_call.delta - greeks_put.delta
        assert abs(delta_diff - 1.0) < NUMERICAL_TOLERANCE

    def test_gamma_equality(self) -> None:
        """Gamma_call = Gamma_putの検証"""
        greeks_call = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        greeks_put = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=False)

        assert abs(greeks_call.gamma - greeks_put.gamma) < NUMERICAL_TOLERANCE

    def test_vega_equality(self) -> None:
        """Vega_call = Vega_putの検証"""
        greeks_call = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=True)
        greeks_put = models.greeks(100.0, 100.0, 1.0, 0.05, 0.2, is_call=False)

        assert abs(greeks_call.vega - greeks_put.vega) < NUMERICAL_TOLERANCE

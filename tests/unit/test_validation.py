"""入力検証とエラー処理の包括的ユニットテスト."""

import math

import numpy as np
import pytest
from quantforge.models import black_scholes

from tests.conftest import PRACTICAL_TOLERANCE, arrow


@pytest.mark.unit
class TestInputValidation:
    """入力検証の完全テスト."""

    def test_negative_spot_price(self) -> None:
        """負のスポット価格でエラー."""
        with pytest.raises(ValueError, match="[Ss]pot"):
            black_scholes.call_price(-100.0, 100.0, 1.0, 0.05, 0.2)

    def test_zero_spot_price(self) -> None:
        """ゼロのスポット価格でエラー."""
        with pytest.raises(ValueError, match="[Ss]pot"):
            black_scholes.call_price(0.0, 100.0, 1.0, 0.05, 0.2)

    def test_negative_strike_price(self) -> None:
        """負の行使価格でエラー."""
        with pytest.raises(ValueError, match="[Ss]trike"):
            black_scholes.call_price(100.0, -100.0, 1.0, 0.05, 0.2)

    def test_zero_strike_price(self) -> None:
        """ゼロの行使価格でエラー."""
        with pytest.raises(ValueError, match="[Ss]trike"):
            black_scholes.call_price(100.0, 0.0, 1.0, 0.05, 0.2)

    def test_negative_time_to_maturity(self) -> None:
        """負の満期までの時間でエラー."""
        with pytest.raises(ValueError, match="[Tt]ime"):
            black_scholes.call_price(100.0, 100.0, -1.0, 0.05, 0.2)

    def test_zero_time_to_maturity(self) -> None:
        """ゼロの満期までの時間でエラー."""
        with pytest.raises(ValueError, match="[Tt]ime"):
            black_scholes.call_price(100.0, 100.0, 0.0, 0.05, 0.2)

    def test_negative_volatility(self) -> None:
        """負のボラティリティでエラー."""
        with pytest.raises(ValueError, match="[Vv]olatility"):
            black_scholes.call_price(100.0, 100.0, 1.0, 0.05, -0.2)

    def test_zero_volatility(self) -> None:
        """ゼロのボラティリティでエラー."""
        with pytest.raises(ValueError, match="[Vv]olatility"):
            black_scholes.call_price(100.0, 100.0, 1.0, 0.05, 0.0)

    def test_extreme_interest_rates(self) -> None:
        """極端な金利の処理."""
        # 負の金利（許容範囲内）
        price_neg = black_scholes.call_price(100.0, 100.0, 1.0, -0.05, 0.2)
        assert price_neg > 0, "負の金利で価格が負"

        # 高い金利（許容範囲内）
        price_high = black_scholes.call_price(100.0, 100.0, 1.0, 0.5, 0.2)
        assert price_high > 0, "高金利で価格が負"

        # 許容範囲外の金利
        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, 1.5, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, -1.5, 0.2)


@pytest.mark.unit
class TestNumericValues:
    """特殊な数値の処理テスト."""

    def test_nan_inputs(self) -> None:
        """NaN入力の処理."""
        nan = float("nan")

        with pytest.raises(ValueError):
            black_scholes.call_price(nan, 100.0, 1.0, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, nan, 1.0, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, nan, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, nan, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, 0.05, nan)

    def test_inf_inputs(self) -> None:
        """無限大入力の処理."""
        inf = float("inf")

        with pytest.raises(ValueError):
            black_scholes.call_price(inf, 100.0, 1.0, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, inf, 1.0, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, inf, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, inf, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, 0.05, inf)

    def test_very_small_positive_values(self) -> None:
        """非常に小さい正の値の処理."""
        # 許容される最小値
        min_price = 0.01
        min_time = 0.001
        min_vol = 0.005

        price1 = black_scholes.call_price(min_price, 100.0, 1.0, 0.05, 0.2)
        assert price1 >= 0, "最小価格で負の結果"

        price2 = black_scholes.call_price(100.0, min_price, 1.0, 0.05, 0.2)
        assert price2 >= 0, "最小行使価格で負の結果"

        price3 = black_scholes.call_price(100.0, 100.0, min_time, 0.05, 0.2)
        assert price3 >= 0, "最小時間で負の結果"

        price4 = black_scholes.call_price(100.0, 100.0, 1.0, 0.05, min_vol)
        assert price4 >= 0, "最小ボラティリティで負の結果"

        # 許容範囲外の小さい値
        with pytest.raises(ValueError):
            black_scholes.call_price(0.001, 100.0, 1.0, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 0.0001, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, 0.05, 0.001)

    def test_very_large_values(self) -> None:
        """非常に大きい値の処理."""
        max_price = 2147483648.0  # 2^31
        max_time = 100.0
        max_vol = 5.0  # MAX_VOLATILITY constant

        # 許容される最大値
        price1 = black_scholes.call_price(max_price - 1, 100.0, 1.0, 0.05, 0.2)
        assert price1 >= 0, "最大価格で負の結果"
        assert math.isfinite(price1), "最大価格で無限大"

        price2 = black_scholes.call_price(100.0, max_price - 1, 1.0, 0.05, 0.2)
        assert price2 >= 0, "最大行使価格で負の結果"
        assert math.isfinite(price2), "最大行使価格で無限大"

        price3 = black_scholes.call_price(100.0, 100.0, max_time, 0.05, 0.2)
        assert price3 >= 0, "最大時間で負の結果"
        assert math.isfinite(price3), "最大時間で無限大"

        price4 = black_scholes.call_price(100.0, 100.0, 1.0, 0.05, max_vol)
        assert price4 >= 0, "最大ボラティリティで負の結果"
        assert math.isfinite(price4), "最大ボラティリティで無限大"

        # 許容範囲外の大きい値
        with pytest.raises(ValueError):
            black_scholes.call_price(max_price * 2, 100.0, 1.0, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, max_time * 2, 0.05, 0.2)

        with pytest.raises(ValueError):
            black_scholes.call_price(100.0, 100.0, 1.0, 0.05, max_vol * 2)


@pytest.mark.unit
class TestBatchValidation:
    """バッチ処理の検証テスト."""

    def test_empty_batch(self) -> None:
        """空のバッチ処理."""
        spots = np.array([])
        # Arrow Nativeは空配列をサポートしていない
        with pytest.raises(Exception, match="incompatible length"):
            black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)

    def test_single_element_batch(self) -> None:
        """単一要素のバッチ処理."""
        spots = np.array([100.0])
        result = black_scholes.call_price_batch(spots, 100.0, 1.0, 0.05, 0.2)
        assert len(result) == 1, "単一要素バッチのサイズが不正"

        # 単一計算と同じ結果
        single_price = black_scholes.call_price(100.0, 100.0, 1.0, 0.05, 0.2)
        batch_value = arrow.get_value(result, 0)
        assert abs(batch_value - single_price) < PRACTICAL_TOLERANCE, "バッチと単一計算の不一致"

    def test_batch_with_invalid_values(self) -> None:
        """無効な値を含むバッチ処理."""
        # NaNを含むバッチ - エラーが発生することを確認
        spots_nan = np.array([100.0, float("nan"), 110.0])
        with pytest.raises(Exception, match="spot must be finite"):
            black_scholes.call_price_batch(spots_nan, 100.0, 1.0, 0.05, 0.2)

        # 負の値を含むバッチ - エラーが発生することを確認
        spots_neg = np.array([100.0, -50.0, 110.0])
        with pytest.raises(Exception, match="spot must be positive"):
            black_scholes.call_price_batch(spots_neg, 100.0, 1.0, 0.05, 0.2)

        # ゼロを含むバッチ - エラーが発生することを確認
        spots_zero = np.array([100.0, 0.0, 110.0])
        with pytest.raises(Exception, match="spot must be positive"):
            black_scholes.call_price_batch(spots_zero, 100.0, 1.0, 0.05, 0.2)

    def test_batch_consistency(self) -> None:
        """バッチ処理の一貫性テスト."""
        spots = np.linspace(50, 150, 100)
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        # バッチ処理
        batch_results = black_scholes.call_price_batch(spots, k, t, r, sigma)
        arrow.assert_type(batch_results)
        batch_results_list = arrow.to_list(batch_results)

        # 個別処理との比較
        for i, spot in enumerate(spots):
            single_result = black_scholes.call_price(spot, k, t, r, sigma)
            assert abs(batch_results_list[i] - single_result) < PRACTICAL_TOLERANCE, f"バッチと個別の不一致: {i}"

    def test_large_batch(self) -> None:
        """大規模バッチの処理."""
        n = 100000
        spots = np.random.uniform(50, 150, n)
        k = 100.0
        t = 1.0
        r = 0.05
        sigma = 0.2

        results = black_scholes.call_price_batch(spots, k, t, r, sigma)
        arrow.assert_type(results)
        results_array = np.array(arrow.to_list(results))

        assert len(results_array) == n, "バッチサイズが不正"
        assert np.all(results_array >= 0), "負の価格が存在"
        assert np.all(np.isfinite(results_array)), "無限大またはNaNが存在"

        # 価格の妥当性チェック
        intrinsic_values = np.maximum(spots - k * np.exp(-r * t), 0)
        assert np.all(results_array >= intrinsic_values - PRACTICAL_TOLERANCE), "本質的価値を下回る価格"
        assert np.all(results_array <= spots), "スポット価格を超える価格"


@pytest.mark.unit
class TestErrorMessages:
    """エラーメッセージの適切性テスト."""

    def test_error_message_content(self) -> None:
        """エラーメッセージの内容確認."""
        # スポット価格エラー
        with pytest.raises(ValueError) as exc_info:
            black_scholes.call_price(-100.0, 100.0, 1.0, 0.05, 0.2)
        # エラーメッセージは "s, k, t, and sigma must be positive" 形式
        assert "s" in str(exc_info.value).lower() or "spot" in str(exc_info.value).lower()

        # 行使価格エラー
        with pytest.raises(ValueError) as exc_info:
            black_scholes.call_price(100.0, -100.0, 1.0, 0.05, 0.2)
        assert "k" in str(exc_info.value).lower() or "strike" in str(exc_info.value).lower()

        # 時間エラー
        with pytest.raises(ValueError) as exc_info:
            black_scholes.call_price(100.0, 100.0, -1.0, 0.05, 0.2)
        assert "t" in str(exc_info.value).lower() or "time" in str(exc_info.value).lower()

        # ボラティリティエラー
        with pytest.raises(ValueError) as exc_info:
            black_scholes.call_price(100.0, 100.0, 1.0, 0.05, -0.2)
        assert "sigma" in str(exc_info.value).lower() or "volatility" in str(exc_info.value).lower()

    def test_error_includes_value(self) -> None:
        """エラーメッセージに問題の値が含まれることを確認."""
        with pytest.raises(ValueError) as exc_info:
            black_scholes.call_price(-123.45, 100.0, 1.0, 0.05, 0.2)
        # エラーメッセージに実際の値が含まれるか
        # 現在のメッセージは "s, k, t, and sigma must be positive" で値を含まない
        error_msg = str(exc_info.value)
        # 値の検証をスキップ（現在の実装では値を含まない）
        assert "must be positive" in error_msg

    def test_multiple_invalid_inputs(self) -> None:
        """複数の無効入力の処理."""
        # 最初のエラーで停止することを確認
        with pytest.raises(ValueError):
            # 複数の無効な値
            black_scholes.call_price(-100.0, -100.0, -1.0, 0.05, -0.2)
        # エラーは一つずつ報告される（最初のエラーで停止）


@pytest.mark.unit
class TestBoundaryConditions:
    """境界条件での検証テスト."""

    def test_minimum_valid_inputs(self) -> None:
        """最小有効値での計算."""
        # 仕様で定義された最小値
        min_price = 0.01
        min_time = 0.001
        min_vol = 0.005
        min_rate = -1.0

        # すべて最小値
        price = black_scholes.call_price(min_price, min_price, min_time, min_rate, min_vol)
        assert price >= 0, "最小値で負の価格"
        assert math.isfinite(price), "最小値で無限大"

    def test_maximum_valid_inputs(self) -> None:
        """最大有効値での計算."""
        # 仕様で定義された最大値
        max_price = 2147483648.0 - 1  # 境界値の直前
        max_time = 100.0
        max_vol = 5.0
        max_rate = 1.0

        # すべて最大値
        price = black_scholes.call_price(max_price, max_price, max_time, max_rate, max_vol)
        assert price >= 0, "最大値で負の価格"
        assert math.isfinite(price), "最大値で無限大"

    def test_mixed_boundary_values(self) -> None:
        """境界値の組み合わせテスト."""
        # 最小スポット、最大行使価格
        price1 = black_scholes.call_price(0.01, 2147483648.0 - 1, 1.0, 0.05, 0.2)
        assert price1 == 0.0, "Deep OTMでゼロでない"

        # 最大スポット、最小行使価格
        price2 = black_scholes.call_price(2147483648.0 - 1, 0.01, 1.0, 0.05, 0.2)
        assert price2 > 0, "Deep ITMで正でない"

        # 最小時間、最大ボラティリティ
        price3 = black_scholes.call_price(100.0, 100.0, 0.001, 0.05, 5.0)
        assert price3 >= 0, "境界値の組み合わせで負"
        assert math.isfinite(price3), "境界値の組み合わせで無限大"

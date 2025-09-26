"""Unit tests for market pricing utilities"""

import math

import numpy as np
import pytest
from quantforge.market_utils import (
    PricingConfig,
    mid_price,
    mid_price_batch,
    mid_price_batch_with_config,
    mid_price_batch_with_metrics,
    mid_price_with_config,
    spread,
    spread_batch,
    spread_pct,
    spread_pct_batch,
    weighted_mid_price,
    weighted_mid_price_batch,
)


class TestMidPrice:
    """Tests for mid price calculation"""

    def test_simple_mid_price(self):
        """Test simple mid price calculation"""
        assert mid_price(100.0, 100.2) == pytest.approx(100.1)

    def test_mid_price_with_zero(self):
        """Test mid price with zero bid (valid in options market)"""
        # Default config has 50% threshold, so 200% spread returns NaN
        assert math.isnan(mid_price(0.0, 100.0))

        # With no threshold, zero is valid
        config = PricingConfig.with_config(max_spread_pct=None)
        result = mid_price_with_config(0.0, 100.0, config)
        assert result == pytest.approx(50.0)

    def test_mid_price_with_negative(self):
        """Test mid price with negative values (should return NaN)"""
        assert math.isnan(mid_price(-100.0, 100.0))
        assert math.isnan(mid_price(100.0, -100.0))

    def test_mid_price_with_nan(self):
        """Test mid price with NaN inputs"""
        assert math.isnan(mid_price(float("nan"), 100.0))
        assert math.isnan(mid_price(100.0, float("nan")))

    def test_mid_price_with_inf(self):
        """Test mid price with infinite values"""
        assert math.isnan(mid_price(float("inf"), 100.0))
        assert math.isnan(mid_price(100.0, float("inf")))

    def test_crossed_spread(self):
        """Test mid price with crossed spread (bid > ask)"""
        # Default config should return NaN
        assert math.isnan(mid_price(105.0, 100.0))


class TestMidPriceWithConfig:
    """Tests for mid price with custom configuration"""

    def test_extreme_option_spread(self):
        """Test extreme spreads common in options markets"""
        # Deep OTM option: bid=1, ask=1000
        # Default config (50% threshold)
        config = PricingConfig()
        assert math.isnan(mid_price_with_config(1.0, 1000.0, config))

        # No threshold
        config_no_limit = PricingConfig.with_config(max_spread_pct=None)
        assert mid_price_with_config(1.0, 1000.0, config_no_limit) == pytest.approx(500.5)

    def test_abnormal_spread_handling(self):
        """Test different abnormal spread handling strategies"""
        config_nan = PricingConfig.with_config(
            max_spread_pct=0.1,  # 10% threshold
            abnormal_handling="return_nan",
        )
        assert math.isnan(mid_price_with_config(100.0, 120.0, config_nan))

        config_continue = PricingConfig.with_config(max_spread_pct=0.1, abnormal_handling="log_and_continue")
        assert mid_price_with_config(100.0, 120.0, config_continue) == pytest.approx(110.0)

    def test_crossed_spread_handling(self):
        """Test different crossed spread handling strategies"""
        config_nan = PricingConfig.with_config(crossed_handling="return_nan")
        assert math.isnan(mid_price_with_config(105.0, 100.0, config_nan))

        config_swap = PricingConfig.with_config(crossed_handling="swap_and_continue")
        assert mid_price_with_config(105.0, 100.0, config_swap) == pytest.approx(102.5)


class TestWeightedMidPrice:
    """Tests for quantity-weighted mid price"""

    def test_weighted_mid_price_equal_quantities(self):
        """Test weighted mid with equal quantities (should equal simple mid)"""
        result = weighted_mid_price(100.0, 100.2, 1000.0, 1000.0)
        assert result == pytest.approx(100.1)

    def test_weighted_mid_price_different_quantities(self):
        """Test weighted mid with different quantities"""
        # Heavy bid side
        result = weighted_mid_price(100.0, 100.2, 2000.0, 1000.0)
        expected = (100.0 * 1000.0 + 100.2 * 2000.0) / 3000.0
        assert result == pytest.approx(expected)

    def test_weighted_mid_price_zero_quantity(self):
        """Test weighted mid with zero quantity (should use simple mid)"""
        result = weighted_mid_price(100.0, 100.2, 0.0, 1000.0)
        assert result == pytest.approx(100.1)

        result = weighted_mid_price(100.0, 100.2, 1000.0, 0.0)
        assert result == pytest.approx(100.1)

    def test_weighted_mid_price_missing_quantities(self):
        """Test weighted mid with None quantities"""
        result = weighted_mid_price(100.0, 100.2)
        assert result == pytest.approx(100.1)

        result = weighted_mid_price(100.0, 100.2, bid_qty=1000.0)
        assert result == pytest.approx(100.1)


class TestSpread:
    """Tests for spread calculations"""

    def test_spread_absolute(self):
        """Test absolute spread calculation"""
        assert spread(100.0, 100.2) == pytest.approx(0.2)
        assert spread(99.8, 100.2) == pytest.approx(0.4)

    def test_spread_percentage(self):
        """Test percentage spread calculation"""
        assert spread_pct(100.0, 100.2) == pytest.approx(0.001998, rel=1e-4)  # 0.2%
        assert spread_pct(99.0, 101.0) == pytest.approx(0.02)  # 2%

    def test_spread_with_crossed(self):
        """Test spread with crossed market"""
        assert spread(105.0, 100.0) == pytest.approx(-5.0)
        assert math.isnan(spread_pct(105.0, 100.0))  # Percentage undefined


class TestBatchProcessing:
    """Tests for batch processing functionality"""

    def test_batch_simple_mid_price(self):
        """Test batch mid price calculation"""
        bids = np.array([100.0, 101.0, 102.0])
        asks = np.array([100.2, 101.3, 102.4])
        result = mid_price_batch(bids, asks)
        expected = np.array([100.1, 101.15, 102.2])
        np.testing.assert_array_almost_equal(result, expected)

    def test_batch_with_nan_values(self):
        """Test batch processing with NaN values"""
        bids = np.array([100.0, float("nan"), 102.0])
        asks = np.array([100.2, 101.3, 102.4])
        result = mid_price_batch(bids, asks)
        assert not math.isnan(result[0])
        assert math.isnan(result[1])
        assert not math.isnan(result[2])

    def test_batch_with_extreme_spreads(self):
        """Test batch with options-like extreme spreads"""
        bids = np.array([1.0, 10.0, 100.0, 1000.0])
        asks = np.array([1000.0, 11.0, 102.0, 1001.0])
        result = mid_price_batch(bids, asks)  # Default 50% threshold
        assert math.isnan(result[0])  # 99900% spread
        assert not math.isnan(result[1])  # 9.5% spread
        assert not math.isnan(result[2])  # 2% spread
        assert not math.isnan(result[3])  # 0.1% spread

    def test_batch_broadcasting(self):
        """Test broadcasting with scalar values"""
        # Scalar bid, array ask
        bid = 100.0
        asks = np.array([100.2, 100.3, 100.4])
        result = mid_price_batch(np.array([bid]), asks)
        expected = np.array([100.1, 100.15, 100.2])
        np.testing.assert_array_almost_equal(result, expected)

    def test_batch_incompatible_sizes(self):
        """Test error on incompatible array sizes"""
        bids = np.array([100.0, 101.0])
        asks = np.array([100.2, 100.3, 100.4])
        with pytest.raises(ValueError, match="incompatible length"):
            mid_price_batch(bids, asks)

    def test_batch_large_scale(self):
        """Test large-scale batch processing (parallel threshold)"""
        n = 15000  # Above parallel threshold
        np.random.seed(42)
        bids = np.random.uniform(99, 101, n)
        asks = bids + np.random.uniform(0.1, 0.3, n)
        result = mid_price_batch(bids, asks)
        assert len(result) == n
        assert np.all(result > bids)
        assert np.all(result < asks)


class TestBatchMetrics:
    """Tests for batch processing with metrics collection"""

    def test_metrics_collection(self):
        """Test metrics collection during batch processing"""
        bids = np.array([100.0, 1.0, 105.0, 100.0])
        asks = np.array([100.2, 1000.0, 104.0, 100.5])
        config = PricingConfig()

        result, metrics = mid_price_batch_with_metrics(bids, asks, config)

        assert metrics.total_processed == 4
        assert metrics.nan_count == 2  # bid=1, ask=1000 is abnormal + crossed spread
        assert metrics.crossed_spreads == 1  # bid=105, ask=104
        assert metrics.abnormal_spreads > 0
        assert metrics.mean_spread_pct > 0
        assert metrics.max_spread_pct > 0

    def test_metrics_with_all_valid(self):
        """Test metrics when all spreads are valid"""
        bids = np.array([100.0, 101.0, 102.0])
        asks = np.array([100.2, 101.3, 102.4])
        config = PricingConfig()

        result, metrics = mid_price_batch_with_metrics(bids, asks, config)

        assert metrics.total_processed == 3
        assert metrics.nan_count == 0
        assert metrics.crossed_spreads == 0
        assert metrics.abnormal_spreads == 0


class TestWeightedBatch:
    """Tests for batch weighted mid price"""

    def test_weighted_batch_processing(self):
        """Test batch weighted mid price calculation"""
        bids = np.array([100.0, 101.0])
        bid_qtys = np.array([1000.0, 2000.0])
        asks = np.array([100.2, 101.3])
        ask_qtys = np.array([1500.0, 1000.0])

        result = weighted_mid_price_batch(bids, asks, bid_qtys, ask_qtys)
        assert len(result) == 2

        # Verify first element
        expected_0 = (100.0 * 1500.0 + 100.2 * 1000.0) / 2500.0
        assert result[0] == pytest.approx(expected_0)

    def test_weighted_batch_with_zero_quantities(self):
        """Test weighted batch with some zero quantities"""
        bids = np.array([100.0, 101.0, 102.0])
        bid_qtys = np.array([1000.0, 0.0, 2000.0])
        asks = np.array([100.2, 101.3, 102.4])
        ask_qtys = np.array([1500.0, 1000.0, 0.0])

        result = weighted_mid_price_batch(bids, asks, bid_qtys, ask_qtys)
        # Simple mid should be used for zero quantities
        assert result[1] == pytest.approx(101.15)  # Simple mid
        assert result[2] == pytest.approx(102.2)  # Simple mid


class TestSpreadBatch:
    """Tests for batch spread calculations"""

    def test_spread_batch(self):
        """Test batch spread calculation"""
        bids = np.array([100.0, 99.8])
        asks = np.array([100.2, 100.2])
        result = spread_batch(bids, asks)
        np.testing.assert_array_almost_equal(result, [0.2, 0.4])

    def test_spread_pct_batch(self):
        """Test batch spread percentage calculation"""
        bids = np.array([100.0, 99.0])
        asks = np.array([100.2, 101.0])
        result = spread_pct_batch(bids, asks)
        # First: (100.2 - 100.0) / 100.1 ≈ 0.001998
        # Second: (101.0 - 99.0) / 100.0 = 0.02
        assert result[0] == pytest.approx(0.001998, rel=1e-4)
        assert result[1] == pytest.approx(0.02)


class TestRealWorldScenarios:
    """Tests for real-world market scenarios"""

    def test_nikkei_option_chain_processing(self):
        """Test processing a simulated Nikkei 225 option chain"""
        n = 100
        strikes = np.linspace(40000, 50000, n)
        atm = 45000

        # Distance from ATM determines spread width
        distance = np.abs(strikes - atm) / atm
        spread_pct = 0.002 + distance * 2.0  # 0.2% to 200%+ for far strikes

        bids = strikes * (1 - spread_pct / 2)
        asks = strikes * (1 + spread_pct / 2)

        config = PricingConfig.with_config(max_spread_pct=0.1)  # 10% threshold

        mids, metrics = mid_price_batch_with_metrics(bids, asks, config)

        # Valid options should be near ATM
        valid_mids = mids[~np.isnan(mids)]
        assert len(valid_mids) < n  # Some should be filtered
        assert len(valid_mids) > n // 3  # But not too many

    def test_sparse_order_book(self):
        """Test handling of sparse order book with missing levels"""
        # Some strikes have no bid (zero in options market)
        bids = np.array([0.0, 10.0, 100.0, 0.0])
        asks = np.array([5.0, 11.0, 102.0, 1000.0])

        # With no spread limit, zero bids are valid
        config = PricingConfig.with_config(max_spread_pct=None)
        result = mid_price_batch_with_config(bids, asks, config)
        assert result[0] == pytest.approx(2.5)  # Zero bid is valid
        assert result[3] == pytest.approx(500.0)  # Zero bid is valid

    def test_high_frequency_data_stream(self):
        """Test processing high-frequency market data"""
        # Simulate 1 second of tick data (100 updates)
        np.random.seed(42)
        base_price = 100.0
        n = 100

        # Random walk for bid/ask
        noise = np.random.randn(n) * 0.01
        bids = base_price + np.cumsum(noise) - 0.1
        asks = bids + np.random.uniform(0.05, 0.15, n)

        mids = mid_price_batch(bids, asks)

        # All should be valid in normal market
        assert np.all(~np.isnan(mids))
        assert np.all(mids > bids)
        assert np.all(mids < asks)

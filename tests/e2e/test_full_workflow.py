"""End-to-end tests for complete workflows."""

import numpy as np
import pytest

# Import the main module
import quantforge


class TestE2EWorkflows:
    """Test complete user workflows."""

    def test_option_pricing_workflow(self):
        """Test complete option pricing workflow."""
        # 1. Single pricing
        spot = 100.0
        strike = 105.0
        time = 0.25
        rate = 0.05
        vol = 0.2

        # Black-Scholes
        call_price = quantforge.black_scholes.call_price(spot, strike, time, rate, vol)
        put_price = quantforge.black_scholes.put_price(spot, strike, time, rate, vol)

        assert isinstance(call_price, float)
        assert isinstance(put_price, float)
        assert call_price > 0
        assert put_price > 0

        # 2. Greeks calculation
        greeks = quantforge.black_scholes.greeks(spot, strike, time, rate, vol)

        assert isinstance(greeks, dict)
        assert "delta" in greeks
        assert "gamma" in greeks
        assert "vega" in greeks
        assert "theta" in greeks
        assert "rho" in greeks

        # 3. Implied volatility
        iv = quantforge.black_scholes.implied_volatility(call_price, spot, strike, time, rate, is_call=True)

        assert abs(iv - vol) < 1e-6

        # 4. Batch processing
        spots = np.linspace(90, 110, 21)
        prices = quantforge.black_scholes.call_price_batch(spots, strike, time, rate, vol)

        assert len(prices) == 21
        assert all(p >= 0 for p in prices)

    def test_cross_model_workflow(self):
        """Test workflow across different models."""
        params = {"s": 100, "k": 100, "t": 1, "r": 0.05, "sigma": 0.2}

        # Compare different models
        bs_call = quantforge.black_scholes.call_price(**params)
        quantforge.black76.call_price(f=100, k=100, t=1, r=0.05, sigma=0.2)
        merton_call = quantforge.merton.call_price(**params, q=0.0)

        # Should be close but not identical (Black76 uses forward price)
        assert abs(bs_call - merton_call) < 1e-10  # Same when q=0

    def test_data_pipeline(self):
        """Test data processing pipeline."""
        # Simulate market data
        market_data = {
            "spots": np.random.uniform(90, 110, 100),
            "strikes": np.random.uniform(95, 105, 100),
            "times": np.random.uniform(0.1, 2.0, 100),
            "rates": 0.05,
            "sigmas": np.random.uniform(0.1, 0.4, 100),
        }

        # Calculate prices
        prices = quantforge.black_scholes.call_price_batch(**market_data)

        # Calculate Greeks
        greeks = quantforge.black_scholes.greeks_batch(**market_data)

        # Validate results
        assert len(prices) == 100
        assert all(p >= 0 for p in prices)

        # Greeks should be dict of arrays
        assert isinstance(greeks, dict)
        assert all(len(greeks[k]) == 100 for k in greeks)
        assert all(0 <= greeks["delta"][i] <= 1 for i in range(100))

    def test_american_options_workflow(self):
        """Test American options pricing workflow."""
        # Parameters
        spot = 100.0
        strike = 110.0
        time = 1.0
        rate = 0.05
        q = 0.02
        vol = 0.25

        # Calculate American option prices
        am_call = quantforge.american.call_price(spot, strike, time, rate, q, vol)
        am_put = quantforge.american.put_price(spot, strike, time, rate, q, vol)

        # Calculate European equivalents for comparison
        eu_call = quantforge.merton.call_price(spot, strike, time, rate, q, vol)
        eu_put = quantforge.merton.put_price(spot, strike, time, rate, q, vol)

        # American options should be worth at least as much as European
        assert am_call >= eu_call - 1e-10
        assert am_put >= eu_put - 1e-10

        # Calculate Greeks
        am_greeks = quantforge.american.greeks(spot, strike, time, rate, q, vol, is_call=True)

        assert isinstance(am_greeks, dict)
        assert "delta" in am_greeks
        assert "gamma" in am_greeks

    def test_volatility_surface_workflow(self):
        """Test implied volatility surface construction."""
        # Market data grid
        spots = [100.0]
        strikes = np.linspace(80, 120, 9)
        times = [0.25, 0.5, 1.0]
        rate = 0.05

        # Generate synthetic market prices
        market_vols = np.random.uniform(0.15, 0.35, (len(times), len(strikes)))

        results = []
        for t_idx, time in enumerate(times):
            for k_idx, strike in enumerate(strikes):
                for spot in spots:
                    # Calculate price with market vol
                    vol = market_vols[t_idx, k_idx]
                    price = quantforge.black_scholes.call_price(spot, strike, time, rate, vol)

                    # Calculate implied vol from price
                    iv = quantforge.black_scholes.implied_volatility(price, spot, strike, time, rate, is_call=True)

                    # Should recover the original volatility
                    assert abs(iv - vol) < 1e-6

                    results.append(
                        {
                            "spot": spot,
                            "strike": strike,
                            "time": time,
                            "market_vol": vol,
                            "implied_vol": iv,
                            "price": price,
                        }
                    )

        assert len(results) == len(spots) * len(strikes) * len(times)

    def test_portfolio_valuation_workflow(self):
        """Test portfolio valuation workflow."""
        # Portfolio of options
        portfolio = [
            {"type": "call", "spot": 100, "strike": 95, "time": 0.5, "quantity": 10},
            {"type": "put", "spot": 100, "strike": 105, "time": 0.5, "quantity": -5},
            {"type": "call", "spot": 100, "strike": 100, "time": 1.0, "quantity": 20},
        ]

        rate = 0.05
        vol = 0.2

        # Calculate portfolio value
        total_value = 0.0
        total_delta = 0.0
        total_gamma = 0.0
        total_vega = 0.0

        for position in portfolio:
            if position["type"] == "call":
                price = quantforge.black_scholes.call_price(
                    position["spot"], position["strike"], position["time"], rate, vol
                )
                greeks = quantforge.black_scholes.greeks(
                    position["spot"], position["strike"], position["time"], rate, vol, is_call=True
                )
            else:
                price = quantforge.black_scholes.put_price(
                    position["spot"], position["strike"], position["time"], rate, vol
                )
                greeks = quantforge.black_scholes.greeks(
                    position["spot"], position["strike"], position["time"], rate, vol, is_call=False
                )

            total_value += price * position["quantity"]
            total_delta += greeks["delta"] * position["quantity"]
            total_gamma += greeks["gamma"] * position["quantity"]
            total_vega += greeks["vega"] * position["quantity"]

        # Portfolio should have meaningful values
        assert total_value != 0
        assert abs(total_delta) < 1000  # Reasonable delta
        assert abs(total_gamma) < 100  # Reasonable gamma
        assert abs(total_vega) < 1000  # Reasonable vega

    def test_error_handling_workflow(self):
        """Test error handling in various scenarios."""
        # Test invalid inputs
        with pytest.raises(ValueError):
            quantforge.black_scholes.call_price(-100, 100, 1, 0.05, 0.2)  # Negative spot

        with pytest.raises(ValueError):
            quantforge.black_scholes.call_price(100, -100, 1, 0.05, 0.2)  # Negative strike

        with pytest.raises(ValueError):
            quantforge.black_scholes.call_price(100, 100, -1, 0.05, 0.2)  # Negative time

        with pytest.raises(ValueError):
            quantforge.black_scholes.call_price(100, 100, 1, 0.05, -0.2)  # Negative volatility

        # Test edge cases
        # Zero time should give intrinsic value
        price = quantforge.black_scholes.call_price(110, 100, 1e-10, 0.05, 0.2)
        assert abs(price - 10.0) < 0.01

        # Very high volatility
        price = quantforge.black_scholes.call_price(100, 100, 1, 0.05, 5.0)
        assert price > 0 and price < 100

        # Very low volatility
        price = quantforge.black_scholes.call_price(100, 100, 1, 0.05, 0.01)
        assert price > 0

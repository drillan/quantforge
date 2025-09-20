#!/usr/bin/env python3
"""
Market data integration example for QuantForge

This example demonstrates how to integrate QuantForge market utilities
with real trading workflows:
- Processing market data feeds
- Calculating implied volatilities from market prices
- Greeks calculation with market spreads
- Portfolio risk analysis
"""

import numpy as np
import pandas as pd
from quantforge.black_scholes import (
    call_price_batch,
    greeks_batch,
    implied_volatility_batch,
    put_price_batch,
)
from quantforge.market_utils import (
    PricingConfig,
    mid_price_batch_with_metrics,
    weighted_mid_price_batch,
)


def generate_market_data(spot_price=100.0, n_strikes=21):
    """Generate simulated market data for demonstration"""

    # Strike range around ATM
    strikes = np.linspace(spot_price * 0.8, spot_price * 1.2, n_strikes)

    # Time to expiry (various maturities)
    expiries = np.array([7, 14, 30, 60, 90]) / 365.0

    # Risk-free rate
    rate = 0.05

    # Base implied volatility with smile
    moneyness = np.log(strikes / spot_price)
    base_iv = 0.20 + 0.1 * moneyness**2  # Volatility smile

    data = []
    for expiry in expiries:
        for i, strike in enumerate(strikes):
            # Adjust IV for time
            iv = base_iv[i] * (1 + 0.1 * np.sqrt(30 / (expiry * 365)))

            # Calculate theoretical price
            is_call = strike >= spot_price
            if is_call:
                theo_price_array = call_price_batch(
                    np.array([spot_price]), np.array([strike]), np.array([expiry]), np.array([rate]), np.array([iv])
                )
                # Convert from Arrow array to numpy
                theo_price = np.array(theo_price_array)[0]
            else:
                theo_price_array = put_price_batch(
                    np.array([spot_price]), np.array([strike]), np.array([expiry]), np.array([rate]), np.array([iv])
                )
                # Convert from Arrow array to numpy
                theo_price = np.array(theo_price_array)[0]

            # Generate bid/ask with realistic spreads
            if theo_price > 0.01:
                # Spread widens for OTM options
                otm_factor = abs(moneyness[i])
                spread_pct = 0.005 + otm_factor * 0.02

                # Add some noise
                noise = np.random.normal(0, 0.001)
                bid = theo_price * (1 - spread_pct / 2 + noise)
                ask = theo_price * (1 + spread_pct / 2 + noise)

                # Generate volumes (higher near ATM)
                atm_distance = abs(strike - spot_price) / spot_price
                bid_vol = int(1000 * np.exp(-5 * atm_distance))
                ask_vol = int(1000 * np.exp(-5 * atm_distance))
            else:
                # Very deep OTM - might have no bid
                bid = 0
                ask = max(0.01, theo_price * 10)
                bid_vol = 0
                ask_vol = 10

            data.append(
                {
                    "strike": strike,
                    "expiry_days": int(expiry * 365),
                    "type": "C" if is_call else "P",
                    "bid": max(0, bid),
                    "ask": max(bid + 0.01, ask),
                    "bid_vol": bid_vol,
                    "ask_vol": ask_vol,
                    "theo_iv": iv,
                }
            )

    return pd.DataFrame(data), spot_price, rate


def process_market_data(df, spot, rate):
    """Process market data and calculate analytics"""
    print("=" * 60)
    print("Market Data Processing Pipeline")
    print("=" * 60)

    # Group by expiry
    for expiry_days, group in df.groupby("expiry_days"):
        print(f"\n{expiry_days} Days to Expiry")
        print("-" * 40)

        # Convert to arrays
        bids = group["bid"].values
        asks = group["ask"].values
        bid_vols = group["bid_vol"].values
        ask_vols = group["ask_vol"].values
        strikes = group["strike"].values
        types = group["type"].values

        # Calculate mid prices with appropriate config
        if expiry_days <= 7:
            # Near expiry - tighter spreads expected
            config = PricingConfig.with_config(max_spread_pct=0.1)
        else:
            # Longer dated - wider spreads acceptable
            config = PricingConfig.with_config(max_spread_pct=0.5)

        # Process with metrics
        mids, metrics = mid_price_batch_with_metrics(bids, asks, config)

        # Also calculate volume-weighted mids
        _ = weighted_mid_price_batch(bids, asks, bid_vols, ask_vols)

        # Statistics
        valid_mask = ~np.isnan(mids)
        n_valid = np.sum(valid_mask)

        print(f"Contracts processed: {len(group)}")
        print(f"Valid mid prices: {n_valid}/{len(group)}")
        print(f"Average spread: {metrics.mean_spread_pct * 100:.2f}%")
        print(f"Max spread: {metrics.max_spread_pct * 100:.2f}%")

        if metrics.crossed_spreads > 0:
            print(f"⚠️  Crossed spreads detected: {metrics.crossed_spreads}")

        # Calculate implied volatilities from market mids
        if n_valid > 0:
            valid_indices = np.where(valid_mask)[0]
            valid_mids = mids[valid_indices]
            valid_strikes = strikes[valid_indices]
            valid_types = types[valid_indices]

            # Prepare for IV calculation
            spots = np.full(len(valid_mids), spot)
            times = np.full(len(valid_mids), expiry_days / 365.0)
            rates = np.full(len(valid_mids), rate)
            is_calls = valid_types == "C"

            # Calculate IVs
            ivs = implied_volatility_batch(valid_mids, spots, valid_strikes, times, rates, is_calls)

            # Show ATM options
            atm_distance = np.abs(valid_strikes - spot)
            atm_idx = np.argmin(atm_distance)

            print(f"\nATM Option (Strike={valid_strikes[atm_idx]:.1f}):")
            print(f"  Market Mid: {valid_mids[atm_idx]:.3f}")
            print(f"  Implied Vol: {ivs[atm_idx] * 100:.1f}%")

            # Volatility smile
            sorted_indices = np.argsort(valid_strikes)
            smile_strikes = valid_strikes[sorted_indices]
            smile_ivs = ivs[sorted_indices]

            print("\nVolatility Smile:")
            print("  Strike | IV%")
            for i in range(0, len(smile_strikes), max(1, len(smile_strikes) // 5)):
                if not np.isnan(smile_ivs[i]):
                    print(f"  {smile_strikes[i]:6.1f} | {smile_ivs[i] * 100:5.1f}%")


def calculate_portfolio_risk(df, spot, rate, portfolio_positions):
    """Calculate portfolio Greeks using market prices"""
    print("\n" + "=" * 60)
    print("Portfolio Risk Analysis")
    print("=" * 60)

    # Filter to positions we hold
    df_positions = df[df["strike"].isin(portfolio_positions.keys())]

    if df_positions.empty:
        print("No matching positions in market data")
        return

    # Calculate mid prices for our positions
    bids = df_positions["bid"].values
    asks = df_positions["ask"].values

    # Use lenient config for portfolio (we need prices for all positions)
    config = PricingConfig.with_config(max_spread_pct=None)
    mids, _ = mid_price_batch_with_metrics(bids, asks, config)

    # Prepare Greeks calculation
    strikes = df_positions["strike"].values
    expiries = df_positions["expiry_days"].values / 365.0
    types = df_positions["type"].values

    spots = np.full(len(mids), spot)
    rates = np.full(len(mids), rate)

    # Calculate IVs first
    is_calls = types == "C"
    ivs = implied_volatility_batch(mids, spots, strikes, expiries, rates, is_calls)

    # Replace NaN IVs with reasonable defaults
    median_iv = np.nanmedian(ivs)
    ivs = np.where(np.isnan(ivs), median_iv, ivs)

    # Calculate Greeks
    greeks = greeks_batch(spots, strikes, expiries, rates, ivs, is_calls)

    # Aggregate portfolio Greeks
    total_delta = 0
    total_gamma = 0
    total_vega = 0
    total_theta = 0

    print("\nPosition-Level Greeks:")
    print("Strike | Type | Qty   | Delta   | Gamma   | Vega    | Theta")
    print("-" * 65)

    for i, (_strike, row) in enumerate(df_positions.iterrows()):
        qty = portfolio_positions.get(row["strike"], 0)

        # Position Greeks
        pos_delta = greeks["delta"][i] * qty
        pos_gamma = greeks["gamma"][i] * qty
        pos_vega = greeks["vega"][i] * qty
        pos_theta = greeks["theta"][i] * qty

        total_delta += pos_delta
        total_gamma += pos_gamma
        total_vega += pos_vega
        total_theta += pos_theta

        print(
            f"{row['strike']:6.1f} | {row['type']:4s} | {qty:5d} | "
            f"{pos_delta:7.2f} | {pos_gamma:7.4f} | "
            f"{pos_vega:7.2f} | {pos_theta:6.2f}"
        )

    print("\nPortfolio-Level Greeks:")
    print(f"  Total Delta: {total_delta:+.2f}")
    print(f"  Total Gamma: {total_gamma:+.4f}")
    print(f"  Total Vega:  {total_vega:+.2f}")
    print(f"  Total Theta: {total_theta:+.2f} per day")

    # Risk scenarios
    print("\nRisk Scenarios:")
    print("  1% spot move: P&L ≈ ${total_delta * spot * 0.01:+,.0f}")
    print("  5% spot move: P&L ≈ ${(total_delta * spot * 0.05 + 0.5 * total_gamma * (spot * 0.05)**2):+,.0f}")
    print("  1 vol point:  P&L ≈ ${total_vega:+,.0f}")
    print("  1 day decay:  P&L ≈ ${total_theta:+,.0f}")


def main():
    """Main execution"""
    print("=" * 60)
    print("QuantForge Market Integration Example")
    print("=" * 60)

    # Generate simulated market data
    print("\nGenerating market data...")
    df, spot, rate = generate_market_data(spot_price=100.0, n_strikes=21)

    print(f"Spot price: ${spot:.2f}")
    print(f"Risk-free rate: {rate * 100:.1f}%")
    print(f"Total options: {len(df)}")

    # Process market data
    process_market_data(df, spot, rate)

    # Example portfolio
    portfolio_positions = {
        100.0: 10,  # Long 10 ATM calls
        95.0: -5,  # Short 5 OTM puts
        105.0: -5,  # Short 5 OTM calls
        90.0: 2,  # Long 2 deep OTM puts (protection)
    }

    # Calculate portfolio risk
    calculate_portfolio_risk(df, spot, rate, portfolio_positions)

    print("\n" + "=" * 60)
    print("Integration example completed successfully!")


if __name__ == "__main__":
    np.random.seed(42)  # For reproducible results
    main()

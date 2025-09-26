#!/usr/bin/env python3
"""
Batch processing examples for QuantForge market utilities

This example demonstrates:
- Large-scale batch processing with Arrow arrays
- Broadcasting for scalar/array combinations
- Metrics collection during processing
- Real options chain analysis
"""

import math
import time

import numpy as np
from quantforge.market_utils import (
    PricingConfig,
    mid_price_batch,
    mid_price_batch_with_metrics,
    spread_batch,
    spread_pct_batch,
    weighted_mid_price_batch,
)


def example_basic_batch():
    """Basic batch processing examples"""
    print("=" * 60)
    print("Basic Batch Processing")
    print("=" * 60)

    # Multiple price pairs
    bids = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
    asks = np.array([100.2, 101.3, 102.4, 103.1, 104.5])

    mids = mid_price_batch(bids, asks)
    spreads = spread_batch(bids, asks)
    spread_pcts = spread_pct_batch(bids, asks) * 100

    print("Batch processing results:")
    print("Index | Bid    | Ask    | Mid     | Spread | Spread%")
    print("-" * 55)
    for i in range(len(bids)):
        print(f"{i:5d} | {bids[i]:6.1f} | {asks[i]:6.1f} | {mids[i]:7.2f} | {spreads[i]:6.2f} | {spread_pcts[i]:6.3f}%")

    print(f"\nProcessed {len(bids)} price pairs")
    print(f"Average mid: {np.mean(mids):.2f}")
    print(f"Average spread: {np.mean(spreads):.2f}")
    print(f"Average spread%: {np.mean(spread_pcts):.3f}%")


def example_broadcasting():
    """Broadcasting examples with scalar/array combinations"""
    print("\n" + "=" * 60)
    print("Broadcasting Examples")
    print("=" * 60)

    # Scenario 1: Fixed bid, multiple asks
    print("Fixed bid, multiple asks:")
    bid = np.array([100.0])  # Scalar as 1-element array
    asks = np.array([100.1, 100.2, 100.3, 100.4, 100.5])
    mids = mid_price_batch(bid, asks)
    print(f"  Bid: {bid[0]}")
    print(f"  Asks: {asks}")
    print(f"  Mids: {mids}")

    # Scenario 2: Multiple bids, fixed ask
    print("\nMultiple bids, fixed ask:")
    bids = np.array([99.5, 99.6, 99.7, 99.8, 99.9])
    ask = np.array([100.0])  # Scalar
    mids = mid_price_batch(bids, ask)
    print(f"  Bids: {bids}")
    print(f"  Ask: {ask[0]}")
    print(f"  Mids: {mids}")

    # Scenario 3: Scalar spread analysis
    print("\nScalar spread analysis:")
    bids = np.array([100.0, 101.0, 102.0])
    ask = np.array([102.5])  # Fixed ask for all
    spreads = spread_batch(bids, ask)
    print(f"  Bids: {bids}")
    print(f"  Ask: {ask[0]}")
    print(f"  Spreads: {spreads}")


def example_with_metrics():
    """Batch processing with metrics collection"""
    print("\n" + "=" * 60)
    print("Batch Processing with Metrics")
    print("=" * 60)

    # Mixed quality data
    n = 20
    np.random.seed(42)

    # Generate realistic market data
    bids = np.random.uniform(95, 105, n)
    # Some normal spreads, some wide, some crossed
    spreads = np.random.choice([0.1, 0.5, 2.0, 10.0, -0.5], n)
    asks = bids + spreads

    # Add some extreme cases
    bids[0] = 1.0
    asks[0] = 1000.0  # Extreme spread
    bids[1] = 105.0
    asks[1] = 100.0  # Crossed
    bids[2] = 100.0
    asks[2] = 100.01  # Very tight

    # Process with metrics
    config = PricingConfig.with_config(max_spread_pct=0.1)  # 10% limit
    mids, metrics = mid_price_batch_with_metrics(bids, asks, config)

    print(f"Processing {n} price pairs with 10% spread limit")
    print("\nMetrics:")
    print(f"  Total processed: {metrics.total_processed}")
    print(f"  NaN results: {metrics.nan_count}")
    print(f"  Valid results: {metrics.total_processed - metrics.nan_count}")
    print(f"  Crossed spreads: {metrics.crossed_spreads}")
    print(f"  Abnormal spreads: {metrics.abnormal_spreads}")
    print(f"  Mean spread %: {metrics.mean_spread_pct * 100:.2f}%")
    print(f"  Max spread %: {metrics.max_spread_pct * 100:.2f}%")

    # Show some examples
    print("\nSample results:")
    print("Index | Bid    | Ask     | Mid     | Status")
    print("-" * 50)
    for i in range(min(5, n)):
        mid_str = f"{mids[i]:7.2f}" if not math.isnan(mids[i]) else "    NaN"
        status = "Valid" if not math.isnan(mids[i]) else "Filtered"
        print(f"{i:5d} | {bids[i]:6.2f} | {asks[i]:7.2f} | {mid_str} | {status}")


def example_weighted_batch():
    """Volume-weighted batch processing"""
    print("\n" + "=" * 60)
    print("Volume-Weighted Batch Processing")
    print("=" * 60)

    # Order book simulation
    n_levels = 5
    base_price = 100.0

    # Create order book levels
    bid_prices = base_price - np.arange(n_levels) * 0.01
    ask_prices = base_price + 0.01 + np.arange(n_levels) * 0.01

    # Volume typically increases away from mid
    bid_volumes = np.array([100, 250, 500, 1000, 2000])
    ask_volumes = np.array([150, 300, 450, 800, 1500])

    # Calculate weighted mids for each level
    weighted_mids = weighted_mid_price_batch(bid_prices, ask_prices, bid_volumes, ask_volumes)

    # Compare with simple mids
    simple_mids = mid_price_batch(bid_prices, ask_prices)

    print("Order Book Levels:")
    print("Level | Bid Price@Vol  | Ask Price@Vol  | Simple | Weighted | Diff")
    print("-" * 70)
    for i in range(n_levels):
        diff = weighted_mids[i] - simple_mids[i]
        print(
            f"{i:5d} | {bid_prices[i]:.2f}@{bid_volumes[i]:4.0f} | "
            f"{ask_prices[i]:.2f}@{ask_volumes[i]:4.0f} | "
            f"{simple_mids[i]:.3f} | {weighted_mids[i]:.3f} | "
            f"{diff:+.3f}"
        )

    # Volume imbalance analysis
    total_bid_vol = np.sum(bid_volumes)
    total_ask_vol = np.sum(ask_volumes)
    imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol)
    print(f"\nTotal bid volume: {total_bid_vol:.0f}")
    print(f"Total ask volume: {total_ask_vol:.0f}")
    print(f"Volume imbalance: {imbalance * 100:+.1f}%")


def example_options_chain():
    """Real-world options chain processing"""
    print("\n" + "=" * 60)
    print("Options Chain Processing (Nikkei 225 Simulation)")
    print("=" * 60)

    # Generate realistic options chain
    spot = 45000
    n_strikes = 41  # ±20 strikes from ATM
    strikes = np.linspace(40000, 50000, n_strikes)

    # Time to expiry affects spreads
    _ = 30 / 365  # 30 days

    print(f"Spot price: {spot:,.0f}")
    print(f"Strikes: {strikes[0]:,.0f} to {strikes[-1]:,.0f}")
    print(f"Number of strikes: {n_strikes}")

    # Generate realistic bid/ask based on moneyness
    moneyness = (strikes - spot) / spot
    base_value = spot * 0.01  # Base option value

    # Option values decrease away from ATM
    values = base_value * np.exp(-10 * moneyness**2)

    # Spreads widen for OTM options
    spread_pcts = 0.002 + np.abs(moneyness) * 2.0

    # Generate bid/ask
    bids = values * (1 - spread_pcts / 2)
    asks = values * (1 + spread_pcts / 2)

    # Deep OTM might have zero bid
    bids[np.abs(moneyness) > 0.15] *= 0.1
    bids[bids < 1] = 0  # No bid below 1

    # Process with different configurations
    configs = [
        ("Default (50%)", PricingConfig()),
        ("Strict (5%)", PricingConfig.with_config(max_spread_pct=0.05)),
        ("No limit", PricingConfig.with_config(max_spread_pct=None)),
    ]

    for config_name, config in configs:
        mids, metrics = mid_price_batch_with_metrics(bids, asks, config)
        valid_count = metrics.total_processed - metrics.nan_count

        print(f"\n{config_name} configuration:")
        print(f"  Valid prices: {valid_count}/{n_strikes}")
        print(f"  Filtered: {metrics.nan_count}")
        print(f"  Mean spread: {metrics.mean_spread_pct * 100:.1f}%")
        print(f"  Max spread: {metrics.max_spread_pct * 100:.1f}%")

        # Show ATM ± 2 strikes
        atm_idx = n_strikes // 2
        print("\n  Strike  | Bid     | Ask      | Mid      | Spread%")
        print("  " + "-" * 52)
        for i in range(atm_idx - 2, atm_idx + 3):
            mid_val = mids[i]
            mid_str = f"{mid_val:8.2f}" if not math.isnan(mid_val) else "     NaN"
            spread_pct_val = spread_pcts[i] * 100
            print(f"  {strikes[i]:7.0f} | {bids[i]:7.2f} | {asks[i]:8.2f} | {mid_str} | {spread_pct_val:6.1f}%")


def example_performance():
    """Performance comparison for different batch sizes"""
    print("\n" + "=" * 60)
    print("Performance Analysis")
    print("=" * 60)

    sizes = [100, 1_000, 10_000, 100_000]
    print("Batch Size | Time (ms) | Rate (million/sec)")
    print("-" * 45)

    for size in sizes:
        # Generate data
        np.random.seed(42)
        bids = np.random.uniform(99, 101, size)
        asks = bids + np.random.uniform(0.01, 0.5, size)

        # Time the processing
        start = time.perf_counter()
        _ = mid_price_batch(bids, asks)
        elapsed = (time.perf_counter() - start) * 1000

        rate = size / elapsed / 1000  # Million per second
        print(f"{size:10,d} | {elapsed:9.2f} | {rate:18.2f}")

    print("\nNote: Parallel processing kicks in at 10,000+ elements")


if __name__ == "__main__":
    print("QuantForge Market Utilities - Batch Processing Examples")
    print("=" * 60)

    example_basic_batch()
    example_broadcasting()
    example_with_metrics()
    example_weighted_batch()
    example_options_chain()
    example_performance()

    print("\n" + "=" * 60)
    print("Batch examples completed successfully!")

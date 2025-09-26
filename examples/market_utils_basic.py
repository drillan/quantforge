#!/usr/bin/env python3
"""
Basic market utilities examples for QuantForge

This example demonstrates:
- Simple mid-price calculation
- Handling abnormal spreads in options markets
- Volume-weighted mid prices
- Spread analysis
"""

import math

from quantforge.market_utils import (
    PricingConfig,
    mid_price,
    mid_price_with_config,
    spread,
    spread_pct,
    weighted_mid_price,
)


def example_simple_mid_price():
    """Basic mid-price calculation examples"""
    print("=" * 60)
    print("Simple Mid-Price Examples")
    print("=" * 60)

    # Normal spread in liquid market
    bid, ask = 100.0, 100.2
    mid = mid_price(bid, ask)
    print(f"Normal spread: bid={bid}, ask={ask}")
    print(f"  Mid price: {mid:.2f}")
    print(f"  Spread: {spread(bid, ask):.2f}")
    print(f"  Spread %: {spread_pct(bid, ask) * 100:.3f}%")

    # Wide spread in options market
    bid, ask = 10.0, 15.0
    mid = mid_price(bid, ask)
    print(f"\nWide spread (33%): bid={bid}, ask={ask}")
    print(f"  Mid price: {mid:.2f}")
    print(f"  Spread %: {spread_pct(bid, ask) * 100:.1f}%")

    # Extreme spread (typical for deep OTM options)
    bid, ask = 1.0, 100.0
    mid = mid_price(bid, ask)
    print(f"\nExtreme spread: bid={bid}, ask={ask}")
    print(f"  Mid price: {mid}")
    print(f"  Result: {'NaN (filtered)' if math.isnan(mid) else f'{mid:.2f}'}")

    # Crossed spread (market anomaly)
    bid, ask = 105.0, 100.0
    mid = mid_price(bid, ask)
    print(f"\nCrossed spread: bid={bid}, ask={ask}")
    print(f"  Mid price: {mid}")
    print(f"  Result: {'NaN (invalid)' if math.isnan(mid) else f'{mid:.2f}'}")


def example_custom_config():
    """Examples with custom pricing configuration"""
    print("\n" + "=" * 60)
    print("Custom Configuration Examples")
    print("=" * 60)

    # No spread limit for illiquid options
    config_no_limit = PricingConfig.with_config(max_spread_pct=None)
    bid, ask = 1.0, 1000.0
    mid = mid_price_with_config(bid, ask, config_no_limit)
    print(f"No spread limit: bid={bid}, ask={ask}")
    print("  Config: max_spread_pct=None")
    print(f"  Mid price: {mid:.2f}")

    # Strict limit for forex/futures
    config_strict = PricingConfig.with_config(max_spread_pct=0.001)  # 0.1%
    bid, ask = 100.0, 100.15
    mid = mid_price_with_config(bid, ask, config_strict)
    print(f"\nStrict limit (0.1%): bid={bid}, ask={ask}")
    print(f"  Spread: {spread_pct(bid, ask) * 100:.3f}%")
    print(f"  Result: {'NaN (exceeds limit)' if math.isnan(mid) else f'{mid:.2f}'}")

    # Auto-swap crossed spreads
    config_swap = PricingConfig.with_config(crossed_handling="swap_and_continue")
    bid, ask = 105.0, 100.0
    mid = mid_price_with_config(bid, ask, config_swap)
    print(f"\nAuto-swap crossed: bid={bid}, ask={ask}")
    print("  Config: crossed_handling='swap_and_continue'")
    print(f"  Mid price: {mid:.2f} (swapped to {ask}, {bid})")


def example_weighted_mid_price():
    """Volume-weighted mid-price examples"""
    print("\n" + "=" * 60)
    print("Volume-Weighted Mid-Price Examples")
    print("=" * 60)

    # Equal volumes (same as simple mid)
    bid, ask = 100.0, 100.2
    bid_qty, ask_qty = 1000.0, 1000.0
    simple = mid_price(bid, ask)
    weighted = weighted_mid_price(bid, ask, bid_qty, ask_qty)
    print(f"Equal volumes: bid={bid}@{bid_qty}, ask={ask}@{ask_qty}")
    print(f"  Simple mid: {simple:.3f}")
    print(f"  Weighted mid: {weighted:.3f}")
    print(f"  Difference: {abs(weighted - simple):.6f}")

    # Heavy bid side (price pulled down)
    bid_qty, ask_qty = 5000.0, 1000.0
    weighted = weighted_mid_price(bid, ask, bid_qty, ask_qty)
    print(f"\nHeavy bid side: bid={bid}@{bid_qty}, ask={ask}@{ask_qty}")
    print(f"  Simple mid: {simple:.3f}")
    print(f"  Weighted mid: {weighted:.3f}")
    print(f"  Pulled toward bid by: {simple - weighted:.3f}")

    # Heavy ask side (price pulled up)
    bid_qty, ask_qty = 1000.0, 5000.0
    weighted = weighted_mid_price(bid, ask, bid_qty, ask_qty)
    print(f"\nHeavy ask side: bid={bid}@{bid_qty}, ask={ask}@{ask_qty}")
    print(f"  Simple mid: {simple:.3f}")
    print(f"  Weighted mid: {weighted:.3f}")
    print(f"  Pulled toward ask by: {weighted - simple:.3f}")

    # Missing quantities (fallback to simple)
    weighted = weighted_mid_price(bid, ask)
    print(f"\nNo quantities provided: bid={bid}, ask={ask}")
    print(f"  Weighted mid: {weighted:.3f}")
    print(f"  Falls back to simple: {weighted == simple}")


def example_real_world_scenario():
    """Real-world market data scenario"""
    print("\n" + "=" * 60)
    print("Real-World Scenario: Options Market Making")
    print("=" * 60)

    # Simulated option chain (ATM ± 5 strikes)
    strikes = [95, 97.5, 100, 102.5, 105]
    spot = 100.0

    print(f"Underlying price: {spot}")
    print(f"Strikes: {strikes}")
    print("\nCall options:")
    print("Strike | Bid    | Ask     | Mid    | Spread% | Valid")
    print("-" * 55)

    for strike in strikes:
        # Spread widens for OTM options
        _ = max(spot - strike, 0) / spot
        base_spread = 0.002 if strike <= spot else 0.01
        spread_multiplier = 1 + abs(spot - strike) / spot * 10

        # Generate bid/ask
        if strike <= spot:  # ITM/ATM
            intrinsic = spot - strike
            time_value = 2.0 * math.exp(-abs(spot - strike) / 10)
            fair_value = intrinsic + time_value
            spread_pct_val = base_spread * spread_multiplier
        else:  # OTM
            time_value = 2.0 * math.exp(-abs(spot - strike) / 5)
            fair_value = time_value
            spread_pct_val = base_spread * spread_multiplier

        half_spread = fair_value * spread_pct_val / 2
        bid = max(0.01, fair_value - half_spread)
        ask = fair_value + half_spread

        # Calculate mid with default config
        mid = mid_price(bid, ask)
        spread_pct_val = spread_pct(bid, ask) * 100
        is_valid = not math.isnan(mid)

        mid_str = f"{mid:6.2f}" if is_valid else "   NaN"
        print(
            f"{strike:5.1f} | {bid:6.2f} | {ask:7.2f} | "
            f"{mid_str} | "
            f"{spread_pct_val:6.1f}% | "
            f"{'Yes' if is_valid else 'No'}"
        )

    print("\nNote: Deep OTM options filtered due to wide spreads")


if __name__ == "__main__":
    print("QuantForge Market Utilities Examples")
    print("=" * 60)

    example_simple_mid_price()
    example_custom_config()
    example_weighted_mid_price()
    example_real_world_scenario()

    print("\n" + "=" * 60)
    print("Examples completed successfully!")

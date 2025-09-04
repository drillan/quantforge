#!/usr/bin/env python3
"""BS2002内部計算のデバッグ"""

import math


def bs2002_call_debug(s, k, t, r, q, sigma):
    """BS2002 call計算の内部をPythonで再現してデバッグ"""

    TIME_NEAR_EXPIRY_THRESHOLD = 1e-7

    if t < TIME_NEAR_EXPIRY_THRESHOLD:
        return max(s - k, 0.0)

    if q <= 0.0:
        print("No dividend case, returning European value")
        return None  # Would return European value

    b = r - q
    sigma_sq = sigma * sigma

    # Calculate beta
    inner = b / sigma_sq - 0.5
    beta = 0.5 - b / sigma_sq + math.sqrt(inner * inner + 2.0 * r / sigma_sq)

    # Calculate B_infinity (perpetual exercise boundary)
    b_inf = beta / (beta - 1.0) * k

    # Calculate B0 (zero time exercise boundary)
    b0 = max(k, r * k / q)

    # Calculate h(t) - time to maturity factor
    h_t = -(b * t + 2.0 * sigma * math.sqrt(t))

    # Calculate trigger price I
    i = b0 + (b_inf - b0) * (1.0 - math.exp(h_t))

    print("BS2002 Call Internal Values:")
    print(f"  s={s}, k={k}, t={t}, r={r}, q={q}, sigma={sigma}")
    print(f"  b (cost of carry) = r - q = {b:.4f}")
    print(f"  beta = {beta:.4f}")
    print(f"  B_infinity = {b_inf:.4f}")
    print(f"  B0 = {b0:.4f}")
    print(f"  h(t) = {h_t:.4f}")
    print(f"  exp(h(t)) = {math.exp(h_t):.4f}")
    print(f"  Trigger price I = {i:.4f}")
    print(f"  s >= I? {s >= i} (immediate exercise)")
    print()

    if s >= i:
        return s - k

    # If not immediate exercise, would calculate psi functions
    alpha = (i - k) * i ** (-beta)
    print(f"  alpha = {alpha:.6f}")
    print("  Would calculate 6 psi terms...")

    return None


def test_cases():
    """Various test cases"""

    print("=" * 60)
    print("Test 1: Call with small dividend (q=0.03)")
    print("=" * 60)
    result = bs2002_call_debug(100, 100, 1.0, 0.05, 0.03, 0.2)
    if result is not None:
        print(f"Result: {result:.4f}")
    print()

    print("=" * 60)
    print("Test 2: Call with larger dividend (q=0.05)")
    print("=" * 60)
    result = bs2002_call_debug(100, 100, 1.0, 0.05, 0.05, 0.2)
    if result is not None:
        print(f"Result: {result:.4f}")
    print()

    print("=" * 60)
    print("Test 3: Put via transformation (swap S/K and r/q)")
    print("=" * 60)
    print("P(S=100,K=100,r=0.05,q=0) = C(S=100,K=100,r=0,q=0.05)")
    result = bs2002_call_debug(100, 100, 1.0, 0.0, 0.05, 0.2)
    if result is not None:
        print(f"Result: {result:.4f}")
    print()


if __name__ == "__main__":
    test_cases()

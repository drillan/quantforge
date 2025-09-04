#!/usr/bin/env python3
"""BS2002実装のデバッグテスト"""

import sys

sys.path.insert(0, ".")

import quantforge


def test_bs2002_call_no_dividend():
    """配当なしの場合、American Call = European Call"""
    s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2

    # American call (BS2002)
    american = quantforge.american.call_price(s, k, t, r, q, sigma)
    # European call (Merton)
    european = quantforge.merton.call_price(s, k, t, r, q, sigma)

    print("No dividend test:")
    print(f"  American call (BS2002): {american:.4f}")
    print(f"  European call (Merton): {european:.4f}")
    print(f"  Difference: {abs(american - european):.6f}")
    print(f"  Should be equal (diff < 1e-6): {abs(american - european) < 1e-6}")
    print()


def test_bs2002_call_with_dividend():
    """配当ありの場合のAmerican Call"""
    s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.03, 0.2

    # American call (BS2002)
    american = quantforge.american.call_price(s, k, t, r, q, sigma)
    # European call (Merton)
    european = quantforge.merton.call_price(s, k, t, r, q, sigma)

    print("With dividend test (call):")
    print(f"  American call (BS2002): {american:.4f}")
    print(f"  European call (Merton): {european:.4f}")
    print(f"  Early exercise premium: {american - european:.4f}")
    print(f"  American >= European: {american >= european}")
    print()


def test_bs2002_put():
    """BS2002 Put実装テスト（BENCHOP比較）"""
    s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.0, 0.2

    # American put (BS2002)
    american = quantforge.american.put_price(s, k, t, r, q, sigma)
    benchop = 6.248

    error = abs(american - benchop) / benchop * 100

    print("BS2002 Put test (BENCHOP comparison):")
    print(f"  American put (BS2002): {american:.4f}")
    print(f"  BENCHOP reference: {benchop:.3f}")
    print(f"  Error: {error:.2f}%")
    print(f"  Target (<1%): {error < 1.0}")
    print()


def test_put_call_transformation():
    """Put-Call変換の検証"""
    s, k, t, r, q, sigma = 100.0, 100.0, 1.0, 0.05, 0.03, 0.2

    # Direct put calculation (if we had it)
    # For now, test the transformation formula

    # P(S,K,r,q) should equal C(K,S,q,r)
    put_direct = quantforge.american.put_price(s, k, t, r, q, sigma)
    call_transformed = quantforge.american.call_price(k, s, t, q, r, sigma)

    print("Put-Call transformation test:")
    print(f"  Put P(S={s},K={k},r={r},q={q}): {put_direct:.4f}")
    print(f"  Call C(S={k},K={s},r={q},q={r}): {call_transformed:.4f}")
    print("  These should be equal for correct transformation")
    print()


def test_boundary_conditions():
    """境界条件のテスト"""
    k = 100.0
    t, r, q, sigma = 1.0, 0.05, 0.0, 0.2

    print("Boundary conditions test:")

    # Deep ITM put
    s = 50.0
    put_price = quantforge.american.put_price(s, k, t, r, q, sigma)
    intrinsic = k - s
    print(f"  Deep ITM put (S={s}, K={k}):")
    print(f"    Price: {put_price:.4f}")
    print(f"    Intrinsic: {intrinsic:.4f}")
    print(f"    Should be >= intrinsic: {put_price >= intrinsic}")

    # Deep OTM put
    s = 150.0
    put_price = quantforge.american.put_price(s, k, t, r, q, sigma)
    print(f"  Deep OTM put (S={s}, K={k}):")
    print(f"    Price: {put_price:.4f}")
    print(f"    Should be small: {put_price < 1.0}")

    # At the money
    s = 100.0
    put_price = quantforge.american.put_price(s, k, t, r, q, sigma)
    print(f"  ATM put (S={s}, K={k}):")
    print(f"    Price: {put_price:.4f}")
    print()


if __name__ == "__main__":
    test_bs2002_call_no_dividend()
    test_bs2002_call_with_dividend()
    test_bs2002_put()
    test_put_call_transformation()
    test_boundary_conditions()

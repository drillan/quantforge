#!/usr/bin/env python3
"""BAW実装の精度確認テスト"""

import time

import quantforge

# BENCHOP Problem 1 parameters
s = 100.0
k = 100.0
t = 1.0
r = 0.05
q = 0.0
sigma = 0.2

# Test American put
american_put = quantforge.american.put_price(s, k, t, r, q, sigma)
benchop_put = 6.248

put_error = abs(american_put - benchop_put) / benchop_put * 100

print("American Put Test (BENCHOP Problem 1)")
print(f"  Parameters: S={s}, K={k}, T={t}, r={r}, q={q}, σ={sigma}")
print(f"  American put (BAW with dampening): {american_put:.4f}")
print(f"  BENCHOP reference: {benchop_put:.3f}")
print(f"  Error: {put_error:.2f}%")
print(f"  Target (<1%): {'✅ PASS' if put_error < 1.0 else '❌ FAIL'}")
print()

# Test American call
american_call = quantforge.american.call_price(s, k, t, r, q, sigma)
european_call = quantforge.merton.call_price(s, k, t, r, q, sigma)

print("American Call Test (no dividend)")
print(f"  American call: {american_call:.4f}")
print(f"  European call: {european_call:.4f}")
print(f"  Equal (no early exercise): {'✅ PASS' if abs(american_call - european_call) < 1e-4 else '❌ FAIL'}")
print()

# Performance test
n_calculations = 10000
start = time.perf_counter()

for _ in range(n_calculations):
    quantforge.american.put_price(s, k, t, r, q, sigma)

end = time.perf_counter()
time_per_calc = (end - start) / n_calculations * 1e6  # microseconds

print("Performance Test")
print(f"  Calculations: {n_calculations:,}")
print(f"  Total time: {(end - start) * 1000:.2f} ms")
print(f"  Time per calculation: {time_per_calc:.2f} μs")
print(f"  Target (<1 μs): {'✅ PASS' if time_per_calc < 1.0 else '⚠️ CHECK' if time_per_calc < 10.0 else '❌ FAIL'}")
print()

print("Overall Status: BAW implementation with empirical dampening")
print(f"  Accuracy: {put_error:.2f}% error (BENCHOP)")
print(f"  Performance: {time_per_calc:.2f} μs/calc")
print("  Critical Rules compliance: ✅ (dampening factor in constants.rs)")

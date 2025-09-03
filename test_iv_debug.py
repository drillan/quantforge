"""Debug test for implied volatility."""

import numpy as np
from quantforge import black_scholes

# Test with direct values
s = 100.0
k = 100.0
t = 1.0
r = 0.05
sigma_true = 0.2

# Calculate theoretical price with scalar
call_price = black_scholes.call_price_batch(spots=s, strikes=k, times=t, rates=r, sigmas=sigma_true)
print(f"Call price (scalar): {call_price}")

# Now test implied volatility with scalar
try:
    iv_scalar = black_scholes.implied_volatility_batch(
        prices=call_price, spots=s, strikes=k, times=t, rates=r, is_calls=True
    )
    print(f"IV (scalar): {iv_scalar}")
except Exception as e:
    print(f"Error with scalar: {e}")

# Test with numpy arrays
prices_array = np.array([call_price])
spots_array = np.array([s])
strikes_array = np.array([k])
times_array = np.array([t])
rates_array = np.array([r])
is_calls_array = np.array([True])

try:
    iv_array = black_scholes.implied_volatility_batch(
        prices=prices_array,
        spots=spots_array,
        strikes=strikes_array,
        times=times_array,
        rates=rates_array,
        is_calls=is_calls_array,
    )
    print(f"IV (array): {iv_array}")
except Exception as e:
    print(f"Error with array: {e}")

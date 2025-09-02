"""Test for Arrow FFI implementation using pyo3-arrow and arro3-core"""

import numpy as np
import pytest

try:
    import pyarrow as pa

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False
    pa = None

import quantforge


@pytest.mark.skipif(not HAS_PYARROW, reason="PyArrow not installed")
def test_arrow_native_call_price():
    """Test Arrow native call price calculation"""
    # Create Arrow arrays
    spots = pa.array([100.0, 110.0, 120.0])
    strikes = pa.array([105.0, 105.0, 105.0])
    times = pa.array([1.0, 1.0, 1.0])
    rates = pa.array([0.05, 0.05, 0.05])
    sigmas = pa.array([0.2, 0.2, 0.2])

    # Calculate call prices
    result = quantforge.arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)

    # Result should be an Arrow array
    assert hasattr(result, "__arrow_c_array__"), "Result should support Arrow C Data Interface"

    # Convert to numpy for validation
    result_np = np.array(result)

    # Validate results
    assert len(result_np) == 3
    assert all(result_np > 0), "All call prices should be positive"

    # S=100, K=105 should have lower price than S=120, K=105
    assert result_np[0] < result_np[2], "Higher spot price should give higher call value"


@pytest.mark.skipif(not HAS_PYARROW, reason="PyArrow not installed")
def test_arrow_native_put_price():
    """Test Arrow native put price calculation"""
    # Create Arrow arrays
    spots = pa.array([100.0, 90.0, 80.0])
    strikes = pa.array([105.0, 105.0, 105.0])
    times = pa.array([1.0, 1.0, 1.0])
    rates = pa.array([0.05, 0.05, 0.05])
    sigmas = pa.array([0.2, 0.2, 0.2])

    # Calculate put prices
    result = quantforge.arrow_native.arrow_put_price(spots, strikes, times, rates, sigmas)

    # Result should be an Arrow array
    assert hasattr(result, "__arrow_c_array__"), "Result should support Arrow C Data Interface"

    # Convert to numpy for validation
    result_np = np.array(result)

    # Validate results
    assert len(result_np) == 3
    assert all(result_np > 0), "All put prices should be positive"

    # S=100, K=105 should have lower price than S=80, K=105
    assert result_np[0] < result_np[2], "Lower spot price should give higher put value"


@pytest.mark.skipif(not HAS_PYARROW, reason="PyArrow not installed")
def test_arrow_large_batch():
    """Test Arrow native with large batch"""
    n = 10000

    # Create large Arrow arrays
    spots = pa.array([100.0] * n)
    strikes = pa.array([105.0] * n)
    times = pa.array([1.0] * n)
    rates = pa.array([0.05] * n)
    sigmas = pa.array([0.2] * n)

    # Calculate call prices
    result = quantforge.arrow_native.arrow_call_price(spots, strikes, times, rates, sigmas)

    # Convert to numpy
    result_np = np.array(result)

    # All values should be the same
    assert len(result_np) == n
    assert np.allclose(result_np, result_np[0]), "All identical inputs should give identical outputs"


@pytest.mark.skipif(not HAS_PYARROW, reason="PyArrow not installed")
def test_arrow_error_handling():
    """Test error handling in Arrow native implementation"""
    with pytest.raises(Exception):
        # Wrong type - should fail
        quantforge.arrow_native.arrow_call_price(
            [100.0],  # Not an Arrow array
            pa.array([105.0]),
            pa.array([1.0]),
            pa.array([0.05]),
            pa.array([0.2]),
        )


if __name__ == "__main__":
    # Run basic tests
    if HAS_PYARROW:
        test_arrow_native_call_price()
        test_arrow_native_put_price()
        test_arrow_large_batch()
        print("All Arrow FFI tests passed!")
    else:
        print("PyArrow not installed, skipping Arrow FFI tests")

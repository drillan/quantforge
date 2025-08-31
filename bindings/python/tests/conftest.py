"""Test configuration and fixtures for bindings tests"""

import numpy as np
import pytest

# Test constants
TOLERANCE = 1e-10
PRACTICAL_TOLERANCE = 1e-6

# Standard test values
SPOT = 100.0
STRIKE = 100.0
TIME = 1.0
RATE = 0.05
SIGMA = 0.2
DIVIDEND_YIELD = 0.02


@pytest.fixture
def standard_inputs():
    """Standard test inputs for single calculations"""
    return {"s": SPOT, "k": STRIKE, "t": TIME, "r": RATE, "sigma": SIGMA, "q": DIVIDEND_YIELD}


@pytest.fixture
def batch_inputs():
    """Standard batch test inputs"""
    return {
        "spots": np.array([90.0, 100.0, 110.0]),
        "strikes": np.array([95.0, 100.0, 105.0]),
        "times": np.array([0.5, 1.0, 1.5]),
        "rates": np.array([0.04, 0.05, 0.06]),
        "sigmas": np.array([0.18, 0.20, 0.22]),
    }


@pytest.fixture
def large_batch():
    """Large batch for performance testing"""
    size = 100_000
    return {
        "spots": np.random.uniform(80, 120, size),
        "strikes": np.full(size, 100.0),
        "times": np.full(size, 1.0),
        "rates": np.full(size, 0.05),
        "sigmas": np.full(size, 0.20),
    }

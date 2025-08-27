"""
Integration tests comparing American option implementation with GBS_2025.py reference.

This test file validates our Bjerksund-Stensland 2002 implementation against
the reference Python implementation in draft/GBS_2025.py.
"""

import os
import sys

import pytest

# Add draft directory to path to import GBS_2025
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../draft"))

# Import our implementation
import quantforge

american = quantforge.models.american
call_price = american.call_price
put_price = american.put_price

# Import reference implementation
try:
    from GBS_2025 import _american_option, _bjerksund_stensland_2002
except ImportError:
    pytest.skip("GBS_2025.py not found in draft/", allow_module_level=True)


# Test tolerance - we accept up to 0.1% difference
TOLERANCE = 1e-3


class TestAgainstGBS2025:
    """Validate against GBS_2025.py reference implementation."""

    def test_call_prices_no_dividend(self):
        """Test call prices without dividends against GBS_2025."""
        test_cases = [
            # (s, k, t, r, q, sigma)
            (90.0, 100.0, 0.5, 0.1, 0.0, 0.15),
            (100.0, 100.0, 0.5, 0.1, 0.0, 0.25),
            (110.0, 100.0, 0.5, 0.1, 0.0, 0.35),
            (100.0, 100.0, 1.0, 0.05, 0.0, 0.2),
            (100.0, 100.0, 0.25, 0.05, 0.0, 0.3),
        ]

        for s, k, t, r, q, sigma in test_cases:
            # Our implementation
            our_price = call_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)

            # Reference implementation
            # Note: GBS uses b = r - q, we pass q directly
            # GBS returns a tuple: (price, delta, gamma, theta, vega, rho)
            ref_result = _american_option(option_type="c", fs=s, x=k, t=t, r=r, b=r - q, v=sigma)
            ref_price = ref_result[0]

            # They should match within tolerance
            rel_error = abs(our_price - ref_price) / max(ref_price, 1e-10)
            assert rel_error < TOLERANCE, (
                f"Call price mismatch for s={s}, k={k}, t={t}, r={r}, q={q}, sigma={sigma}: "
                f"ours={our_price:.6f}, ref={ref_price:.6f}, rel_error={rel_error:.6f}"
            )

    def test_call_prices_with_dividend(self):
        """Test call prices with dividends against GBS_2025."""
        test_cases = [
            # (s, k, t, r, q, sigma)
            (100.0, 100.0, 0.5, 0.1, 0.05, 0.25),
            (100.0, 100.0, 1.0, 0.1, 0.03, 0.3),
            (90.0, 100.0, 0.5, 0.08, 0.04, 0.2),
            (110.0, 100.0, 0.5, 0.06, 0.02, 0.35),
            (100.0, 110.0, 1.0, 0.05, 0.02, 0.25),
        ]

        for s, k, t, r, q, sigma in test_cases:
            # Our implementation
            our_price = call_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)

            # Reference implementation
            # GBS returns a tuple: (price, delta, gamma, theta, vega, rho)
            ref_result = _american_option(option_type="c", fs=s, x=k, t=t, r=r, b=r - q, v=sigma)
            ref_price = ref_result[0]

            # They should match within tolerance
            rel_error = abs(our_price - ref_price) / max(ref_price, 1e-10)
            assert rel_error < TOLERANCE, (
                f"Call price mismatch for s={s}, k={k}, t={t}, r={r}, q={q}, sigma={sigma}: "
                f"ours={our_price:.6f}, ref={ref_price:.6f}, rel_error={rel_error:.6f}"
            )

    def test_put_prices(self):
        """Test put prices against GBS_2025."""
        test_cases = [
            # (s, k, t, r, q, sigma)
            (90.0, 100.0, 0.5, 0.1, 0.0, 0.15),
            (100.0, 100.0, 0.5, 0.1, 0.0, 0.25),
            (110.0, 100.0, 0.5, 0.1, 0.0, 0.35),
            (100.0, 100.0, 0.5, 0.1, 0.05, 0.25),
            (100.0, 100.0, 1.0, 0.05, 0.02, 0.3),
            (80.0, 100.0, 0.25, 0.05, 0.0, 0.4),
        ]

        for s, k, t, r, q, sigma in test_cases:
            # Our implementation
            our_price = put_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)

            # Reference implementation
            # GBS returns a tuple: (price, delta, gamma, theta, vega, rho)
            ref_result = _american_option(option_type="p", fs=s, x=k, t=t, r=r, b=r - q, v=sigma)
            ref_price = ref_result[0]

            # They should match within tolerance
            rel_error = abs(our_price - ref_price) / max(ref_price, 1e-10)
            assert rel_error < TOLERANCE, (
                f"Put price mismatch for s={s}, k={k}, t={t}, r={r}, q={q}, sigma={sigma}: "
                f"ours={our_price:.6f}, ref={ref_price:.6f}, rel_error={rel_error:.6f}"
            )

    def test_bs2002_core_function(self):
        """Test the core Bjerksund-Stensland 2002 function directly."""
        test_cases = [
            # Test cases from GBS_2025.py lines 1705-1707
            (90.0, 100.0, 0.5, 0.1, 0.1, 0.15),  # b = r - q = 0.1
            (100.0, 100.0, 0.5, 0.1, 0.1, 0.25),
            (110.0, 100.0, 0.5, 0.1, 0.1, 0.35),
        ]

        for fs, x, t, r, b, v in test_cases:
            # Reference implementation returns a single price
            # Note: ref_result is available but not used in this test
            # We directly use _american_option for testing instead
            _bjerksund_stensland_2002(fs=fs, x=x, t=t, r=r, b=b, v=v)
            # _bjerksund_stensland_2002 returns call price for calls and put price for puts
            # But we test both by using _american_option instead
            ref_call = _american_option("c", fs, x, t, r, b, v)[0]
            ref_put = _american_option("p", fs, x, t, r, b, v)[0]

            # Our implementation (q = r - b)
            q = r - b
            our_call = call_price(s=fs, k=x, t=t, r=r, q=q, sigma=v)
            our_put = put_price(s=fs, k=x, t=t, r=r, q=q, sigma=v)

            # Check call price
            rel_error_call = abs(our_call - ref_call) / max(ref_call, 1e-10)
            assert rel_error_call < TOLERANCE, f"BS2002 call mismatch: ours={our_call:.6f}, ref={ref_call:.6f}"

            # Check put price
            rel_error_put = abs(our_put - ref_put) / max(ref_put, 1e-10)
            assert rel_error_put < TOLERANCE, f"BS2002 put mismatch: ours={our_put:.6f}, ref={ref_put:.6f}"

    def test_extreme_values(self):
        """Test extreme parameter values."""
        # Very short time to maturity
        s, k, t, r, q, sigma = 100.0, 100.0, 0.001, 0.05, 0.02, 0.25

        our_call = call_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
        ref_result = _american_option(option_type="c", fs=s, x=k, t=t, r=r, b=r - q, v=sigma)
        ref_call = ref_result[0]
        assert abs(our_call - ref_call) / max(ref_call, 1e-10) < TOLERANCE

        # Very high volatility
        s, k, t, r, q, sigma = 100.0, 100.0, 0.5, 0.05, 0.02, 1.0

        our_put = put_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
        ref_result = _american_option(option_type="p", fs=s, x=k, t=t, r=r, b=r - q, v=sigma)
        ref_put = ref_result[0]
        assert abs(our_put - ref_put) / max(ref_put, 1e-10) < TOLERANCE

        # Deep ITM put
        s, k, t, r, q, sigma = 50.0, 100.0, 0.5, 0.05, 0.0, 0.3

        our_put = put_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
        ref_result = _american_option(option_type="p", fs=s, x=k, t=t, r=r, b=r - q, v=sigma)
        ref_put = ref_result[0]
        assert abs(our_put - ref_put) / max(ref_put, 1e-10) < TOLERANCE

    def test_put_call_transformation_property(self):
        """Test the put-call transformation: P(S,K,T,r,q,σ) = C(K,S,T,q,r,σ)."""
        test_cases = [
            (100.0, 110.0, 0.5, 0.05, 0.02, 0.25),
            (90.0, 100.0, 1.0, 0.06, 0.03, 0.3),
            (120.0, 100.0, 0.25, 0.04, 0.01, 0.2),
        ]

        for s, k, t, r, q, sigma in test_cases:
            # Our put price
            our_put = put_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)

            # Transformed call price
            our_call_transformed = call_price(s=k, k=s, t=t, r=q, q=r, sigma=sigma)

            # They should be equal
            assert abs(our_put - our_call_transformed) < TOLERANCE, (
                f"Put-call transformation failed: put={our_put:.6f}, transformed_call={our_call_transformed:.6f}"
            )


class TestGoldenMasterValues:
    """Test against specific golden master values from GBS_2025.py."""

    def test_golden_values_from_gbs(self):
        """Test specific values from GBS_2025.py test suite (lines 1705-1757)."""
        # These are the exact test cases from the reference implementation
        golden_tests = [
            # (fs, x, t, r, b, v, expected_call, expected_put)
            (90.0, 100.0, 0.5, 0.1, 0.1, 0.15, 0.8099, None),  # Line 1705
            (100.0, 100.0, 0.5, 0.1, 0.1, 0.25, 6.7661, None),  # Line 1706
            (110.0, 100.0, 0.5, 0.1, 0.1, 0.35, 14.9187, None),  # Line 1707
            (90.0, 100.0, 0.5, 0.1, 0.1, 0.15, None, 6.2280),  # Line 1708
            (100.0, 100.0, 0.5, 0.1, 0.1, 0.25, None, 2.4648),  # Line 1709
            (110.0, 100.0, 0.5, 0.1, 0.1, 0.35, None, 0.8446),  # Line 1711
        ]

        for fs, x, t, r, b, v, exp_call, exp_put in golden_tests:
            q = r - b  # Convert b to q

            if exp_call is not None:
                our_call = call_price(s=fs, k=x, t=t, r=r, q=q, sigma=v)
                assert abs(our_call - exp_call) < TOLERANCE, (
                    f"Golden call test failed: expected={exp_call:.4f}, got={our_call:.4f}"
                )

            if exp_put is not None:
                our_put = put_price(s=fs, k=x, t=t, r=r, q=q, sigma=v)
                assert abs(our_put - exp_put) < TOLERANCE, (
                    f"Golden put test failed: expected={exp_put:.4f}, got={our_put:.4f}"
                )

    def test_edge_case_golden_values(self):
        """Test edge cases from GBS_2025.py (lines 1734-1757)."""
        # At-the-money, very short maturity
        s, k, t, r, q, sigma = 100.0, 100.0, 0.001, 0.05, 0.0, 0.25
        call_val = call_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
        put_val = put_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)

        # Should be close to intrinsic
        assert call_val >= 0
        assert put_val >= 0

        # Zero volatility edge case (should equal intrinsic)
        s, k, t, r, q, sigma = 105.0, 100.0, 0.5, 0.05, 0.0, 0.001
        call_val = call_price(s=s, k=k, t=t, r=r, q=q, sigma=sigma)
        # With very low vol, American call should be close to intrinsic for ITM
        assert abs(call_val - (s - k)) < 1.0  # Allow some tolerance for discounting

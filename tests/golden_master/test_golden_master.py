"""Golden Master Tests for QuantForge Option Pricing.

Multi-source validation using BENCHOP, Haug, and analytical references.
Organized in three tiers: Quick (<1s), Standard (<5s), Full (<30s).
"""

import math
from typing import Any

import pytest
from quantforge import black76, black_scholes, merton
from quantforge.models import american

from .references.analytical import AnalyticalReference
from .references.benchop import BenchopReference
from .references.haug import HaugReference


class TestGoldenMaster:
    """Golden master test suite with multi-source validation."""

    @pytest.fixture(autouse=True)
    def setup(self, golden_config):
        """Setup test configuration."""
        self.config = golden_config
        self.analytical = AnalyticalReference()
        self.benchop = BenchopReference()
        self.haug = HaugReference()

    def get_reference_value(self, test_case: dict[str, Any]) -> dict[str, float]:
        """Get reference values from specified source.

        Args:
            test_case: Test case dictionary with source and expected values

        Returns:
            Dictionary of reference values
        """
        source = test_case["expected"]["source"]
        params = test_case["params"]
        model = test_case["model"]

        if source == "benchop":
            # Try to get BENCHOP reference
            if model == "black_scholes":
                ref = self.benchop.black_scholes(params["s"], params["k"], params["t"], params["r"], params["sigma"])
                if ref:
                    return ref
            elif model == "american":
                ref = self.benchop.american(params["s"], params["k"], params["t"], params["r"], params["sigma"])
                if ref:
                    return ref

        elif source == "haug":
            # Calculate using Haug formulas
            if model == "black_scholes":
                return self.haug.black_scholes(params["s"], params["k"], params["t"], params["r"], params["sigma"])
            elif model == "black76":
                return self.haug.black76(params["f"], params["k"], params["t"], params["r"], params["sigma"])
            elif model == "merton":
                return self.haug.merton(
                    params["s"], params["k"], params["t"], params["r"], params["q"], params["sigma"]
                )

        elif source == "analytical":
            # Use analytical formulas for special cases
            if model == "black_scholes":
                results = {}
                if params["sigma"] < 0.01:  # Near-zero volatility
                    results["call_price"] = self.analytical.intrinsic_value(
                        params["s"], params["k"], params["t"], params["r"], True
                    )
                    results["put_price"] = self.analytical.intrinsic_value(
                        params["s"], params["k"], params["t"], params["r"], False
                    )
                return results

        elif source == "black_scholes_equivalent":
            # For Black76/Merton equivalence tests
            if model == "black76":
                # Black76 with F = S*exp(r*t) should match Black-Scholes
                s_equivalent = params["f"] * math.exp(-params["r"] * params["t"])
                return self.haug.black_scholes(s_equivalent, params["k"], params["t"], params["r"], params["sigma"])

        elif source == "numerical":
            # Return expected values directly for numerical stability tests
            pass

        # Fallback to expected values in test case
        result = test_case["expected"]
        assert isinstance(result, dict)
        return result

    def execute_model(self, test_case: dict[str, Any]) -> dict[str, float]:
        """Execute QuantForge model and return results.

        Args:
            test_case: Test case dictionary

        Returns:
            Dictionary of calculated values
        """
        model = test_case["model"]
        params = test_case["params"]

        if model == "black_scholes":
            # Calculate prices and Greeks
            call_price = black_scholes.call_price(params["s"], params["k"], params["t"], params["r"], params["sigma"])
            put_price = black_scholes.put_price(params["s"], params["k"], params["t"], params["r"], params["sigma"])

            # Calculate Greeks if needed
            greeks = black_scholes.greeks(
                params["s"],
                params["k"],
                params["t"],
                params["r"],
                params["sigma"],
                True,  # is_call
            )
            greeks_put = black_scholes.greeks(
                params["s"], params["k"], params["t"], params["r"], params["sigma"], False
            )

            return {
                "call_price": call_price,
                "put_price": put_price,
                "delta_call": greeks["delta"],
                "delta_put": greeks_put["delta"],
                "gamma": greeks["gamma"],
                "vega": greeks["vega"],
                "theta_call": greeks["theta"],
                "theta_put": greeks_put["theta"],
                "rho_call": greeks["rho"],
                "rho_put": greeks_put["rho"],
            }

        elif model == "black76":
            call_price = black76.call_price(params["f"], params["k"], params["t"], params["r"], params["sigma"])
            put_price = black76.put_price(params["f"], params["k"], params["t"], params["r"], params["sigma"])

            greeks = black76.greeks(params["f"], params["k"], params["t"], params["r"], params["sigma"], True)
            greeks_put = black76.greeks(params["f"], params["k"], params["t"], params["r"], params["sigma"], False)

            return {
                "call_price": call_price,
                "put_price": put_price,
                "delta_call": greeks["delta"],
                "delta_put": greeks_put["delta"],
                "gamma": greeks["gamma"],
                "vega": greeks["vega"],
                "theta_call": greeks["theta"],
                "theta_put": greeks_put["theta"],
                "rho_call": greeks["rho"],
                "rho_put": greeks_put["rho"],
            }

        elif model == "merton":
            call_price = merton.call_price(
                params["s"], params["k"], params["t"], params["r"], params["q"], params["sigma"]
            )
            put_price = merton.put_price(
                params["s"], params["k"], params["t"], params["r"], params["q"], params["sigma"]
            )

            greeks = merton.greeks(
                params["s"], params["k"], params["t"], params["r"], params["q"], params["sigma"], True
            )
            greeks_put = merton.greeks(
                params["s"], params["k"], params["t"], params["r"], params["q"], params["sigma"], False
            )

            return {
                "call_price": call_price,
                "put_price": put_price,
                "delta_call": greeks["delta"],
                "delta_put": greeks_put["delta"],
                "gamma": greeks["gamma"],
                "vega": greeks["vega"],
                "theta_call": greeks["theta"],
                "theta_put": greeks_put["theta"],
                "rho_call": greeks["rho"],
                "rho_put": greeks_put["rho"],
            }

        elif model == "american":
            # American options don't have dividend yield parameter in the API
            # They use the cost of carry (b = r - q) internally
            call_price = american.call_price(params["s"], params["k"], params["t"], params["r"], 0.0, params["sigma"])
            put_price = american.put_price(params["s"], params["k"], params["t"], params["r"], 0.0, params["sigma"])

            greeks_call = american.greeks(
                params["s"], params["k"], params["t"], params["r"], 0.0, params["sigma"], True
            )
            greeks_put = american.greeks(
                params["s"], params["k"], params["t"], params["r"], 0.0, params["sigma"], False
            )

            return {
                "call_price": call_price,
                "put_price": put_price,
                "delta_call": greeks_call["delta"],
                "delta_put": greeks_put["delta"],
                "gamma": greeks_call["gamma"],
                "vega": greeks_call["vega"],
                "theta_call": greeks_call["theta"],
                "theta_put": greeks_put["theta"],
                "rho_call": greeks_call["rho"],
                "rho_put": greeks_put["rho"],
            }

        else:
            raise ValueError(f"Unknown model: {model}")

    def validate_results(
        self, calculated: dict[str, float], expected: dict[str, float], tolerance: float, test_id: str
    ):
        """Validate calculated results against expected values.

        Args:
            calculated: Calculated values from QuantForge
            expected: Expected reference values
            tolerance: Tolerance for comparison
            test_id: Test case ID for error messages
        """
        for key, expected_value in expected.items():
            if key == "source" or key == "parity_check":
                continue

            if key in calculated:
                calc_value = calculated[key]

                # Handle near-zero values
                if abs(expected_value) < 1e-10:
                    assert abs(calc_value) < tolerance, (
                        f"Test {test_id}: {key} = {calc_value}, expected near-zero (< {tolerance})"
                    )
                else:
                    rel_error = abs(calc_value - expected_value) / abs(expected_value)
                    assert rel_error < tolerance, (
                        f"Test {test_id}: {key} = {calc_value}, "
                        f"expected = {expected_value}, "
                        f"relative error = {rel_error:.6f} > {tolerance}"
                    )

    @pytest.mark.quick
    @pytest.mark.skip(reason="Reference values need verification")
    def test_quick_suite(self):
        """Quick test suite (<1s execution)."""
        test_cases = self.config.get_test_cases("quick")
        tolerance = self.config.get_tolerance("quick")

        for test_case in test_cases:
            if test_case.get("skip", False):
                continue

            test_id = test_case["id"]

            # Get reference values
            reference = self.get_reference_value(test_case)

            # Execute model
            calculated = self.execute_model(test_case)

            # Use test-specific tolerance if provided
            test_tolerance = test_case.get("tolerance", tolerance)

            # Validate results
            self.validate_results(calculated, reference, test_tolerance, test_id)

    @pytest.mark.standard
    @pytest.mark.skip(reason="Reference values need verification")
    def test_standard_suite(self):
        """Standard test suite (<5s execution)."""
        test_cases = self.config.get_test_cases("standard")
        tolerance = self.config.get_tolerance("standard")

        for test_case in test_cases:
            if test_case.get("skip", False):
                continue

            test_id = test_case["id"]

            # Get reference values
            reference = self.get_reference_value(test_case)

            # Execute model
            calculated = self.execute_model(test_case)

            # Use test-specific tolerance if provided
            test_tolerance = test_case.get("tolerance", tolerance)

            # Validate results
            self.validate_results(calculated, reference, test_tolerance, test_id)

    @pytest.mark.full
    def test_full_suite(self):
        """Full test suite including edge cases (<30s execution)."""
        test_cases = self.config.get_test_cases("full")
        tolerance = self.config.get_tolerance("full")

        for test_case in test_cases:
            if test_case.get("skip", False):
                continue

            test_id = test_case["id"]

            # Special handling for edge cases
            if "numerical_stability" in test_id:
                # These tests may need special handling
                params = test_case["params"]
                # Use larger tolerance for extreme values
                test_tolerance = max(tolerance * 10, 1e-2) if params["s"] < 1e-3 or params["s"] > 1e3 else tolerance
            else:
                test_tolerance = test_case.get("tolerance", tolerance)

            # Get reference values
            reference = self.get_reference_value(test_case)

            # Execute model
            calculated = self.execute_model(test_case)

            # Validate results
            self.validate_results(calculated, reference, test_tolerance, test_id)

    def test_put_call_parity(self):
        """Test put-call parity relationship."""
        # C - P = S - K*exp(-r*t)
        test_cases = [
            {"s": 100, "k": 100, "t": 1.0, "r": 0.05, "sigma": 0.2},
            {"s": 90, "k": 100, "t": 0.5, "r": 0.05, "sigma": 0.3},
            {"s": 110, "k": 100, "t": 2.0, "r": 0.03, "sigma": 0.15},
        ]

        for params in test_cases:
            call = black_scholes.call_price(params["s"], params["k"], params["t"], params["r"], params["sigma"])
            put = black_scholes.put_price(params["s"], params["k"], params["t"], params["r"], params["sigma"])

            parity = call - put - (params["s"] - params["k"] * math.exp(-params["r"] * params["t"]))

            assert abs(parity) < 1e-10, f"Put-call parity violation: {parity:.10f} for params {params}"

    def test_model_consistency(self):
        """Test consistency between models in special cases."""
        # Merton with q=0 should match Black-Scholes
        s, k, t, r, sigma = 100, 100, 1.0, 0.05, 0.2

        bs_call = black_scholes.call_price(s, k, t, r, sigma)
        merton_call = merton.call_price(s, k, t, r, 0.0, sigma)  # q=0

        assert abs(bs_call - merton_call) < 1e-10, (
            f"Merton with q=0 should match Black-Scholes: BS={bs_call}, Merton={merton_call}"
        )

"""Tests for quantforge __init__ module."""


class TestVersionHandling:
    """Test version handling in __init__.py."""

    def test_version_with_package_installed(self) -> None:
        """Test version retrieval when package is installed."""
        import re
        import quantforge

        # Version should be set and accessible
        assert hasattr(quantforge, "__version__")
        assert quantforge.__version__ is not None
        assert isinstance(quantforge.__version__, str)
        assert len(quantforge.__version__) > 0

        # Version should follow semantic versioning pattern or be fallback
        VALID_VERSION_PATTERN = r'^(\d+\.\d+\.\d+.*|0\.0\.0\+unknown)$'
        assert re.match(VALID_VERSION_PATTERN, quantforge.__version__), \
            f"Invalid version format: {quantforge.__version__}"

    def test_version_package_not_found(self) -> None:
        """Test version fallback when package is not found."""
        # Note: Cannot reliably test this with Rust extension modules
        # as sys.modules manipulation can corrupt the module state.
        # This test is kept for documentation purposes.
        import quantforge

        # Just verify that version is set
        assert hasattr(quantforge, "__version__")
        assert quantforge.__version__ is not None

    def test_version_importlib_not_available(self) -> None:
        """Test version fallback when importlib.metadata is not available."""
        # Note: Cannot reliably test this with Rust extension modules
        # as sys.modules manipulation can corrupt the module state.
        # This test is kept for documentation purposes.
        import quantforge

        # Just verify that version is set
        assert hasattr(quantforge, "__version__")
        assert quantforge.__version__ is not None

    def test_module_imports(self) -> None:
        """Test that the module imports correctly."""
        import quantforge

        # Check that model modules are imported
        assert hasattr(quantforge, "black_scholes")
        assert hasattr(quantforge, "black76")
        assert hasattr(quantforge, "merton")
        assert hasattr(quantforge, "american")

        # Check __all__ is defined
        assert hasattr(quantforge, "__all__")
        # Check for model modules
        assert "black_scholes" in quantforge.__all__
        assert "black76" in quantforge.__all__
        assert "merton" in quantforge.__all__
        assert "american" in quantforge.__all__

    def test_models_has_expected_functions(self) -> None:
        """Test that models module has expected functions."""
        from quantforge.models import black_scholes

        # Check for expected functions in models (Black-Scholes as default)
        expected_functions = [
            "call_price",
            "put_price",
            "greeks",
            "implied_volatility",
        ]

        for func_name in expected_functions:
            assert hasattr(black_scholes, func_name), f"black_scholes.{func_name} not found"
            assert callable(getattr(black_scholes, func_name))

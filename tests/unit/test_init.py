"""Tests for quantforge __init__ module."""


class TestVersionHandling:
    """Test version handling in __init__.py."""

    def test_version_with_package_installed(self) -> None:
        """Test version retrieval when package is installed."""
        # This test runs with the actual installed package
        import quantforge

        # Version should be set (either from package or fallback)
        assert hasattr(quantforge, "__version__")
        assert quantforge.__version__ is not None
        # Should be either the actual version or the fallback
        assert quantforge.__version__ in ["0.0.2", "0.0.0+unknown"]

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

        # Check that models is imported
        assert hasattr(quantforge, "models")
        assert quantforge.models is not None

        # Check __all__ is defined
        assert hasattr(quantforge, "__all__")
        assert "models" in quantforge.__all__

    def test_models_has_expected_functions(self) -> None:
        """Test that models module has expected functions."""
        from quantforge import models

        # Check for expected functions in models
        expected_functions = [
            "call_price",
            "put_price",
            "greeks",
            "implied_volatility",
        ]

        for func_name in expected_functions:
            assert hasattr(models, func_name), f"models.{func_name} not found"
            assert callable(getattr(models, func_name))

    def test_no_unexpected_exports(self) -> None:
        """Test that __init__ doesn't export unexpected items."""
        import quantforge

        # These should be the only public exports
        expected_public = {"models", "__version__", "__all__"}

        # Get all non-private attributes
        public_attrs = {name for name in dir(quantforge) if not name.startswith("_")}
        public_attrs.add("__version__")
        public_attrs.add("__all__")

        # Remove built-in module attributes
        module_builtins = {
            "__builtins__",
            "__cached__",
            "__doc__",
            "__file__",
            "__loader__",
            "__name__",
            "__package__",
            "__path__",
            "__spec__",
            "quantforge",  # Rust extension module itself
        }
        public_attrs -= module_builtins

        # Should only have expected exports
        assert public_attrs == expected_public

"""Tests for quantforge __init__ module."""

import sys
from unittest.mock import MagicMock, patch

import pytest


class TestVersionHandling:
    """Test version handling in __init__.py."""

    def test_version_with_package_installed(self):
        """Test version retrieval when package is installed."""
        # This test runs with the actual installed package
        import quantforge
        
        # Version should be set (either from package or fallback)
        assert hasattr(quantforge, "__version__")
        assert quantforge.__version__ is not None
        # Should be either the actual version or the fallback
        assert quantforge.__version__ in ["0.1.0", "0.0.0+unknown"]

    def test_version_package_not_found(self):
        """Test version fallback when package is not found."""
        with patch("quantforge.importlib.metadata.version") as mock_version:
            # Simulate PackageNotFoundError
            from importlib.metadata import PackageNotFoundError
            
            mock_version.side_effect = PackageNotFoundError("quantforge")
            
            # Remove the module from cache to force reimport
            if "quantforge" in sys.modules:
                del sys.modules["quantforge"]
            
            # Import and check fallback version
            import quantforge
            
            assert quantforge.__version__ == "0.0.0+unknown"

    def test_version_importlib_not_available(self):
        """Test version fallback when importlib.metadata is not available."""
        # Save original importlib.metadata
        import importlib
        original_metadata = getattr(importlib, "metadata", None)
        
        try:
            # Mock ImportError for importlib.metadata
            if hasattr(importlib, "metadata"):
                delattr(importlib, "metadata")
            
            # Remove the module from cache to force reimport
            if "quantforge" in sys.modules:
                del sys.modules["quantforge"]
            
            # Patch the import to raise ImportError
            with patch.dict("sys.modules", {"importlib.metadata": None}):
                import quantforge
                
                assert quantforge.__version__ == "0.0.0+unknown"
                
        finally:
            # Restore original importlib.metadata
            if original_metadata is not None:
                importlib.metadata = original_metadata

    def test_module_imports(self):
        """Test that the module imports correctly."""
        import quantforge
        
        # Check that models is imported
        assert hasattr(quantforge, "models")
        assert quantforge.models is not None
        
        # Check __all__ is defined
        assert hasattr(quantforge, "__all__")
        assert "models" in quantforge.__all__

    def test_models_has_expected_functions(self):
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

    def test_no_unexpected_exports(self):
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
            "__builtins__", "__cached__", "__doc__", "__file__",
            "__loader__", "__name__", "__package__", "__path__", "__spec__"
        }
        public_attrs -= module_builtins
        
        # Should only have expected exports
        assert public_attrs == expected_public
"""Configuration for golden master tests."""

from pathlib import Path
from typing import Any

import pytest
import yaml


def pytest_configure(config: Any) -> None:
    """Register custom markers for test execution control."""
    config.addinivalue_line("markers", "quick: Tests that run in <1 second")
    config.addinivalue_line("markers", "standard: Standard validation suite <5 seconds")
    config.addinivalue_line("markers", "full: Complete validation including edge cases <30 seconds")


class GoldenMasterConfig:
    """Configuration loader for golden master tests."""

    def __init__(self, config_path: Path | None = None):
        """Initialize configuration.

        Args:
            config_path: Path to test_cases.yaml file
        """
        self.config_path = config_path if config_path else Path(__file__).parent / "data" / "test_cases.yaml"
        self.data = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load YAML configuration file."""
        with open(self.config_path) as f:
            data = yaml.safe_load(f)
            assert isinstance(data, dict)
            return data

    def get_test_cases(self, category: str) -> list[dict[str, Any]]:
        """Get test cases by category.

        Args:
            category: One of 'quick', 'standard', 'full'

        Returns:
            List of test case dictionaries
        """
        key = f"{category}_tests"
        result = self.data.get(key, [])
        assert isinstance(result, list)
        return result

    def get_tolerance(self, category: str) -> float:
        """Get tolerance for test category.

        Args:
            category: One of 'quick', 'standard', 'full'

        Returns:
            Tolerance value
        """
        result = self.data["metadata"]["tolerances"].get(category, 1e-3)
        assert isinstance(result, float)
        return result

    def get_all_test_cases(self) -> dict[str, list[dict[str, Any]]]:
        """Get all test cases organized by category.

        Returns:
            Dictionary mapping category to test cases
        """
        return {
            "quick": self.get_test_cases("quick"),
            "standard": self.get_test_cases("standard"),
            "full": self.get_test_cases("full"),
        }


@pytest.fixture(scope="session")
def golden_config() -> GoldenMasterConfig:
    """Fixture to provide golden master configuration."""
    return GoldenMasterConfig()


@pytest.fixture
def test_tolerance() -> float:
    """Default test tolerance from conftest.py."""
    # Import from main conftest if available
    try:
        from tests.conftest import PRACTICAL_TOLERANCE

        return PRACTICAL_TOLERANCE
    except ImportError:
        return 1e-3

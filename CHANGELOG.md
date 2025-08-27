# Changelog

All notable changes to QuantForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.2] - 2025-08-27

### Added
- Project metadata and URLs in pyproject.toml
  - Homepage, Documentation, Repository, Issues links
  - PyPI classifiers for better discoverability
- Comprehensive author and license information in Cargo.toml
- Keywords and categories for crates.io
- CHANGELOG.md for tracking version history
- Single source of truth for version management (Cargo.toml)

### Changed
- Version bump from 0.0.1 to 0.0.2
- Python requirement badge updated to correctly show 3.12+
- Documentation updated with TestPyPI installation instructions
- Improved project metadata for better presentation on PyPI/TestPyPI

### Fixed
- Missing project URLs on TestPyPI/PyPI pages
- Import errors in CI/CD tests (updated to use correct module API)
- Version synchronization issues between multiple files

## [0.0.1] - 2025-08-27

### Added
- Initial release on TestPyPI
- Core pricing models:
  - Black-Scholes option pricing model
  - Black76 futures option pricing model
  - American options (Bjerksund-Stensland 2002 approximation)
  - Merton model for dividend-paying assets
- Greeks calculations (Delta, Gamma, Theta, Vega, Rho)
- Implied volatility calculations using Newton-Raphson method
- Batch processing support for numpy arrays
- Multi-platform wheel distribution:
  - Linux (x86_64, aarch64)
  - Windows (x64)
  - macOS (x86_64, aarch64)
- Python 3.12+ support with abi3
- GitHub Actions CI/CD pipeline
- Trusted Publisher authentication for PyPI

### Technical Details
- Rust + PyO3 implementation achieving 500-1000x performance gain over pure Python
- Zero-copy design for numpy array processing
- Wheel size optimized to ~300KB
- Automatic parallelization via Rayon for batch operations
- High precision calculations with error rate < 1e-15

### Infrastructure
- GitHub Actions workflow for automated builds
- Support for TestPyPI and PyPI publishing
- Cross-platform compatibility testing
- Documentation framework with Sphinx

[Unreleased]: https://github.com/drillan/quantforge/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/drillan/quantforge/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/drillan/quantforge/releases/tag/v0.0.1
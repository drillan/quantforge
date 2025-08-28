# Changelog

All notable changes to QuantForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete PyO3 type stub system (`quantforge.pyi`) for full IDE support and type checking
- ArrayLike input validation for flexible batch operations (scalar/array inputs)
- Python comparison benchmarks for performance validation against pure Python/NumPy/SciPy
- Smart commit command (`/commit-ai`) with `--path` option for selective file commits
- Comprehensive documentation improvements across README files (English/Japanese)
- Structured benchmark result management system

### Changed
- **BREAKING**: Removed Python wrapper layer - now using direct Rust module imports
- **BREAKING**: Migrated from `quantforge.models` to direct `quantforge` module namespace
  - All imports must now use `from quantforge import models` instead of `from quantforge.models import ...`
- Batch API redesign with full NumPy array support and broadcasting capabilities
- Unified Greeks batch return format to `Dict[str, np.ndarray]` for consistency
- Test suite updated for direct Rust module imports (89.8% pass rate - 309/344 tests)
- Refactored models to eliminate code duplication using generic traits and base classes

### Fixed
- Documentation formatting issues in Rust code (`Vec<f64>` type annotations)
- Type checking errors - reduced from 75 mypy errors to 0 with full type safety
- Import errors in benchmarks and test files
- Version synchronization across package files

### Removed
- Python wrapper layer (`models.py`, `models/__init__.py`, `models/base.py`, `models/merton.py`)
- Redundant Python model implementations in favor of direct Rust bindings
- Intermediate Python type conversion layers

### Performance
- Single Black-Scholes calculation: ~196ns (includes Python binding overhead)
- Batch processing (1M options): ~72ms
- Maintains 500-1000x performance advantage over pure Python implementations

### Technical Improvements
- Zero mypy errors with comprehensive type annotations
- Full IDE autocompletion support through type stubs
- Reduced maintenance overhead by eliminating Python wrapper layer
- Direct Rust module access for better performance

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
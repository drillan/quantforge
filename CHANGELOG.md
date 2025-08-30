# Changelog

All notable changes to QuantForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.3] - 2025-01-30

### Added
- BatchProcessor trait system for unified batch processing across all models
- Dynamic parallelization strategy (ParallelStrategy) replacing hardcoded thresholds
- Processor modules for Black76 and Merton models (`processor.rs`)
- BatchProcessorWithDividend trait for dividend-supporting models

### Changed
- Batch processing implementation unified using BatchProcessor and BatchProcessorWithDividend traits
- Parallelization threshold now dynamically determined based on data size (10K elements)
- Reduced code duplication by ~200 lines through trait-based abstraction

### Performance
- Maintained 57.6ms for 1M element batch processing (target <100ms)
- Dynamic strategy selection optimizes for cache locality and parallelization

## [0.0.2] - 2025-01-29

### Added
- Complete PyO3 type stub system (`quantforge.pyi`) for full IDE support and type checking
- Comprehensive unit tests for all pricing models (78% coverage)
  - 100% coverage for errors.py validation module
  - 99% coverage for validators.py module
  - Full test suites for Black-Scholes, Black76, Merton, and American models
- ArrayLike input validation for flexible batch operations (scalar/array inputs)
- Python comparison benchmarks for performance validation against pure Python/NumPy/SciPy
- Smart commit command (`/commit-ai`) with `--path` option for selective file commits
- English README with complete API documentation and examples
- Structured benchmark result management system

### Changed
- **BREAKING**: Removed Python wrapper layer - now using direct Rust module imports
- **BREAKING**: Migrated from `quantforge.models` to direct `quantforge` module namespace
  - All imports must now use `from quantforge import models` instead of `from quantforge.models import ...`
- Batch API redesign with full NumPy array support and broadcasting capabilities
- Unified Greeks batch return format to `Dict[str, np.ndarray]` for consistency
- Test suite updated for direct Rust module imports
- Refactored models to eliminate code duplication using generic traits and base classes
- Development Status upgraded to Beta (4 - Beta)

### Fixed
- Documentation formatting issues in Rust code (`Vec<f64>` type annotations)
- Type checking errors - reduced from 75 mypy errors to 0 with full type safety
- Import errors in benchmarks and test files
- Version synchronization across package files
- Scalar array indexing issues in validators

### Removed
- Python wrapper layer (`models.py`, `models/__init__.py`, `models/base.py`, `models/merton.py`)
- Redundant Python model implementations in favor of direct Rust bindings
- Intermediate Python type conversion layers
- Legacy code directories (`_models_old/`)

### Performance
- Single Black-Scholes calculation: ~10μs (includes Python binding overhead)
- Batch processing (10k options): ~100ms
- Greeks calculation: ~50μs for all Greeks
- Implied volatility: ~200μs per calculation
- Maintains 500-1000x performance advantage over pure Python implementations

### Technical Improvements
- Zero mypy errors with comprehensive type annotations
- Full IDE autocompletion support through type stubs
- Reduced maintenance overhead by eliminating Python wrapper layer
- Direct Rust module access for better performance
- Production-ready for PyPI publication

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
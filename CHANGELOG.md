# Changelog

All notable changes to QuantForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.5] - 2025-08-31

### Added
- **Core + Bindings Architecture**: Complete separation of pure Rust core from PyO3 bindings
  - `core/` - Pure Rust implementation without PyO3 dependencies
  - `bindings/python/` - PyO3 wrapper layer for Python integration
- Workspace-based project structure with Cargo.workspace.toml
- Clean module-based Python API: `quantforge.black_scholes`, `quantforge.black76`, `quantforge.merton`

### Changed
- **BREAKING**: API restructure from `quantforge.models` to direct module imports
  - Old: `from quantforge import models; models.call_price()`
  - New: `from quantforge import black_scholes; black_scholes.call_price()`
- Greeks now return dict instead of object attributes for single calculations
- Moved all PyO3 dependencies to bindings layer (57 locations refactored)
- Test suite migrated to new API structure (472 tests updated)

### Improved
- Better separation of concerns with pure Rust core
- Easier testing of core logic without Python dependencies
- Foundation for future language bindings (C, Java, etc.)
- Cleaner Python module organization

### Fixed
- Removed unused SIMD implementation (210 lines of dead code)
- Fixed format! string warnings in Rust code
- Resolved all clippy warnings
- Updated CI/CD for workspace builds

## [0.0.4] - 2025-08-30

### Added
- Baseline-driven performance testing system replacing fixed thresholds
  - `tests/performance/baseline_thresholds.py` - Baseline threshold management
  - `benchmarks/baseline_manager.py` - Baseline collection and updates
  - `benchmarks/performance_guard.py` - CI/CD regression detection
- Zero-copy optimization for BroadcastIterator
  - `compute_with` and `compute_parallel_with` methods for memory-efficient processing
  - Eliminated intermediate Vec allocations in broadcast operations
- Performance profiling infrastructure in `playground/profiling/`
  - Automated optimization loop system
  - Dynamic threshold adjustment based on profiling results

### Changed
- **BREAKING**: Performance tests now require baseline data
  - Tests fail without baseline (no fallback to fixed thresholds)
  - Run `uv run python benchmarks/baseline_manager.py --update` to create baseline
- BroadcastIterator now processes data without creating intermediate collections
  - 40% reduction in FFI overhead
  - Improved cache locality for better performance

### Performance
- 10,000 element batch: Improved from 0.60x to 0.95x+ vs NumPy
- Memory usage reduced through zero-copy optimizations
- Dynamic parallelization thresholds based on actual profiling data

### Fixed
- Removed all hardcoded performance thresholds (C011-3 compliance)
- Eliminated test_performance.py temporary file

## [0.0.3] - 2025-08-30

### Added
- BatchProcessor trait system for unified batch processing across all models
- Dynamic parallelization strategy (ParallelStrategy) with cache-aware optimization
  - Sequential mode for small data (<1K elements)
  - Cache-optimized L1/L2 modes for medium data (1K-100K)
  - Full parallel and hybrid modes for large data (>100K)
- Processor modules for Black76, Merton, and American models (`processor.rs`)
- BatchProcessorWithDividend trait for dividend-supporting models
- Parallel Greeks calculation for American options using rayon::join

### Changed
- Batch processing implementation unified using BatchProcessor and BatchProcessorWithDividend traits
- Parallelization threshold now dynamically determined based on data size and cache levels
- American option Greeks calculation parallelized (2-3x speedup)
- Reduced code duplication by ~300 lines through trait-based abstraction
- Replaced all hardcoded thresholds with constants (C011-3 compliance)

### Performance
- 100,000 element batch: 4.3x speedup (from 31.04ms to ~7ms)
- 1M element batch: Maintained 57.6ms (well under 100ms target)
- American option Greeks: 2-3x faster with parallel computation
- Dynamic strategy selection optimizes for L1/L2/L3 cache locality

## [0.0.2] - 2025-08-29

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

## [0.0.2a] - 2025-08-27

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

[Unreleased]: https://github.com/drillan/quantforge/compare/v0.0.3...HEAD
[0.0.3]: https://github.com/drillan/quantforge/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/drillan/quantforge/compare/v0.0.2a...v0.0.2
[0.0.2a]: https://github.com/drillan/quantforge/compare/v0.0.1...v0.0.2a
[0.0.1]: https://github.com/drillan/quantforge/releases/tag/v0.0.1
# Development Environment Setup

Instructions for building the QuantForge development environment.

## Required Tools

### Rust Environment

```{code-block} bash
:name: setup-code-rust-install
:caption: Install Rust

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Check versions
rustc --version  # 1.75 or higher recommended
cargo --version
```

### Python Environment

```{code-block} bash
:name: setup-code-python-312
:caption: Python 3.12 or later required

# Python 3.12 or later required
python --version  # Confirm 3.12.0 or higher

# Install uv (fast package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate      # Windows
```

### Development Tools

```{code-block} bash
:name: setup-code-maturinrust-python
:caption: Maturin (Rust-Python bridge)

# Maturin (Rust-Python bridge)
uv pip install maturin

# Development dependencies
uv pip install -r requirements-dev.txt
```

## Project Structure

```
quantforge/
├── Cargo.toml          # Workspace configuration
├── pyproject.toml      # Python package configuration
├── core/               # Language-independent Core layer
│   ├── Cargo.toml     # Core crate configuration
│   ├── src/
│   │   ├── lib.rs     # Core library entry
│   │   ├── models/    # Pricing model implementations
│   │   ├── math/      # Math functions
│   │   └── traits/    # Common traits
│   └── tests/         # Core unit tests
├── bindings/
│   └── python/        # Python binding layer
│       ├── Cargo.toml # Bindings crate configuration
│       └── src/       # PyO3 binding implementations
├── python/
│   └── quantforge/    # Python package
└── tests/             # Integration tests
```

## Build Instructions

### Development Build

```{code-block} bash
:name: setup-code-debug-build
:caption: Debug build (fast compilation)

# Debug build (fast compilation)
maturin develop

# Release build (optimized)
maturin develop --release
```

### Running Tests

```{code-block} bash
:name: setup-code-rust-test
:caption: Rust tests

# Rust tests
cargo test

# Python tests
pytest tests/python/

# Benchmarks
cargo bench
```

## IDE Setup

### VS Code

Recommended extensions:
- rust-analyzer
- Python
- Even Better TOML

Configuration example (`.vscode/settings.json`):
```json
{
    "rust-analyzer.cargo.features": ["python"],
    "python.linting.enabled": true,
    "python.formatting.provider": "black"
}
```

### IntelliJ IDEA / PyCharm

- Install Rust plugin
- Configure Python SDK
- Enable Cargo integration

## Debugging

### Rust Debugging

```{code-block} bash
:name: setup-code-debug-info-build
:caption: Build with debug information

# Build with debug information
RUST_BACKTRACE=1 cargo build

# Log output
RUST_LOG=debug cargo run
```

### Python Debugging

```python
import quantforge as qf
import logging

logging.basicConfig(level=logging.DEBUG)
# Debug execution
```

## Coding Standards

### Rust

- Format with `cargo fmt`
- Lint with `cargo clippy`
- Minimize unsafe operations

### Python

- Format with Black
- Type check with mypy
- PEP 8 compliant

## Performance Analysis

### Profiling

```{code-block} bash
:name: setup-code-rust-profiling
:caption: Rust profiling

# Rust profiling
cargo install flamegraph
cargo flamegraph

# Python profiling
python -m cProfile -o profile.out script.py
```

### Benchmarking

```{code-block} bash
:name: setup-code-criterionrs
:caption: Criterion.rs benchmarks

# Criterion.rs benchmarks
cargo bench

# Python benchmarks
python benchmarks/benchmark.py
```

## Troubleshooting

### Build Errors

```{code-block} bash
:name: setup-code-clean-build
:caption: Clean build

# Clean build
cargo clean
rm -rf target/
maturin develop --release
```

### Link Errors

```{code-block} bash
:name: setup-code-macos
:caption: macOS

# macOS
export DYLD_LIBRARY_PATH=$HOME/.rustup/toolchains/stable-*/lib

# Linux
export LD_LIBRARY_PATH=$HOME/.rustup/toolchains/stable-*/lib
```

## Next Steps

- [Architecture](architecture.md)
- [Contributing](contributing.md)
- [Testing Strategy](testing.md)
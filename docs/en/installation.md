# Installation Guide

## System Requirements

### Requirements

- **Python**: 3.12 or later
- **OS**: Linux, macOS, Windows
- **Memory**: 4GB or higher (recommended 8GB or higher for large-scale batch processing)

### Option Requirements

- **Rust environment**: Only required when building from source
- **CPU**: x86-64 or ARM processor

## Installation Method

### Install the development version from TestPyPI (currently available)

The latest development version is available from TestPyPI:

```{code-block} bash
:name: installation-code-testpypi
:caption: Install latest development version from TestPyPI
:linenos:

# Install latest development version from TestPyPI
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge
```

### Installing stable version from PyPI (in progress)

```{code-block} bash
:name: installation-code-section
:caption: After stable version is released
:linenos:

# After stable version is released
pip install quantforge
```

### use uv (recommended)

uv is a fast and reliable Python package manager:

```{code-block} bash
:name: installation-code-uv
:caption: Install uv (if not already installed)
:linenos:

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install from TestPyPI
uv pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge
```


## Platform-Specific Notes

### Linux

```{code-block} bash
:name: installation-code-ubuntudebian
:caption: Required system libraries (Ubuntu/Debian)
:linenos:

# Required system libraries (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y build-essential

# Required system libraries (RHEL/CentOS/Fedora)
sudo yum groupinstall "Development Tools"
```

### macOS

```{code-block} bash
:name: installation-code-xcode
:caption: Xcode Command Line Tools required
:linenos:

# Xcode Command Line Tools required
xcode-select --install

# For Apple Silicon
# Works via Rosetta 2 but native build recommended
arch -arm64 uv pip install quantforge
```

### Windows

```{code-block} powershell
:name: installation-code-visual-studio-build-tools
:caption: Visual Studio Build Tools may be required
:linenos:

# Visual Studio Build Tools may be required
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

# Installation via PowerShell
uv pip install quantforge
```

## Building from Source

For development versions or access to latest features:

### Prerequisites

```{code-block} bash
:name: installation-code-rust
:caption: Install Rust
:linenos:

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install Maturin
uv pip install maturin
```

### Build Procedure

```{code-block} bash
:name: installation-code-clone-repo
:caption: Clone repository
:linenos:

# Clone repository
git clone https://github.com/drillan/quantforge.git
cd quantforge

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install in development mode
maturin develop --release

# Or production build
maturin build --release
uv pip install target/wheels/quantforge-*.whl
```

## Installation confirmation

### Basic Verification

```{code-block} python
:name: installation-code-python
:caption: Run in Python interpreter
:linenos:

# Run in Python interpreter
from quantforge.models import black_scholes
import quantforge

# Check version
print(quantforge.__version__)

# Basic calculation test
price = black_scholes.call_price(
    s=100.0,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)
print(f"Test calculation: {price:.4f}")
# Expected: 10.4506
```

### Performance Testing

```python
import numpy as np
import time
from quantforge.models import black_scholes

# Performance measurement
n = 100_000
spots = np.random.uniform(90, 110, n)

start = time.perf_counter()
prices = black_scholes.call_price_batch(
    spots=spots,
    k=100.0,
    t=1.0,
    r=0.05,
    sigma=0.2
)
elapsed = (time.perf_counter() - start) * 1000

print(f"Batch processing: {n:,} options in {elapsed:.1f}ms")
print(f"Speed: {elapsed/n*1000:.1f}ns per option")
```

## Troubleshooting

### Common Problems and Solutions

#### ImportError: DLL load failed (Windows)

```{code-block} powershell
:name: installation-code-visual-c-redistributable
:caption: Install Visual C++ Redistributable
:linenos:

# Install Visual C++ Redistributable
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

#### Symbol not found (macOS)

```{code-block} bash
:name: installation-code-macos
:caption: Check macOS version
:linenos:

# Check macOS version
sw_vers

# Minimum requirement: macOS 10.15 or later
# For older versions, build from source
```

#### Illegal instruction (Linux)

```{code-block} bash
:name: installation-code-cpu
:caption: Check CPU features
:linenos:

# Check CPU features
lscpu | grep -E "avx|sse"

# Custom build
maturin build --release
```

#### Out Of Memory Error

```{code-block} python
:name: installation-code-batch-size
:caption: Adjust batch size
:linenos:

# Adjust batch size
# Split batches that are too large
batch_size = 10_000  # Process 10k at a time instead of 1M
```

### Performance Tuning

#### Environment Variables

```{code-block} bash
:name: installation-code-thread-control
:caption: Control thread count
:linenos:

# Control thread count
export RAYON_NUM_THREADS=8

# Debug settings
export RUST_LOG=debug
```

#### Python Settings

```{code-block} python
:name: installation-code-numpy
:caption: NumPy thread control
:linenos:

# NumPy thread control
import os
os.environ["OMP_NUM_THREADS"] = "1"  # Parallelized on QuantForge side
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
```

## Upgrade

### Upgrade to Latest Version

```{code-block} bash
:name: installation-code-uv-upgrade
:caption: Using uv
:linenos:

# Using uv
uv pip install --upgrade quantforge

# Using pip
pip install --upgrade quantforge
```

### Install Specific Version

```{code-block} bash
:name: installation-code-version-specify
:caption: Specify version
:linenos:

# Specify version
uv pip install quantforge==0.2.0

# Development version
uv pip install quantforge --pre
```

## Uninstall

```{code-block} bash
:name: installation-code-uv-uninstall
:caption: Using uv
:linenos:

# Using uv
uv pip uninstall quantforge

# Using pip
pip uninstall quantforge
```

## Next Step

After installation is complete:

1. [Quickstart](quickstart.md) - Get started in 5 minutes
2. [Basic Usage](user_guide/basic_usage.md) - Detailed usage instructions
3. API Reference - Detailed overview of all features (coming soon)

## Support

If the issue remains unresolved:

- [GitHub Issues](https://github.com/drillan/quantforge/issues)
- [Project Page](https://github.com/drillan/quantforge)

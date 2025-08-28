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

```bash
# TestPyPIから最新開発版をインストール
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge
```

### Installing stable version from PyPI (in progress)

```bash
# 安定版がリリースされた後
pip install quantforge
```

### use uv (recommended)

uv is a fast and reliable Python package manager:

```bash
# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows

# TestPyPIからインストール
uv pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge
```


## Platform-Specific Notes

### Linux

```bash
# 必要なシステムライブラリ（Ubuntu/Debian）
sudo apt-get update
sudo apt-get install -y build-essential

# 必要なシステムライブラリ（RHEL/CentOS/Fedora）
sudo yum groupinstall "Development Tools"
```

### macOS

```bash
# Xcodeコマンドラインツールが必要
xcode-select --install

# Apple Siliconの場合
# Rosetta 2経由でも動作しますが、ネイティブビルドを推奨
arch -arm64 uv pip install quantforge
```

### Windows

```powershell
# Visual Studio Build Toolsが必要な場合があります
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

# PowerShellでのインストール
uv pip install quantforge
```

## Building from Source

For development versions or access to latest features:

### Prerequisites

```bash
# Rustのインストール
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Maturinのインストール
uv pip install maturin
```

### Build Procedure

```bash
# リポジトリのクローン
git clone https://github.com/drillan/quantforge.git
cd quantforge

# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate

# 開発モードでインストール
maturin develop --release

# または本番ビルド
maturin build --release
uv pip install target/wheels/quantforge-*.whl
```

## Installation confirmation

### Basic Verification

```python
# Pythonインタープリタで実行
from quantforge.models import black_scholes
import quantforge

# バージョン確認
print(quantforge.__version__)

# 基本的な計算テスト
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

# パフォーマンス測定
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

```powershell
# Visual C++ Redistributableのインストール
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

#### Symbol not found (macOS)

```bash
# macOSバージョンの確認
sw_vers

# 最小要件: macOS 10.15以上
# 古いバージョンの場合はソースからビルド
```

#### Illegal instruction (Linux)

```bash
# CPU機能の確認
lscpu | grep -E "avx|sse"

# カスタムビルド
maturin build --release
```

#### Out Of Memory Error

```python
# バッチサイズを調整
# 大きすぎるバッチを分割
batch_size = 10_000  # 100万件ではなく1万件ずつ処理
```

### Performance Tuning

#### Environment Variables

```bash
# スレッド数の制御
export RAYON_NUM_THREADS=8

# デバッグ用設定
export RUST_LOG=debug
```

#### Python Settings

```python
# NumPyのスレッド制御
import os
os.environ["OMP_NUM_THREADS"] = "1"  # QuantForge側で並列化
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
```

## Upgrade

### Upgrade to Latest Version

```bash
# uvを使用
uv pip install --upgrade quantforge

# pipを使用
pip install --upgrade quantforge
```

### Install Specific Version

```bash
# バージョン指定
uv pip install quantforge==0.2.0

# 開発版
uv pip install quantforge --pre
```

## Uninstall

```bash
# uvを使用
uv pip uninstall quantforge

# pipを使用
pip uninstall quantforge
```

## Next Step

After installation is complete:

1. [Quickstart](quickstart.md) - Get started in 5 minutes
2. [Basic Usage](user_guide/basic_usage.md) - Detailed usage instructions
3. [API Reference](api/python/index.md) - Detailed overview of all features

## Support

If the issue remains unresolved:

- [GitHub Issues](https://github.com/drillan/quantforge/issues)
- [FAQ](faq.md)
- [Project Page](https://github.com/drillan/quantforge)

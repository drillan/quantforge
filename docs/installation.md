# インストールガイド

## システム要件

### 必須要件

- **Python**: 3.12以上
- **OS**: Linux, macOS, Windows
- **メモリ**: 4GB以上（大規模バッチ処理には8GB以上推奨）

### オプション要件

- **Rust環境**: ソースからビルドする場合のみ必要
- **CPU**: x86-64またはARMプロセッサ

## インストール方法

### uv を使用（推奨）

uvは高速で信頼性の高いPythonパッケージマネージャーです。

```bash
# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境の作成と有効化
uv venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows

# QuantForgeのインストール
uv pip install quantforge
```

### pip を使用

標準的なpipでもインストール可能です：

```bash
# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows

# インストール
pip install quantforge
```


## プラットフォーム別の注意事項

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

## ソースからのビルド

開発版や最新機能を使用したい場合：

### 前提条件

```bash
# Rustのインストール
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Maturinのインストール
uv pip install maturin
```

### ビルド手順

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/quantforge.git
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

## インストールの確認

### 基本的な確認

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

### パフォーマンステスト

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

## トラブルシューティング

### よくある問題と解決方法

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

#### メモリ不足エラー

```python
# バッチサイズを調整
# 大きすぎるバッチを分割
batch_size = 10_000  # 100万件ではなく1万件ずつ処理
```

### パフォーマンスチューニング

#### 環境変数

```bash
# スレッド数の制御
export RAYON_NUM_THREADS=8

# デバッグ用設定
export RUST_LOG=debug
```

#### Python設定

```python
# NumPyのスレッド制御
import os
os.environ["OMP_NUM_THREADS"] = "1"  # QuantForge側で並列化
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
```

## アップグレード

### 最新版へのアップグレード

```bash
# uvを使用
uv pip install --upgrade quantforge

# pipを使用
pip install --upgrade quantforge
```

### 特定バージョンのインストール

```bash
# バージョン指定
uv pip install quantforge==0.2.0

# 開発版
uv pip install quantforge --pre
```

## アンインストール

```bash
# uvを使用
uv pip uninstall quantforge

# pipを使用
pip uninstall quantforge
```

## 次のステップ

インストールが完了したら：

1. [クイックスタート](quickstart.md) - 5分で始める
2. [基本的な使い方](user_guide/basic_usage.md) - 詳細な使用方法
3. [APIリファレンス](api/python/index.md) - 全機能の詳細

## サポート

問題が解決しない場合：

- [GitHub Issues](https://github.com/yourusername/quantforge/issues)
- [FAQ](faq.md)
- [Discord Community](https://discord.gg/quantforge)
# QuantForge

<div align="center">

**日本語** | [English](./README.md)

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

**オプション価格計算エンジン - Python比500-1000倍の高速化を実現**

[Features](#-主要機能) • [Installation](#-インストール) • [Quick Start](#-クイックスタート) • [Benchmarks](#-ベンチマーク) • [Documentation](#-ドキュメント)

</div>

---

## 📖 概要

QuantForgeは、Rust + PyO3で実装された超高速オプション価格計算ライブラリです。Black-Scholesモデルに基づく価格計算、グリークス算出、インプライドボラティリティ計算を、Pythonの使いやすさを保ちながら、ネイティブコード並みの速度で実行できます。

### ✨ 特徴

#### オプション価格モデル

QuantForgeは複数のオプション価格モデルをサポートし、各資産クラスに最適化されています：

- **Black-Scholes**: 株式のヨーロピアンオプション
- **Merton** *(近日公開予定)*: 配当付き資産のオプション
- **Black76** *(近日公開予定)*: 商品オプション
- **Garman-Kohlhagen** *(近日公開予定)*: FXオプション

#### コア機能

- ⚡ **超高速処理**: Rust実装により、純粋なPython実装比で500-1000倍の高速化
- 🎯 **高精度計算**: erfベース実装により機械精度レベル（<1e-15）の計算精度を実現
- 🚀 **自動並列化**: 30,000要素以上のバッチ処理で自動的にRayon並列処理を適用
- 📦 **ゼロコピー設計**: NumPy配列を直接参照し、メモリコピーのオーバーヘッドを排除
- ✅ **堅牢性**: 158のゴールデンマスターテストを含む包括的なテストカバレッジ
- 🔧 **実務対応**: 入力検証、エッジケース処理、Put-Callパリティ検証済み

## 🚀 パフォーマンス指標

| 操作 | 処理時間 | 備考 |
|------|----------|------|
| Black-Scholes単一計算 | < 10ns | コール/プット価格 |
| 全グリークス計算 | < 50ns | Delta, Gamma, Vega, Theta, Rho |
| インプライドボラティリティ | < 200ns | Newton-Raphson法 |
| 100万件バッチ処理 | < 20ms | 自動並列化適用 |

## 📥 インストール

### 開発版のインストール

```bash
# リポジトリのクローン
git clone https://github.com/drillan/quantforge.git
cd quantforge

# Rustツールチェーンのインストール（未インストールの場合）
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# maturinのインストール
pip install maturin

# ライブラリのビルドとインストール
maturin develop --release
```

### 依存関係のインストール（開発用）

```bash
# uvを使用する場合（推奨）
uv sync --group dev

# または通常のpip
pip install -e ".[dev]"
```

## 💡 クイックスタート

### 使用方法

```python
import numpy as np
from quantforge.models import black_scholes

# 単一のオプション価格計算
spot = 100.0      # 原資産価格
strike = 105.0    # 権利行使価格
time = 0.25       # 満期までの時間（年）
rate = 0.05       # 無リスク金利
sigma = 0.2       # ボラティリティ（業界標準記号σ）

# 株式オプションのBlack-Scholesモデル
call_price = black_scholes.call_price(spot, strike, time, rate, sigma)
put_price = black_scholes.put_price(spot, strike, time, rate, sigma)
print(f"Call: ${call_price:.4f}, Put: ${put_price:.4f}")
```

### バッチ処理（大規模データの高速処理）

```python
# 複数のスポット価格でのバッチ計算
spots = np.linspace(80, 120, 100000)  # 10万個のデータポイント

from quantforge.models import black_scholes
call_prices = black_scholes.call_price_batch(spots, strike, time, rate, sigma)

# 自動的に並列処理が適用される（30,000要素以上）
print(f"Calculated {len(call_prices)} prices in milliseconds")
```

### グリークス計算

```python
# モジュールベースAPI
from quantforge.models import black_scholes

# 全グリークス一括計算
greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)
print(greeks)  # Greeks(delta=0.377, gamma=0.038, vega=0.189, theta=-0.026, rho=0.088)

# 個別のグリークスへのアクセス
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### インプライドボラティリティ計算

```python
from quantforge.models import black_scholes

# マーケット価格からインプライドボラティリティを逆算
market_price = 3.5
iv = black_scholes.implied_volatility(
    market_price, spot, strike, time, rate, is_call=True
)
print(f"Implied Volatility (Call): {iv_call:.4%}")

# バッチ処理にも対応
market_prices = np.array([3.0, 3.5, 4.0, 4.5, 5.0])
spots_arr = np.full(5, spot)
strikes_arr = np.full(5, strike)
times_arr = np.full(5, time)
rates_arr = np.full(5, rate)
is_calls = np.array([True, True, True, True, True])

ivs = qf.calculate_implied_volatility_batch(
    market_prices, spots_arr, strikes_arr, times_arr, rates_arr, is_calls
)
print(f"Implied Volatilities: {ivs}")
```

## 🔧 実装済み機能

### 価格計算
- ✅ ヨーロピアンコールオプション価格（単一/バッチ）
- ✅ ヨーロピアンプットオプション価格（単一/バッチ）
- ✅ Put-Callパリティ検証
- ✅ 自動並列化（大規模データ）

### グリークス（感応度）
- ✅ **Delta**: 原資産価格に対する感応度（コール/プット）
- ✅ **Gamma**: Deltaの変化率
- ✅ **Vega**: ボラティリティに対する感応度
- ✅ **Theta**: 時間経過に対する感応度（コール/プット）
- ✅ **Rho**: 金利に対する感応度（コール/プット）
- ✅ 全グリークス一括計算
- ✅ バッチ処理対応（Delta Call, Gamma）

### インプライドボラティリティ
- ✅ Newton-Raphson法による高速計算
- ✅ Brent法によるフォールバック
- ✅ Brenner-Subrahmanyam近似による初期推定
- ✅ コール/プット両対応
- ✅ バッチ処理（自動並列化）

### 技術的特徴
- ✅ **高精度数学関数**: erfベース正規分布実装（機械精度<1e-15）
- ✅ **ゼロコピー設計**: NumPy配列の直接参照
- ✅ **動的並列化**: データサイズに応じた自動最適化
- ✅ **包括的な入力検証**: エッジケース対応

## 📊 ベンチマーク

### Black-Scholes価格計算（100万件）

| 実装 | 処理時間 | 相対速度 |
|------|----------|----------|
| Pure Python | 10,000ms | 1x |
| NumPy | 100ms | 100x |
| **QuantForge (Sequential)** | **20ms** | **500x** |
| **QuantForge (Parallel)** | **9.7ms** | **1,000x** |

### グリークス計算（10万件）

| グリーク | 処理時間 | スループット |
|----------|----------|--------------|
| Delta | 1.2ms | 83M ops/sec |
| Gamma | 1.5ms | 67M ops/sec |
| Vega | 1.4ms | 71M ops/sec |
| All Greeks | 4.8ms | 21M ops/sec |

## 🛠️ 開発環境セットアップ

### 必要要件

- Python 3.11以上
- Rust 1.88以上
- NumPy 1.20以上

### ビルドとテスト

```bash
# Rustコードのビルド
cargo build --release

# Rustテストの実行
cargo test --release

# Pythonテストの実行
pytest

# カバレッジ付きテスト
pytest --cov=quantforge --cov-report=html

# ベンチマークの実行
pytest tests/performance/ -v --benchmark-only
```

### コード品質管理

```bash
# Pythonコードのフォーマット
uv run ruff format .

# リントチェック
uv run ruff check .

# 型チェック
uv run mypy .

# Rustコードのチェック
cargo clippy -- -D warnings
```

## 📚 ドキュメント

詳細なドキュメントはSphinxで生成できます：

```bash
# ドキュメントのビルド
uv run sphinx-build -M html docs docs/_build

# ブラウザで開く
open docs/_build/html/index.html
```

ドキュメントには以下が含まれます：
- APIリファレンス
- 数学的背景
- アーキテクチャ解説
- パフォーマンスチューニングガイド

## 🗺️ ロードマップ

### 実装済み ✅
- [x] Black-Scholesモデル（コール/プット）
- [x] 全グリークス実装
- [x] インプライドボラティリティ計算
- [x] バッチ処理と並列化
- [x] 包括的なテストスイート

### 開発予定 🚧
- [ ] アメリカンオプション（二項ツリー/最小二乗モンテカルロ）
- [ ] エキゾチックオプション（バリア、アジアン、ルックバック）
- [ ] 確率的ボラティリティモデル（Heston、SABR）
- [ ] モンテカルロシミュレーション
- [ ] 有限差分法
- [ ] キャリブレーション機能
- [ ] リアルタイムマーケットデータ連携

## 🤝 コントリビューション

プルリクエストを歓迎します！開発に参加する際は以下をご確認ください：

1. [CLAUDE.md](./CLAUDE.md) - 開発ガイドラインと品質基準
2. [plans/](./plans/) - 実装計画と技術設計書
3. テストの追加（既存のテストスイートを参考に）
4. コード品質チェックの実施

### 開発フロー

```bash
# フィーチャーブランチの作成
git checkout -b feature/your-feature

# 変更の実装とテスト
cargo test --release
pytest

# コミット前の品質チェック
cargo clippy -- -D warnings
uv run ruff check .
uv run mypy .

# プルリクエストの作成
git push origin feature/your-feature
```

## 📈 パフォーマンスの秘密

QuantForgeが高速な理由：

1. **Rust実装**: メモリ安全性を保証しながらC++並みの性能
2. **最適化された実装**: 高速な数学関数の使用
3. **Rayon並列化**: データ並列処理の自動適用
4. **ゼロコピー**: PyO3によるNumPy配列の直接操作
5. **最適化された数学関数**: erfベース実装による高速・高精度計算

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご確認ください。

## 🙏 謝辞

- [PyO3](https://github.com/PyO3/pyo3) - RustとPythonの優れたバインディング
- [Rayon](https://github.com/rayon-rs/rayon) - データ並列処理ライブラリ
- [maturin](https://github.com/PyO3/maturin) - Rust拡張モジュールのビルドツール

---

<div align="center">

**Built with ❤️ and Rust**

[Report Bug](https://github.com/drillan/quantforge/issues) • [Request Feature](https://github.com/drillan/quantforge/issues)

</div>
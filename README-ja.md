# QuantForge

<div align="center">

**日本語** | [English](./README.md)

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

**Rust実装オプション価格計算ライブラリ - NumPy+SciPy比最大<!-- BENCHMARK:MAX_SPEEDUP_NUMPY -->1<!-- /BENCHMARK:MAX_SPEEDUP_NUMPY -->倍の処理速度**

[Features](#-主要機能) • [Installation](#-インストール) • [Quick Start](#-クイックスタート) • [Benchmarks](#-ベンチマーク) • [Documentation](#-ドキュメント)

</div>

---

## 📖 概要

QuantForgeは、Rust + PyO3で実装されたオプション価格計算ライブラリです。Black-Scholesモデルに基づく価格計算、グリークス算出、インプライドボラティリティ計算を、Pythonの使いやすさを保ちながら、Rustのパフォーマンスで実行できます。

## 📋 機能と実装

#### オプション価格モデル

QuantForgeは複数のオプション価格モデルをサポートし、各資産クラスに最適化されています：

- **Black-Scholes**: 株式のヨーロピアンオプション
- **アメリカンオプション**: Bjerksund-Stensland (2002) 近似による早期行使権付きオプション
- **Merton**: 配当付き資産のオプション
- **Black76**: 商品・先物オプション
- **アジアンオプション** *(近日公開予定)*: 経路依存型オプション
- **スプレッドオプション** *(近日公開予定)*: 複数資産オプション
- **Garman-Kohlhagen** *(近日公開予定)*: FXオプション

#### コア機能

- ⚡ **高速処理**: Rust実装により、NumPy+SciPy比で最大<!-- BENCHMARK:MAX_SPEEDUP_NUMPY -->1<!-- /BENCHMARK:MAX_SPEEDUP_NUMPY -->倍、Pure Python比で最大<!-- BENCHMARK:MAX_SPEEDUP_PYTHON -->1<!-- /BENCHMARK:MAX_SPEEDUP_PYTHON -->倍の高速化
- 🎯 **高精度計算**: erfベース実装により機械精度レベル（<1e-15）の計算精度を実現
- 🔥 **インプライドボラティリティ**: Newton-Raphson法により Pure Python比で最大<!-- BENCHMARK:IV:MAX_SPEEDUP -->170<!-- /BENCHMARK:IV:MAX_SPEEDUP -->倍の高速化
- 📊 **完全なグリークス**: Delta, Gamma, Vega, Theta, Rho に加え、モデル固有のグリークス（配当Rho、早期行使境界など）
- 🚀 **自動並列化**: 30,000要素以上のバッチ処理で自動的にRayon並列処理を適用
- 📦 **ゼロコピー設計**: NumPy配列を直接参照し、メモリコピーのオーバーヘッドを排除
- ✅ **堅牢性**: 250以上のゴールデンマスターテストを含む包括的なテストカバレッジ
- 🔧 **実務対応**: 入力検証、エッジケース処理、Put-Callパリティ検証済み

## 📊 パフォーマンス測定結果

<!-- BENCHMARK:SUMMARY:START -->
測定環境: Linux - 6コア - 29.3GB RAM - Python 3.12.5 - 2025-09-12 12:47:56
<!-- BENCHMARK:SUMMARY:END -->

### 最新ベンチマーク結果
<!-- BENCHMARK:TABLE:START -->
※ベンチマークデータが見つかりません
<!-- BENCHMARK:TABLE:END -->

*性能は使用環境により変動します。測定値は5回実行の中央値です。詳細は[ベンチマーク](docs/ja/performance/benchmarks.md)を参照。*

### 🔥 インプライドボラティリティ性能

Newton-Raphson法による公正な比較（同一アルゴリズム・同一パラメータ）:

<!-- BENCHMARK:IV:TABLE:START -->
| データサイズ | QuantForge | NumPy Newton | Pure Python | 最速比 |
|------------|------------|--------------|-------------|--------|
| 単一計算 | 3.94 μs | 180.86 μs | 3.18 μs | 45x |
| 100件 | 34.40 μs | 937.50 μs | 1.03 ms | 30x |
| 1,000件 | 184.11 μs | 1.33 ms | 10.45 ms | 56x |
| 10,000件 | 599.53 μs | 4.28 ms | 102.07 ms | **170x** |
<!-- BENCHMARK:IV:TABLE:END -->

最大速度向上: <!-- BENCHMARK:IV:MAX_SPEEDUP -->170<!-- /BENCHMARK:IV:MAX_SPEEDUP -->倍（Pure Python比）、<!-- BENCHMARK:IV:MAX_SPEEDUP_NUMPY -->45<!-- /BENCHMARK:IV:MAX_SPEEDUP_NUMPY -->倍（NumPy比）

## 📥 インストール

### TestPyPIからのインストール（最新開発版）

```bash
# TestPyPIから最新の開発版をインストール
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ quantforge
```

### ソースからのインストール（開発用）

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

## 🚀 クイックスタート

### 基本的な使い方

```python
import numpy as np
from quantforge.models import black_scholes

# 単一価格計算
spot = 100.0   # 現在価格
strike = 110.0 # 権利行使価格
time = 1.0     # 満期までの時間（年）
rate = 0.05    # 無リスク金利
sigma = 0.2    # ボラティリティ

# コールオプション価格
call_price = black_scholes.call_price(spot, strike, time, rate, sigma)
print(f"Call Price: ${call_price:.4f}")

# プットオプション価格
put_price = black_scholes.put_price(spot, strike, time, rate, sigma)
print(f"Put Price: ${put_price:.4f}")

# 全グリークス計算
greeks = black_scholes.greeks(spot, strike, time, rate, sigma, is_call=True)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
print(f"Theta: {greeks.theta:.4f}")
print(f"Rho: {greeks.rho:.4f}")
```

### バッチ処理（高速化の効果大）

```python
import numpy as np
from quantforge.models import black_scholes

# 100万件のランダムデータ生成
n = 1_000_000
spots = np.random.uniform(80, 120, n)      # 80-120の一様分布
strikes = np.full(n, 100.0)                # 固定ストライク
times = np.random.uniform(0.1, 2.0, n)     # 0.1-2年
rates = np.full(n, 0.05)                   # 固定金利
sigmas = np.random.uniform(0.1, 0.4, n)    # 10-40%のボラティリティ

# バッチ処理（約56ms for 100万件）
prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)

# バッチグリークス計算
greeks = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, 
                                    is_call=np.full(n, True))
```

### インプライドボラティリティ計算

```python
from quantforge.models import black_scholes

# 市場価格からインプライドボラティリティを逆算
market_price = 12.50
iv = black_scholes.implied_volatility(
    price=market_price,
    s=100.0,  # 現在価格
    k=110.0,  # 権利行使価格
    t=1.0,    # 満期
    r=0.05,   # 金利
    is_call=True
)
print(f"Implied Volatility: {iv:.2%}")
```

## 🔄 並列処理の最適化

QuantForgeは計算量とオーバーヘッドのバランスを考慮して、自動的に並列処理を適用します：

| データサイズ | 処理方式 | 備考 |
|------------|---------|------|
| < 1,000 | 単一スレッド | オーバーヘッド回避 |
| 1,000 ~ 30,000 | マルチスレッド（小） | 2-4スレッド使用 |
| > 30,000 | 完全並列 | 利用可能な全コア使用 |

```python
import numpy as np
from quantforge.models import black_scholes

# 大規模データ: 自動的に並列処理（すべてのコア使用）
large_spots = np.random.uniform(90, 110, 1_000_000)
large_prices = black_scholes.call_price_batch(large_spots, 100, 1.0, 0.05, 0.2)

# 小規模データ: 単一スレッド処理（オーバーヘッド回避）
small_spots = np.array([100, 105, 110])
small_prices = black_scholes.call_price_batch(small_spots, 100, 1.0, 0.05, 0.2)
```

## 📊 ベンチマーク

### 実践シナリオ: ボラティリティサーフェス構築（10×10グリッド）
| 実装方式 | 処理時間 | 対QuantForge比 |
|---------|----------|---------------|
| **QuantForge** (並列処理) | 0.1 ms | - |
| **NumPy+SciPy** (ベクトル化) | 0.4 ms | 4倍遅い |
| **Pure Python** (forループ) | 5.5 ms | 55倍遅い |

### 実践シナリオ: 10,000オプションのポートフォリオリスク計算
| 実装方式 | 処理時間 | 対QuantForge比 |
|---------|----------|---------------|
| **QuantForge** (並列処理) | 1.9 ms | - |
| **NumPy+SciPy** (ベクトル化) | 2.7 ms | 1.4倍遅い |
| **Pure Python** (forループ、推定) | ~70 ms | 37倍遅い |

詳細なベンチマーク結果は[パフォーマンス測定](docs/ja/performance/benchmarks.md)を参照してください。

## 🏗️ アーキテクチャ

```
quantforge/
├── src/                    # Rustコア実装
│   ├── models/            # 価格モデル（Black-Scholes, Black76, Merton等）
│   ├── math/              # 数学関数（erf, norm_cdf等）
│   ├── validation.rs      # 入力検証
│   └── traits.rs          # バッチ処理トレイト
│
├── python/                 # Pythonバインディング
│   └── quantforge/        # Pythonパッケージ
│       └── models/        # モデル別モジュール
│
└── tests/                  # テストスイート
    ├── unit/              # 単体テスト
    ├── integration/       # 統合テスト
    ├── golden_master/     # ゴールデンマスターテスト
    └── performance/       # ベンチマークテスト
```

### 技術スタック
- **Rust 1.88+**: コア計算エンジン
- **PyO3**: Python-Rustバインディング
- **Rayon**: データ並列処理
- **NumPy**: 配列インターフェース
- **maturin**: ビルド・パッケージング

## 📚 ドキュメント

- [公式ドキュメント（日本語）](https://drillan.github.io/quantforge/ja/)
- [API リファレンス](https://drillan.github.io/quantforge/ja/api/)
- [パフォーマンスガイド](docs/ja/performance/optimization.md)
- [開発者ガイド](docs/ja/development/architecture.md)
- [詳細なベンチマーク結果](docs/ja/performance/benchmarks.md)

## 🧪 テスト

```bash
# Pythonテスト実行（450以上のテストケース）
pytest tests/

# Rustテスト実行
cargo test --release

# カバレッジ測定
pytest tests/ --cov=quantforge --cov-report=html

# ベンチマーク実行
pytest tests/performance/ -m benchmark
```

## 🤝 コントリビューション

プルリクエストを歓迎します！重要な変更の場合は、まずissueを開いて変更内容について議論してください。

1. フォーク
2. 機能ブランチを作成（`git checkout -b feature/amazing-feature`）
3. 変更をコミット（`git commit -m 'Add amazing feature'`）
4. ブランチにプッシュ（`git push origin feature/amazing-feature`）
5. プルリクエストを開く

詳細は[コントリビューションガイド](CONTRIBUTING.md)を参照してください。

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています - 詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🙏 謝辞

- Black-Scholes式の実装と検証データを提供してくださったQuantLib
- 高速並列処理を実現するRayonプロジェクト
- Python-Rustバインディングを容易にするPyO3プロジェクト

## 📮 連絡先

質問や提案がある場合は、[issue](https://github.com/drillan/quantforge/issues)を開くか、[ディスカッション](https://github.com/drillan/quantforge/discussions)に参加してください。

---

<div align="center">
Made with ❤️ by the QuantForge team
</div>
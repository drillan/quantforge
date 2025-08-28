# QuantForge

<div align="center">

**日本語** | [English](./README.md)

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Rust](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

**Rust実装オプション価格計算ライブラリ - NumPy+SciPy比最大472倍の処理速度**

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

- ⚡ **高速処理**: Rust実装により、NumPy+SciPy比で最大472倍、Pure Python比で最大346倍の高速化
- 🎯 **高精度計算**: erfベース実装により機械精度レベル（<1e-15）の計算精度を実現
- 📊 **完全なグリークス**: Delta, Gamma, Vega, Theta, Rho に加え、モデル固有のグリークス（配当Rho、早期行使境界など）
- 🚀 **自動並列化**: 30,000要素以上のバッチ処理で自動的にRayon並列処理を適用
- 📦 **ゼロコピー設計**: NumPy配列を直接参照し、メモリコピーのオーバーヘッドを排除
- ✅ **堅牢性**: 250以上のゴールデンマスターテストを含む包括的なテストカバレッジ
- 🔧 **実務対応**: 入力検証、エッジケース処理、Put-Callパリティ検証済み

## 📊 パフォーマンス測定結果

測定環境: AMD Ryzen 5 5600G (6コア/12スレッド)、29.3GB RAM、Linux 6.12（2025-08-28測定）

### インプライドボラティリティ計算
| 実装方式 | 単一計算 | 10,000件バッチ | 
|---------|----------|---------------|
| **QuantForge** | 1.5 μs | 19.87 ms |
| **Pure Python** | 32.9 μs (22倍遅い) | 6,865 ms (346倍遅い) |
| **NumPy+SciPy** | 707.3 μs (472倍遅い) | 120 ms (6倍遅い) |

### Black-Scholes価格計算
| 操作 | 処理時間 | 備考 |
|------|----------|------|
| 単一コール価格 | 1.40 μs | 誤差関数実装 |
| 全グリークス計算 | < 50 ns | Delta, Gamma, Vega, Theta, Rho |
| 100万件バッチ処理 | 55.60 ms | 自動並列化適用 |

*性能は使用環境により変動します。測定値は5回実行の中央値です。*

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

## 💡 クイックスタート

### Black-Scholesモデル（ヨーロピアンオプション）

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

### アメリカンオプション（早期行使権付き）

```python
from quantforge.models import american

# 配当付き株式のアメリカンオプション
spot = 100.0      # 現在の株価
strike = 100.0    # 権利行使価格
time = 1.0        # 満期までの時間（年）
rate = 0.05       # 無リスク金利
q = 0.03          # 配当利回り
sigma = 0.2       # ボラティリティ

# Bjerksund-Stensland 2002近似による価格計算
call_price = american.call_price(spot, strike, time, rate, q, sigma)
put_price = american.put_price(spot, strike, time, rate, q, sigma)

# 早期行使境界
boundary = american.exercise_boundary(spot, strike, time, rate, q, sigma, is_call=True)
print(f"早期行使境界: ${boundary:.2f}")
```

### Mertonモデル（配当付き資産）

```python
from quantforge.models import merton

# 配当を支払う株式のオプション
spot = 100.0      # 現在の株価
strike = 105.0    # 権利行使価格
time = 1.0        # 満期までの時間
rate = 0.05       # 無リスク金利
q = 0.03          # 連続配当利回り
sigma = 0.2       # ボラティリティ

# Mertonモデルによる価格計算
call_price = merton.call_price(spot, strike, time, rate, q, sigma)
put_price = merton.put_price(spot, strike, time, rate, q, sigma)

# 配当感応度を含むグリークス
greeks = merton.greeks(spot, strike, time, rate, q, sigma, is_call=True)
print(f"配当Rho: {greeks.dividend_rho:.4f}")  # Merton固有のグリーク
```

### Black76モデル（先物・商品）

```python
from quantforge.models import black76

# 商品先物オプション
forward = 75.50   # 先物価格
strike = 70.00    # 権利行使価格
time = 0.25       # 満期までの時間
rate = 0.05       # 無リスク金利
sigma = 0.3       # ボラティリティ

# Black76による先物オプション価格
call_price = black76.call_price(forward, strike, time, rate, sigma)
put_price = black76.put_price(forward, strike, time, rate, sigma)

print(f"先物コール: ${call_price:.4f}, プット: ${put_price:.4f}")
```

### バッチ処理（完全配列サポート + Broadcasting）

```python
# すべてのパラメータが配列を受け付ける（Broadcasting対応）
n = 100000  # 10万個のオプション
spots = np.linspace(80, 120, n)
strikes = 100.0  # スカラーは自動的に配列サイズに拡張
times = np.random.uniform(0.1, 2.0, n)
rates = 0.05
sigmas = np.random.uniform(0.1, 0.4, n)

from quantforge.models import black_scholes
# すべてのパラメータに配列またはスカラーを指定可能
call_prices = black_scholes.call_price_batch(spots, strikes, times, rates, sigmas)

# Greeksバッチ計算（NumPy配列の辞書を返却）
greeks = black_scholes.greeks_batch(spots, strikes, times, rates, sigmas, is_calls=True)
portfolio_delta = greeks['delta'].sum()
portfolio_vega = greeks['vega'].sum()

# 自動的に並列処理が適用される（30,000要素以上）
print(f"{len(call_prices):,}個のオプションを処理")
print(f"ポートフォリオDelta: {portfolio_delta:.2f}, Vega: {portfolio_vega:.2f}")
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
print(f"Implied Volatility: {iv:.4%}")

# 注：バッチ処理版は将来のリリースで提供予定
```

## 🔬 実装の詳細

### 数学的基盤
- **正規CDF**: 機械精度を実現するerror function (erf)ベース実装
- **グリークス**: エッジケース（ATM、満期直前）の特別処理を含む解析式
- **IVソルバー**: Newton-Raphson法（高速収束）とBrent法（確実な収束）のハイブリッドアプローチ

### アーキテクチャ
- **ゼロコピー設計**: PyO3経由でNumPy配列に直接アクセス
- **動的並列化**: ワークロードに基づく自動スレッドプール調整
- **メモリ効率**: 小バッチではスタック割り当て、最小限のヒープ使用

### 検証
- **250以上のゴールデンマスターテスト**: 参照実装との照合
- **プロパティベーステスティング**: Hypothesisフレームワークによるエッジケース検出
- **プットコールパリティ**: テストスイートでの自動検証
- **境界条件**: 極値の特別処理
- **モデル間クロス検証**: 関連モデル（BS-Merton、American-European）間の整合性チェック

## 🚀 QuantForgeが高速な理由

QuantForgeは5つの主要な最適化により卓越したパフォーマンスを実現しています：

1. **Rustコア実装**
   - ガベージコレクション無しでゼロコスト抽象化とメモリ安全性を実現
   - コンパイル時最適化とインライン化
   - メモリレイアウトの直接制御

2. **数学的最適化**
   - 機械精度を実現するerror function (erf)ベースの正規CDF
   - 数値微分を回避する解析的グリークス公式
   - 境界条件の特別ケース処理

3. **自動並列化**
   - 30,000要素以上の配列に対するRayonベースの並列処理
   - 最適なCPU使用率のためのワークスティーリングスケジューラ
   - キャッシュフレンドリーなデータアクセスパターン

4. **ゼロコピーNumPy統合**
   - PyO3のunsafeブロックを介した直接メモリアクセス
   - シリアライゼーション/デシリアライゼーションのオーバーヘッドなし
   - ndarrayによる効率的な配列イテレーション

5. **最適化された数学関数**
   - 適用可能な場所でのSIMDベクトル化
   - クリティカルパスのブランチフリーアルゴリズム
   - 頻繁にアクセスされる値のルックアップテーブル

## 📊 詳細なベンチマーク結果

### 実践シナリオでの性能比較

#### ボラティリティサーフェス構築（100×100グリッド）
| 実装方式 | 処理時間 | 
|---------|----------|
| **NumPy+SciPy** (ベクトル化) | 2.3 ms |
| **QuantForge** (並列処理) | 6.5 ms |

※ 大規模データではNumPy+SciPyのベクトル化が有効な場合があります

#### ポートフォリオリスク計算（10,000オプション）  
| 実装方式 | 処理時間 |
|---------|----------|
| **QuantForge** (並列処理) | 1.9 ms |
| **NumPy+SciPy** (ベクトル化) | 2.7 ms |

### データサイズ別の最適実装

#### 小規模（100-1,000要素）
- QuantForgeが最高性能（FFIオーバーヘッドが少ない）

#### 中規模（10,000-100,000要素）
- NumPy+SciPyのベクトル化が競合
- FFIオーバーヘッドが顕著

#### 大規模（100万要素以上）
- QuantForgeの並列処理が最大効果を発揮
- Rayonによる自動並列化

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

完全なドキュメントはこちら: **https://drillan.github.io/quantforge/ja/**

ローカルでのドキュメントビルド：

```bash
# ドキュメントのビルド
uv run sphinx-build -M html docs/ja docs/ja/_build

# ブラウザで開く
open docs/ja/_build/html/index.html
```

ドキュメントには以下が含まれます：
- APIリファレンス
- 数学的背景
- アーキテクチャ解説
- パフォーマンスチューニングガイド

## 🗺️ ロードマップ

### 実装済み ✅
- [x] Black-Scholesモデル（ヨーロピアンオプション）
- [x] アメリカンオプション（Bjerksund-Stensland 2002）
- [x] Mertonモデル（配当付き資産）
- [x] Black76モデル（先物・商品）
- [x] 全グリークス実装（モデル固有グリークス含む）
- [x] インプライドボラティリティ計算
- [x] バッチ処理と自動並列化
- [x] ゼロコピーNumPy統合
- [x] 早期行使境界計算
- [x] 250以上のゴールデンマスターテスト

### 開発中 🚧
- [ ] アジアンオプション（幾何平均・算術平均）
- [ ] スプレッドオプション（Kirk近似）
- [ ] バリアオプション（アップ/ダウン、イン/アウト）
- [ ] ルックバックオプション

### 開発予定 📋
- [ ] Garman-Kohlhagen（FXオプション）
- [ ] 確率的ボラティリティモデル（Heston、SABR）
- [ ] モンテカルロフレームワーク（分散削減技法付き）
- [ ] 有限差分法（アメリカンオプション精密化）
- [ ] GPU高速化（CUDA/Metal）
- [ ] リアルタイムマーケットデータ連携
- [ ] キャリブレーションフレームワーク

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

## 📈 ユースケース

QuantForgeは以下の用途に最適化されています：
- **高頻度取引**: マーケットメイキングのためのマイクロ秒レベルの価格計算
- **リスク管理**: リアルタイムポートフォリオグリークス計算
- **バックテスト**: 数百万シナリオの効率的な処理
- **リサーチ**: Pythonでの高速プロトタイピング、本番環境レベルの性能

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご確認ください。

## 🙏 謝辞

- [PyO3](https://github.com/PyO3/pyo3) - RustとPythonの優れたバインディング
- [Rayon](https://github.com/rayon-rs/rayon) - データ並列処理ライブラリ
- [maturin](https://github.com/PyO3/maturin) - Rust拡張モジュールのビルドツール

## 📞 お問い合わせ

- **Issues**: [GitHub Issues](https://github.com/drillan/quantforge/issues)
- **Discussions**: [GitHub Discussions](https://github.com/drillan/quantforge/discussions)
- **Security**: セキュリティ脆弱性は非公開でご報告ください

---

<div align="center">

**Built with ❤️ and Rust**

[Report Bug](https://github.com/drillan/quantforge/issues) • [Request Feature](https://github.com/drillan/quantforge/issues)

*パフォーマンス測定環境: AMD Ryzen 5 5600G、29.3GB RAM、Linux 6.12（2025-08-28測定）*

</div>
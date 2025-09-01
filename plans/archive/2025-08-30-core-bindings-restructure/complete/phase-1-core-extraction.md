# Phase 1: Core層構築

## 概要
PyO3依存を完全に除去し、言語非依存の純粋なRustライブラリとしてCore層を構築します。

## 前提条件
- Phase 0の完了
- ゴールデンマスターテストの準備完了
- 設計ドキュメントの承認

## タスクリスト

### 1. Core層ディレクトリ構造作成 [1時間]

#### 1.1 基本構造の作成
```bash
mkdir -p core/{src,tests,benchmarks,examples}
mkdir -p core/src/{models,math,validation,traits,error}
mkdir -p core/src/models/{black_scholes,black76,merton,american}
```

#### 1.2 Cargo.toml作成
- [x] ワークスペース設定（ルート）
- [x] コアクレート設定
- [x] 依存関係定義（PyO3除外）
- [x] 最適化設定

**ルート Cargo.toml（ワークスペース）**:
```toml
[workspace]
members = [
    "core",
    "bindings/python",
]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
authors = ["driller"]
license = "MIT"
repository = "https://github.com/drillan/quantforge"

[workspace.dependencies]
ndarray = "0.16"
rayon = "1.10"
thiserror = "2.0"
libm = "0.2"

# 開発依存関係
approx = "0.5"
criterion = "0.5"
proptest = "1.0"

[profile.release]
lto = true
codegen-units = 1
opt-level = 3
```

**core/Cargo.toml**:
```toml
[package]
name = "quantforge-core"
version.workspace = true
edition.workspace = true
authors.workspace = true
license.workspace = true

[dependencies]
ndarray.workspace = true
rayon.workspace = true
libm.workspace = true
thiserror.workspace = true

[dev-dependencies]
approx.workspace = true
criterion.workspace = true
proptest.workspace = true

[[bench]]
name = "core_benchmarks"
harness = false
```

### 2. コア実装の抽出 [8時間]

#### 2.1 数学関数の移行
**対象ファイル**:
- `src/math/distributions.rs` → `core/src/math/distributions.rs`
- `src/math/solvers.rs` → `core/src/math/solvers.rs`

**作業内容**:
- [x] PyO3アトリビュート削除
- [x] 純粋Rust関数として再定義
- [x] ユニットテスト移行

**完了条件**: 移動したモジュールが `cargo check` でコンパイル可能

```rust
// Before (src/math/distributions.rs)
#[pyfunction]
pub fn norm_cdf(x: f64) -> f64 { ... }

// After (core/src/math/distributions.rs)
pub fn norm_cdf(x: f64) -> f64 { ... }
```

#### 2.2 モデル実装の抽出

**Black-Scholesモデル**:
- [x] `src/models/black_scholes.rs` からコア計算を抽出
- [x] パラメータ構造体をPyO3非依存に
- [x] Greeks計算の純粋実装

```rust
// core/src/models/black_scholes.rs
pub struct BlackScholesParams {
    pub spot: f64,
    pub strike: f64,
    pub time: f64,
    pub rate: f64,
    pub volatility: f64,
}

impl BlackScholesParams {
    pub fn call_price(&self) -> f64 {
        // 純粋な計算ロジック
    }
}
```

**同様に処理**:
- [x] Black76モデル
- [x] Mertonモデル
- [x] Americanモデル

**完了条件**: `quantforge-core` から `pyo3` 依存を削除し、`cargo check` が通る

#### 2.3 トレイトの再設計
- [x] `PricingModel` トレイト定義
- [x] `Greeks` トレイト定義
- [x] `BatchProcessor` トレイト定義

```rust
// core/src/traits/pricing.rs
pub trait PricingModel {
    type Params;
    fn call_price(params: &Self::Params) -> f64;
    fn put_price(params: &Self::Params) -> f64;
}
```

#### 2.4 エラー型の統一
- [x] PyO3依存しないエラー型定義
- [x] Result型の標準化

```rust
// core/src/error.rs
#[derive(Debug, thiserror::Error)]
pub enum QuantForgeError {
    #[error("Invalid input: {0}")]
    InvalidInput(String),
    #[error("Numerical error: {0}")]
    NumericalError(String),
}

pub type Result<T> = std::result::Result<T, QuantForgeError>;
```

### 3. バッチ処理の最適化 [4時間]

#### 3.1 並列処理戦略
- [x] Rayon統合
- [x] メモリ効率的な実装

```rust
// core/src/models/batch.rs
use rayon::prelude::*;

pub fn call_price_batch(params: &[BlackScholesParams]) -> Vec<f64> {
    params.par_iter()
        .map(|p| p.call_price())
        .collect()
}
```

#### 3.2 ベクトル化対応
- [x] ndarray統合
- [x] ブロードキャスティング実装

### 4. Core層テスト作成 [3時間]

#### 4.1 ユニットテスト
各モジュールに対して：
- [x] 正常系テスト
- [x] エッジケーステスト
- [x] エラーケーステスト

```rust
// core/tests/black_scholes.rs
#[test]
fn test_call_price_atm() {
    let params = BlackScholesParams {
        spot: 100.0,
        strike: 100.0,
        time: 1.0,
        rate: 0.05,
        volatility: 0.2,
    };
    let price = params.call_price();
    assert_relative_eq!(price, 10.450583572185565, epsilon = 1e-10);
}
```

#### 4.2 プロパティベーステスト
```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_put_call_parity(
        spot in 1.0..200.0,
        strike in 1.0..200.0,
        time in 0.01..2.0,
        rate in 0.0..0.2,
        vol in 0.01..1.0
    ) {
        // Put-Call parity検証
    }
}
```

#### 4.3 ベンチマーク作成
```rust
// core/benchmarks/black_scholes.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_call_price(c: &mut Criterion) {
    c.bench_function("black_scholes_call", |b| {
        b.iter(|| {
            let params = black_box(create_test_params());
            params.call_price()
        });
    });
}
```

### 5. ビルドとテスト [1時間]

#### 5.1 ビルド確認
```bash
cd core
cargo build --release
cargo test --all
cargo bench
```

#### 5.2 コード品質チェック
```bash
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
```

#### 5.3 テストカバレッジ測定
```bash
cargo tarpaulin --out Html --output-dir coverage/
```

## 完了条件

### 必須チェックリスト
- [x] Core層がPyO3に依存していない
- [x] 全モデルのコア実装完了
- [x] ユニットテスト合格率100%
- [x] ベンチマーク完了
- [x] コード品質チェック合格

### パフォーマンス基準
- [x] 単一計算: Phase 0のベースライン±5%
- [x] バッチ処理: Phase 0のベースライン±5%
- [x] メモリ使用量: 増加なし

## 成果物

### コード成果物
```
core/
├── Cargo.toml
├── src/
│   ├── lib.rs
│   ├── models/
│   │   ├── black_scholes.rs
│   │   ├── black76.rs
│   │   ├── merton.rs
│   │   └── american.rs
│   ├── math/
│   ├── traits/
│   └── error.rs
├── tests/
└── benchmarks/
```

### ドキュメント成果物
- Core API仕様書
- 移行レポート

## リスクと対策

| リスク | 対策 |
|--------|------|
| PyO3依存の見落とし | コンパイルエラーで検出 |
| パフォーマンス劣化 | 継続的ベンチマーク |
| API設計の不備 | Phase 2で調整可能 |

## Phase 2への引き継ぎ

### 提供物
1. 完全に独立したCore層
2. Core APIドキュメント
3. テストスイート

### 注意事項
- Core層は一切のPython依存を持たない
- すべての機能は純粋Rustで実装
- Phase 2でラッパーを作成予定
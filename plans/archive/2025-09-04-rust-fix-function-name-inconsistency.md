# [Rust] Black76/Merton/American関数名不整合修正 実装計画

## メタデータ
- **作成日**: 2025-09-04
- **言語**: Rust
- **ステータス**: COMPLETED
- **推定規模**: 小
- **推定コード行数**: 40行（属性追加のみ）
- **対象モジュール**: bindings/python/src/models.rs, bindings/python/src/lib.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 40行
- [ ] 新規ファイル数: 0個
- [x] 影響範囲: 単一モジュール（PyO3バインディング層のみ）
- [x] PyO3バインディング: 必要（メイン対象）
- [ ] SIMD最適化: 不要
- [ ] 並列化: 不要

### 規模判定結果
**小規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（小規模）
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| pytest（Python側） | ✅ | `pytest tests/` |

## 問題分析

### 現在の状況
現在、PyO3バインディングで関数名に不整合があります：

| モジュール | Rust関数名 | Python側での期待 | 現在の対処 |
|-----------|-----------|-----------------|------------|
| Black-Scholes | `call_price` | `call_price` | ✅ 正常 |
| Black76 | `black76_call_price` | `call_price` | ❌ Python側でエイリアス |
| Merton | `merton_call_price` | `call_price` | ❌ Python側でエイリアス |
| American | `american_call_price` | `call_price` | ❌ Python側でエイリアス |

### 現在のワークアラウンド
`bindings/python/python/quantforge/__init__.py`に46行のハッキーなエイリアス作成コード：
```python
# Black76用エイリアス（11行）
if hasattr(black76, "black76_call_price"):
    black76.call_price = black76.black76_call_price
# ... 他の関数も同様

# Merton用エイリアス（12行）  
# American用エイリアス（18行）
```

## 実装計画

### Phase 1: 実装（30分）

#### 1.1 Black76関数の修正
`bindings/python/src/models.rs`の以下の関数に`#[pyo3(name = "...")]`属性を追加：

```rust
// 行470-474
#[pyfunction]
#[pyo3(name = "call_price")]  // 追加
pub fn black76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64>

// 行477-481
#[pyfunction]
#[pyo3(name = "put_price")]   // 追加
pub fn black76_put_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64>

// 同様に以下の関数も修正:
// - black76_greeks → greeks
// - black76_implied_volatility → implied_volatility
// - black76_call_price_batch → call_price_batch
// - black76_put_price_batch → put_price_batch
// - black76_greeks_batch → greeks_batch
// - black76_implied_volatility_batch → implied_volatility_batch
```

#### 1.2 Merton関数の修正
同様に`#[pyo3(name = "...")]`属性を追加：
- merton_call_price → call_price
- merton_put_price → put_price
- merton_greeks → greeks
- merton_implied_volatility → implied_volatility
- merton_call_price_batch → call_price_batch
- merton_put_price_batch → put_price_batch
- merton_greeks_batch → greeks_batch
- merton_implied_volatility_batch → implied_volatility_batch

#### 1.3 American関数の修正
同様に`#[pyo3(name = "...")]`属性を追加：
- american_call_price → call_price
- american_put_price → put_price
- american_greeks → greeks
- american_implied_volatility → implied_volatility
- american_binomial → binomial_tree
- american_call_price_batch → call_price_batch
- american_put_price_batch → put_price_batch
- american_greeks_batch → greeks_batch
- american_implied_volatility_batch → implied_volatility_batch

#### 1.4 Python側のクリーンアップ
`bindings/python/python/quantforge/__init__.py`から以下を削除：
- 行6-17: Black76のエイリアス作成コード（11行）
- 行19-31: Mertonのエイリアス作成コード（12行）
- 行33-51: Americanのエイリアス作成コード（18行）

合計46行のハッキーなコードを削除してクリーンな実装に。

### Phase 2: 品質チェック（15分）

```bash
# Rustビルド
cd bindings/python
maturin develop --release

# Rust側のチェック
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --lib --release

# Python側のチェック  
pytest tests/
```

### Phase 3: 完了確認（15分）
- [x] 全モジュールで一貫した関数名（call_price, put_price等） ✅
- [x] Python側のハッキーなエイリアスコード完全削除 ✅
- [x] 全テスト合格（pytest, cargo test） ✅
- [x] APIドキュメントとの整合性確認 ✅

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  # 既存の命名規則に完全準拠
  - name: "call_price"
    meaning: "コール価格計算"
    source: "naming_conventions.md#関数命名パターン"
  - name: "put_price"
    meaning: "プット価格計算"
    source: "naming_conventions.md#関数命名パターン"
  - name: "greeks"
    meaning: "全グリークス計算"
    source: "naming_conventions.md#関数命名パターン"
  - name: "implied_volatility"
    meaning: "インプライドボラティリティ逆算"
    source: "naming_conventions.md#関数命名パターン"
  - name: "binomial_tree"
    meaning: "二項ツリー計算（American専用）"
    source: "既存実装（american.binomial_tree）"
```

### 4.2 新規提案命名
なし（既存の命名規則に完全準拠）

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認（Black-Scholesと同じパターン）
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義（既存通り）
- [x] APIパラメータは省略形を使用（f, k, t, r, sigma等）
- [x] エラーメッセージでもAPI名を使用

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 後方互換性 | 低 | ユーザーゼロ、破壊的変更推奨 |
| テスト失敗 | 低 | 関数名変更のみ、ロジック変更なし |

## チェックリスト

### 実装前
- [x] 既存コードの確認（Black-Scholes実装パターン）
- [x] 影響範囲の確認（PyO3バインディング層のみ）
- [x] Critical Rules確認（C004: 理想実装ファースト）

### 実装中
- [x] 各モジュールごとにテスト実行 ✅
- [x] コミット前の`cargo fmt` ✅
- [x] 段階的な動作確認 ✅

### 実装後
- [x] 全品質ゲート通過 ✅
- [x] Python側のハッキーコード完全削除確認 ✅
- [x] ドキュメントとの整合性確認 ✅
- [x] 計画のarchive移動 ✅

## 成果物

- [x] 修正済みRustバインディング（bindings/python/src/models.rs） ✅
- [x] クリーンなPython初期化（bindings/python/python/quantforge/__init__.py） ✅
- [x] テスト全合格（既存テストで動作確認） ✅
- [x] 一貫性のあるAPI（全モジュール統一） ✅

## 備考

このリファクタリングはCritical Rules C004（理想実装ファースト）とC013（破壊的リファクタリング推奨）に完全準拠。ハッキーなワークアラウンドを削除し、クリーンで保守性の高い実装を実現します。

関連:
- Critical Rules: C004（理想実装ファースト）、C013（破壊的リファクタリング推奨）
- 命名規則: docs/ja/internal/naming_conventions.md
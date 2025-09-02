# [Rust] pyo3-arrow真のゼロコピー実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 削除689行、新規250行
- **対象モジュール**: bindings/python/src/

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 削除689行、新規250行
- [x] 新規ファイル数: 1個（arrow_native.rs完全書き換え）
- [x] 影響範囲: 複数モジュール（lib.rs、arrow関連全ファイル）
- [x] PyO3バインディング: 必要（pyo3-arrow使用）
- [x] SIMD最適化: 不要
- [x] 並列化: 既存のcore実装を活用

### 規模判定結果
**大規模タスク**（レガシーコード一掃を含む）

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all --release` |
| cargo clippy | ✅ | `cargo clippy --all-targets --all-features -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --all --check` |
| similarity-rs | ✅ | `similarity-rs --threshold 0.80 bindings/python/src/` |
| rust-refactor.md | ✅ | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | ✅ | `cargo bench` |
| valgrind | 推奨 | `valgrind --leak-check=full` |

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間"
    source: "naming_conventions.md#共通パラメータ"
  - name: "r"
    meaning: "無リスク金利"
    source: "naming_conventions.md#共通パラメータ"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # pyo3-arrowの標準名（PyArray等）を使用
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装フェーズ

### Phase 1: 設計フェーズ（1日）
- [ ] レガシーコードの完全削除計画
  - [ ] arrow_convert.rs（140行）- NumPy変換ユーティリティ
  - [ ] arrow_native.rs（355行）- to_numpy()使用の旧実装
  - [ ] arrow_native_true.rs（194行）- PyList経由の実装
- [ ] pyo3-arrow APIの詳細調査
- [ ] 新arrow_native.rsのアーキテクチャ設計
- [ ] エラーハンドリング設計

### Phase 2: 段階的実装（3日）

#### マイルストーン1: レガシーコード削除（4時間）
- [ ] arrow_convert.rs 完全削除
- [ ] arrow_native_true.rs 完全削除
- [ ] arrow_native.rs 内容クリア（ファイルは保持）
- [ ] lib.rsからarrow_native_true参照削除
- [ ] **中間ビルドチェック**（エラー確認）

#### マイルストーン2: pyo3-arrow実装（8時間）
- [ ] 依存関係追加
  ```toml
  [dependencies]
  pyo3-arrow = "0.5"  # 最新バージョン確認
  # numpy関連の依存削除
  ```
- [ ] 新arrow_native.rs実装
  ```rust
  use pyo3_arrow::{PyArray, PyArrayMethods};
  use quantforge_core::compute::black_scholes::BlackScholes;
  
  #[pyfunction]
  #[pyo3(name = "arrow_call_price")]
  pub fn arrow_call_price(
      py: Python,
      spots: PyArray,
      strikes: PyArray,
      times: PyArray,
      rates: PyArray,
      sigmas: PyArray,
  ) -> PyResult<PyObject>
  ```
- [ ] 全Black-Scholes関数実装
  - [ ] arrow_call_price
  - [ ] arrow_put_price
  - [ ] arrow_greeks（必要に応じて）
- [ ] **similarity-rs実行**（重複チェック）

#### マイルストーン3: 統合と最適化（4時間）
- [ ] lib.rs更新（新実装の登録）
- [ ] NumPy互換レイヤー削除
  - [ ] call_price_native削除
  - [ ] put_price_native削除
- [ ] パフォーマンステスト作成
- [ ] メモリリークチェック

### Phase 3: 統合テスト（1日）
- [ ] Python側テストスクリプト作成
- [ ] パフォーマンス測定
  - [ ] 10,000要素: 目標 < 150μs
  - [ ] 100,000要素: 目標 < 500μs
  - [ ] 1,000,000要素: 目標 < 5,000μs
- [ ] メモリ使用量確認（ゼロコピー検証）
- [ ] 既存テストとの互換性確認

### Phase 4: リファクタリングフェーズ（必須: 1日）
- [ ] **rust-refactor.md 完全適用**
- [ ] similarity-rs で最終確認
- [ ] コード整理と最適化
- [ ] ドキュメント完成
- [ ] 不要なuse文、依存関係の削除

## 技術要件

### 必須要件
- [x] **レガシーコード完全削除**（NumPy、PyList関連すべて）
- [x] **真のゼロコピー実装**（pyo3-arrow使用）
- [x] **NumPy非依存**（純粋なArrow FFI）
- [x] メモリ安全性（unsafe最小化）
- [x] スレッド安全性（Send + Sync）
- [x] PyArrow/Polars/NumPy自動互換（Buffer Protocol）

### パフォーマンス目標
- [ ] 10,000要素: < 150μs（現在280μs）
- [ ] 100,000要素: < 500μs（現在1,500μs）
- [ ] 1,000,000要素: < 5,000μs（現在14,600μs）
- [ ] メモリ使用量: 入力データの1.0倍（ゼロコピー）

### PyO3連携
- [x] pyo3-arrow経由での自動変換
- [x] GIL解放での並列処理
- [x] Buffer Protocol自動対応

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| pyo3-arrowバージョン互換性 | 中 | バージョン固定、CI/CDでテスト |
| 既存APIとの互換性 | 高 | 関数名、パラメータ名を維持 |
| パフォーマンス未達 | 低 | pyo3-arrowは実績あり |

## 依存関係の更新

### 削除する依存関係
```toml
# 削除
numpy = "0.25"  # 不要になる
```

### 追加する依存関係
```toml
[dependencies]
pyo3-arrow = "0.5"  # または最新バージョン
```

### 既存依存関係（維持）
```toml
arrow = { version = "56.0", features = ["ffi", "pyarrow"] }
arrow-array = "56.0"
arrow-buffer = "56.0"
```

## チェックリスト

### 実装前
- [x] レガシーコードの特定完了
- [x] pyo3-arrow APIドキュメント確認

### 実装中
- [ ] 定期的なテスト実行
- [ ] コミット前の`cargo fmt`
- [ ] 段階的な動作確認
- [ ] レガシーコード削除の確認

### 実装後
- [ ] 全品質ゲート通過
- [ ] パフォーマンステスト結果記録
- [ ] メモリ使用量1.0倍確認（ゼロコピー）
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 新実装コード（bindings/python/src/arrow_native.rs）
- [ ] 削除済みレガシーコード（689行）
- [ ] パフォーマンステスト結果
- [ ] 技術文書（pyo3-arrow統合の詳細）

## 実装の具体的内容

### 新arrow_native.rs（簡潔版）
```rust
//! Arrow Native Module - True Zero-Copy via pyo3-arrow
//!
//! NumPy依存を完全排除し、純粋なArrow FFIで実装

use pyo3::prelude::*;
use pyo3_arrow::{PyArray, error::PyArrowResult};
use quantforge_core::compute::black_scholes::BlackScholes;

/// Black-Scholes call price - 真のゼロコピー実装
#[pyfunction]
#[pyo3(name = "arrow_call_price")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn arrow_call_price(
    py: Python,
    spots: PyArray,    // 自動ゼロコピー変換
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    // GIL解放して計算（Send制約解決済み）
    let result = py.allow_threads(|| {
        BlackScholes::call_price(
            spots.as_ref(),
            strikes.as_ref(),
            times.as_ref(),
            rates.as_ref(),
            sigmas.as_ref(),
        )
    })?;
    
    // ゼロコピーで返却
    Ok(PyArray::from_array_ref(result).to_arro3(py)?)
}

/// Black-Scholes put price - 真のゼロコピー実装
#[pyfunction]
#[pyo3(name = "arrow_put_price")]
#[pyo3(signature = (spots, strikes, times, rates, sigmas))]
pub fn arrow_put_price(
    py: Python,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyArrowResult<PyObject> {
    let result = py.allow_threads(|| {
        BlackScholes::put_price(
            spots.as_ref(),
            strikes.as_ref(),
            times.as_ref(),
            rates.as_ref(),
            sigmas.as_ref(),
        )
    })?;
    
    Ok(PyArray::from_array_ref(result).to_arro3(py)?)
}

/// モジュール登録
pub fn register_arrow_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(arrow_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_put_price, m)?)?;
    Ok(())
}
```

### lib.rs更新（簡潔版）
```rust
//! Python bindings for QuantForge - pyo3-arrow implementation

use pyo3::prelude::*;

mod arrow_native;  // 新実装のみ（レガシー削除）
mod error;
mod models;

use models::*;

#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Arrow Native Module（真のゼロコピー）
    let arrow_module = PyModule::new(m.py(), "arrow_native")?;
    arrow_native::register_arrow_functions(&arrow_module)?;
    
    m.add_submodule(&arrow_module)?;
    
    // 既存モジュール（Black-Scholes等）は維持
    // ...
    
    Ok(())
}
```

## 備考

- **破壊的変更**: レガシーコード689行を完全削除
- **理想実装**: pyo3-arrowによる真のゼロコピー実現
- **NumPy非依存**: 純粋なArrow FFIのみ使用
- **パフォーマンス**: 100,000要素で70%以上の改善見込み
- **コード削減**: 689行→250行（64%削減）
- **保守性向上**: pyo3-arrowが複雑なFFI処理を隠蔽
- **互換性**: PyArrow、Polars、NumPyすべてと自動互換
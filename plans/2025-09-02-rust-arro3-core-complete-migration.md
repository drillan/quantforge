# [Rust] arro3-core完全移行による真のゼロコピー実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 削除689行、新規200行
- **対象モジュール**: bindings/python/src/全体

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 889行（削除+新規）
- [x] 新規ファイル数: 1個（arrow_native.rs完全置換）
- [x] 影響範囲: 全体（レガシーコード完全削除）
- [x] PyO3バインディング: 必要（pyo3-arrow + arro3-core）
- [x] SIMD最適化: 不要
- [x] 並列化: 既存のcore実装を活用

### 規模判定結果
**大規模タスク**（破壊的変更による完全再実装）

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
| miri | 推奨 | `cargo +nightly miri test` |

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
proposed_names: []  # pyo3-arrow/arro3標準のPyArrayを使用
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装フェーズ

### Phase 1: 設計フェーズ（1日）
- [ ] **破壊的削除リスト作成**
  - [ ] arrow_convert.rs - 完全削除（140行）
  - [ ] arrow_native.rs - 完全削除（355行）
  - [ ] arrow_native_true.rs - 完全削除（194行）
- [ ] arro3-core API調査
- [ ] ライフタイム問題の回避策設計
- [ ] エラーハンドリング戦略

### Phase 2: 段階的実装（3-5日）

#### マイルストーン1: 完全破壊（2時間）
- [ ] **git branch -b feature/arro3-complete-migration**
- [ ] レガシーファイル完全削除
  ```bash
  rm bindings/python/src/arrow_convert.rs
  rm bindings/python/src/arrow_native_true.rs
  > bindings/python/src/arrow_native.rs  # 空にする
  ```
- [ ] lib.rs簡潔化（arrow_native_true削除）
- [ ] **中間ビルドエラー確認**（正常）

#### マイルストーン2: arro3-core実装（8時間）
- [ ] 依存関係更新
  ```toml
  [dependencies]
  pyo3 = "0.25.1"
  pyo3-arrow = "0.11.0"
  arrow = "56.0"
  # numpy削除！
  ```
- [ ] 新arrow_native.rs実装
  ```rust
  use pyo3::prelude::*;
  use pyo3_arrow::{PyArray, error::PyArrowResult};
  use std::sync::Arc;
  
  #[pyfunction]
  pub fn arrow_call_price(
      py: Python,
      spots: PyArray,
      strikes: PyArray,
      times: PyArray,
      rates: PyArray,
      sigmas: PyArray,
  ) -> PyArrowResult<PyObject>
  ```
- [ ] ライフタイム回避策実装
  ```rust
  // Arc使用でライフタイム解決
  let py_array = Arc::new(PyArray::from_array_ref(result));
  Ok(py_array.to_arro3(py)?)
  ```
- [ ] **similarity-rs実行**（重複ゼロ確認）

#### マイルストーン3: 統合最適化（4時間）
- [ ] lib.rs最小化
- [ ] 不要な依存関係削除
- [ ] メモリリークチェック（valgrind）
- [ ] GIL解放確認

### Phase 3: 統合テスト（1日）
- [ ] Python側テスト作成
  ```python
  import arro3.core as ar
  # pyarrow不要！
  
  spots = ar.array([100.0] * 10000)
  result = quantforge.arrow_native.arrow_call_price(spots, ...)
  ```
- [ ] パフォーマンス測定
  - [ ] 10,000要素: 目標 < 100μs
  - [ ] 100,000要素: 目標 < 400μs
  - [ ] 1,000,000要素: 目標 < 4,000μs
- [ ] メモリ使用量確認（1.0倍確認）

### Phase 4: リファクタリングフェーズ（必須: 1日）
- [ ] **rust-refactor.md 完全適用**
- [ ] similarity-rs最終確認
- [ ] コード整理
- [ ] ドキュメント完成
- [ ] 計画のarchive移動

## 技術要件

### 必須要件
- [x] **完全破壊的変更**（レガシー689行削除）
- [x] **arro3-core使用**（pyarrow不要、135MB削減）
- [x] **真のゼロコピー**（Arrow PyCapsule Interface）
- [x] **NumPy完全排除**（依存関係からも削除）
- [x] **Arrow非ネイティブ型への変換禁止**（NumPy、PyList等への変換は一切行わない）
- [x] メモリ安全性（unsafe最小化）
- [x] スレッド安全性（Send + Sync）

### パフォーマンス目標
- [ ] 10,000要素: < 100μs（現在280μs、64%改善）
- [ ] 100,000要素: < 400μs（現在1,500μs、73%改善）
- [ ] 1,000,000要素: < 4,000μs（現在14,600μs、73%改善）
- [ ] メモリ使用量: 1.0倍（ゼロコピー達成）
- [ ] ライブラリサイズ: 7MB（pyarrow 135MB → 95%削減）

### PyO3連携
- [x] pyo3-arrow経由での自動変換
- [x] arro3-coreへのto_arro3()出力
- [x] ライフタイム問題のArc回避
- [x] GIL解放での並列処理

## 実装中止条件（Critical Stop Points）

### 🛑 即座に実装を中止する条件
以下のいずれかが発生した場合、実装を即座に中止し、計画を見直す：

1. **Arrow非ネイティブ型への変換が必要になった場合**
   - NumPy配列への変換（`to_numpy()`、`PyArray1`使用）
   - PyListへの変換（`to_pylist()`使用）
   - その他のPythonネイティブ型への変換
   - **判定**: これらが必要になった時点で「真のArrowネイティブ」ではない

2. **ゼロコピーが実現できない場合**
   - `slice.to_vec()`の使用が必要
   - メモリコピーが避けられない実装
   - **判定**: メモリコピーが発生した時点で失敗

3. **pyo3-arrowのto_arro3()が動作しない場合**
   - ライフタイム問題が解決できない
   - Arc/Box回避策でも動作しない
   - **判定**: 3つ以上の回避策を試しても動作しない場合

4. **arro3-coreの致命的制限が判明した場合**
   - 必要な機能が未実装
   - パフォーマンスが現状より劣化
   - **判定**: ベンチマークで現状の50%以下の性能

### 中止時のアクション
1. 実装を即座に停止
2. 問題点を文書化
3. 代替案を検討（直接FFI実装など）
4. 計画をCANCELLEDとしてarchive

## リスクと対策

| リスク | 影響度 | 対策 | 中止トリガー |
|--------|--------|------|-------------|
| ライフタイム問題 | 高 | Arc/Box使用で回避実装済み | 3つ以上の回避策失敗 |
| arro3-core成熟度 | 中 | 十分なテスト、活発な開発コミュニティ | 必須機能未実装 |
| NumPy変換の誘惑 | 高 | 絶対禁止、発見次第中止 | 使用した時点で即中止 |
| パフォーマンス未達 | 低 | ゼロコピー実現で理論的に最速 | 50%以下の性能で中止 |

## 依存関係の更新

### 削除する依存関係
```toml
# 完全削除
numpy = "0.25"      # 削除！
ndarray = "0.16"    # 削除！
```

### 維持する依存関係
```toml
[dependencies]
pyo3 = "0.25.1"
pyo3-arrow = "0.11.0"
arrow = { version = "56.0", features = ["ffi", "pyarrow"] }
arrow-array = "56.0"
arrow-buffer = "56.0"
```

### Python側要件
```python
# requirements.txt
arro3-core>=0.5.1  # 7MB、軽量
# pyarrowは不要！（135MB削減）
```

## チェックリスト

### 実装前
- [x] レガシーコード特定完了（689行）
- [x] arro3-core API調査完了
- [ ] 破壊的変更の決断

### 実装中
- [ ] レガシー完全削除確認
- [ ] テスト随時実行
- [ ] コミット前の`cargo fmt`
- [ ] ライフタイム回避策の動作確認

### 実装後
- [ ] 全品質ゲート通過
- [ ] パフォーマンス70%以上改善確認
- [ ] メモリ使用量1.0倍確認
- [ ] ライブラリサイズ95%削減確認
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 新実装（bindings/python/src/arrow_native.rs、200行）
- [ ] 削除済みレガシー（689行完全削除）
- [ ] パフォーマンステスト結果（70%改善）
- [ ] 技術文書（arro3-core統合）

## 実装の具体的内容

### 新arrow_native.rs（ライフタイム回避版）
```rust
//! Arrow Native Module - arro3-core Zero-Copy Implementation
//!
//! 重要: NumPy/PyList等への変換は絶対禁止
//! Arrow非ネイティブ型への変換を検出した場合、実装を即座に中止すること

use pyo3::prelude::*;
use pyo3_arrow::{PyArray, error::PyArrowResult};
use quantforge_core::compute::black_scholes::BlackScholes;
use arrow::datatypes::{DataType, Field};
use std::sync::Arc;

// 禁止事項の明示
// - use numpy::* は絶対禁止
// - PyList使用禁止
// - to_numpy()、to_pylist()呼び出し禁止

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
    // GIL解放して計算
    let result = py.allow_threads(|| {
        BlackScholes::call_price(
            spots.as_ref(),
            strikes.as_ref(),
            times.as_ref(),
            rates.as_ref(),
            sigmas.as_ref(),
        )
    })?;
    
    // ライフタイム回避: Arcで所有権共有
    let field = Arc::new(Field::new("call_price", DataType::Float64, false));
    let py_array = Arc::new(PyArray::from_array_ref(result, field));
    
    // arro3-coreに返却（ゼロコピー）
    Ok(py_array.to_arro3(py)?)
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
    
    let field = Arc::new(Field::new("put_price", DataType::Float64, false));
    let py_array = Arc::new(PyArray::from_array_ref(result, field));
    
    Ok(py_array.to_arro3(py)?)
}

/// モジュール登録（簡潔）
pub fn register_arrow_functions(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(arrow_call_price, m)?)?;
    m.add_function(wrap_pyfunction!(arrow_put_price, m)?)?;
    Ok(())
}
```

### Python側使用例
```python
import arro3.core as ar
# import pyarrow as pa  # 不要！135MB削減！
import quantforge

# arro3-coreで直接作成（7MB）
spots = ar.array([100.0] * 100_000)
strikes = ar.array([105.0] * 100_000)
times = ar.array([1.0] * 100_000)
rates = ar.array([0.05] * 100_000)
sigmas = ar.array([0.2] * 100_000)

# ゼロコピーで計算
result = quantforge.arrow_native.arrow_call_price(
    spots, strikes, times, rates, sigmas
)
# result: arro3.core.Array（軽量、高速）
```

## 備考

- **完全破壊的変更**: レガシー689行を跡形もなく削除
- **arro3-core採用**: pyarrow不要で135MB削減（95%削減）
- **真のゼロコピー**: Arrow PyCapsule Interfaceで実現
- **ライフタイム解決**: Arc使用で回避実装
- **パフォーマンス**: 理論的最速（70%以上改善見込み）
- **保守性向上**: コード689行→200行（71%削減）
- **理想実装**: 妥協なし、段階的移行なし、完成形のみ

## ⚠️ 絶対禁止事項

以下のいずれかを使用・実装した時点で、この計画は**即座に中止**：

1. **NumPy関連**
   - `numpy::*`のインポート
   - `PyArray1`、`PyArrayMethods`の使用
   - `to_numpy()`メソッドの呼び出し
   - NumPy配列への変換処理

2. **PyList関連**
   - `to_pylist()`メソッドの呼び出し
   - `PyList::new()`の使用
   - Pythonリストへの変換処理

3. **メモリコピー**
   - `slice.to_vec()`の使用
   - `Vec::from(slice)`の使用
   - その他のコピー操作

4. **妥協実装**
   - 「一時的に」NumPy経由
   - 「とりあえず」PyList使用
   - 「後で改善」前提のコード

**これらは技術的負債であり、「Arrowネイティブ」の定義に反する。**
**発見次第、実装を中止し、代替案（直接FFI実装等）を検討すること。**
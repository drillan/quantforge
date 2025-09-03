# [Rust] Arrow FFI ゼロコピー実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 300-400
- **対象モジュール**: bindings/python/src/arrow_native_true.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 300-400 行
- [x] 新規ファイル数: 0 個（既存ファイルの修正）
- [x] 影響範囲: 単一モジュール（arrow_native_true.rs）
- [x] PyO3バインディング: 必要
- [x] SIMD最適化: 不要
- [x] 並列化: 不要（既存の並列化を維持）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| similarity-rs | 条件付き | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | 条件付き | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | 推奨 | `cargo bench` |

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
proposed_names: []  # 新規命名なし、Arrow FFI標準の名前を使用
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装フェーズ

### Phase 1: 設計（2時間）
- [ ] Arrow FFI APIの詳細調査（arrow 56.0）
- [ ] PyCapsuleインターフェースの仕様確認
- [ ] メモリ管理戦略の決定
- [ ] エラーハンドリング設計

### Phase 2: 実装（4-6時間）

#### 2.1 Python→Rust方向の実装
- [ ] `pyarrow_to_arrow_direct`関数の置換
  - [ ] PyCapsule経由でFFI構造体ポインタ取得
  - [ ] arrow::ffiを使用したゼロコピー変換
  - [ ] エラーハンドリングとバリデーション
  - [ ] メモリ安全性の確保

#### 2.2 Rust→Python方向の実装
- [ ] `arrow_to_pyarrow_direct`関数の置換
  - [ ] ArrayRefをFFI構造体にエクスポート
  - [ ] PyCapsuleでのラップ
  - [ ] デストラクタによるメモリ管理
  - [ ] PyArrowオブジェクトの生成

#### 2.3 既存関数の更新
- [ ] `arrow_call_price_true`の更新
- [ ] `arrow_put_price_true`の更新
- [ ] NumPy経由のコードを完全削除
  - [ ] `numpy::{IntoPyArray, PyArray1, PyArrayMethods}`のuse文削除
  - [ ] `to_numpy()`呼び出しの完全削除
  - [ ] NumPy配列への変換・参照を全て削除

### Phase 3: 品質チェック（1時間）
```bash
# 基本チェック
cargo test --all --release
cargo clippy --all-targets --all-features -- -D warnings
cargo fmt --check

# 重複チェック
similarity-rs --threshold 0.80 --skip-test bindings/python/src/

# ビルドとインストール
uv run maturin develop --release
```

### Phase 4: テストと検証（2時間）
- [ ] 単体テスト作成
  - [ ] 小規模データ（1,000要素）
  - [ ] 中規模データ（10,000要素）
  - [ ] 大規模データ（100,000要素）
- [ ] メモリリークチェック（valgrind）
- [ ] パフォーマンステスト
  - [ ] 既存実装との比較
  - [ ] メモリコピーの削減確認

## 技術要件

### 必須要件
- [x] ゼロコピー実装（`slice.to_vec()`の完全排除）
- [x] **NumPyデータ型の完全排除**（PyArray1、numpy::*を一切使用しない）
- [x] メモリ安全性（Rust保証 + unsafe最小化）
- [x] スレッド安全性（Send + Sync）
- [x] PyArrow互換性（__arrow_c_array__プロトコル）

### パフォーマンス目標
- [ ] 10,000要素: < 180 μs（現在280μs）
- [ ] 100,000要素: < 750 μs（現在1,500μs）
- [ ] メモリ使用量: 入力データの1.0倍（現在2.0倍）

### PyO3連携
- [x] FFI経由でのゼロコピー実装
- [x] GIL解放での並列処理維持
- [x] 適切なエラー変換

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Arrow API互換性 | 高 | arrow 56.0の実際のAPIを確認、必要に応じてバージョン固定 |
| unsafe操作のバグ | 高 | 最小限のunsafe使用、十分なテストカバレッジ |
| PyCapsuleライフタイム | 中 | デストラクタで確実な解放、参照カウント管理 |
| PyArrowバージョン依存 | 中 | バージョンチェックとフォールバック機構 |

## 依存関係の調整

### 現在の依存関係（確認済み）
```toml
# arrow関連（Cargo.tomlで確認）
arrow = { version = "56.0", features = ["ffi", "pyarrow"] }
arrow-array = "56.0"
arrow-buffer = "56.0"
```

### 追加が必要な可能性
```toml
# 必要に応じて追加
arrow-data = "56.0"  # ArrayData型が別クレートの場合
arrow-schema = "56.0"  # スキーマ処理が別クレートの場合
```

## チェックリスト

### 実装前
- [x] 既存コードの確認（arrow_native.rs, arrow_native_true.rs）
- [x] 依存関係の確認（Cargo.toml）
- [x] Arrow 56.0 APIドキュメントの確認

### 実装中
- [ ] 定期的なテスト実行
- [ ] コミット前の`cargo fmt`
- [ ] unsafe箇所のコメント記載

### 実装後
- [ ] 全品質ゲート通過
- [ ] パフォーマンステスト結果記録
  - [ ] 50%以上の性能改善確認（100,000要素）
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 実装コード（bindings/python/src/arrow_native_true.rs）
- [ ] テストコード（test_arrow_native_comparison.py の拡張）
- [ ] パフォーマンス測定結果
- [ ] 技術文書（Arrow FFI実装の詳細）

## 実装の具体的内容

### 重要な原則
**この実装ではNumPyを一切使用しません。Arrow FFIを通じた直接的なデータ交換のみを行います。**

### pyarrow_to_arrow_direct（Python→Rust）
```rust
use arrow::array::{make_array, ArrayRef};
use arrow::ffi::{FFI_ArrowArray, FFI_ArrowSchema};
use arrow_data::ArrayData;
use pyo3::types::PyCapsule;
// NumPy関連のuseは一切なし

fn pyarrow_to_arrow_direct(py_array: &Bound<'_, PyAny>) -> PyResult<ArrayRef> {
    // 1. __arrow_c_array__ プロトコルの確認
    if !py_array.hasattr("__arrow_c_array__")? {
        return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "Input is not a PyArrow array or does not support the C Data Interface.",
        ));
    }

    // 2. PyCapsuleからFFI構造体ポインタ取得
    let capsule_tuple = py_array.call_method0("__arrow_c_array__")?;
    let (array_capsule, schema_capsule) = capsule_tuple.extract::<(&Bound<PyCapsule>, &Bound<PyCapsule>)>()?;
    
    let array_ptr = array_capsule.pointer::<FFI_ArrowArray>();
    let schema_ptr = schema_capsule.pointer::<FFI_ArrowSchema>();

    // 3. ArrayData::try_from_ffi でゼロコピー変換
    let array_data = unsafe {
        let schema = std::ptr::read(schema_ptr);
        let array = std::ptr::read(array_ptr);
        ArrayData::try_from_ffi(array, &schema)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!("Failed to import from FFI: {}", e)))?
    };

    // 4. make_array でArrayRef生成
    Ok(arrow::array::make_array(array_data))
}
```

### arrow_to_pyarrow_direct（Rust→Python）
```rust
fn arrow_to_pyarrow_direct(py: Python, array: ArrayRef) -> PyResult<PyObject> {
    // 1. ArrayDataをFFI構造体にエクスポート
    let (ffi_array, ffi_schema) = array.to_data().clone().to_ffi()
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Failed to export to FFI: {}", e)))?;
    
    // FFI構造体をヒープに確保
    let array_ptr = Box::into_raw(Box::new(ffi_array));
    let schema_ptr = Box::into_raw(Box::new(ffi_schema));

    // 2. PyCapsuleでラップ（デストラクタ付き）
    let array_capsule = PyCapsule::new_with_destructor(py, array_ptr, |ptr| {
        let _ = unsafe { Box::from_raw(ptr as *mut FFI_ArrowArray) };
    })?;
    let schema_capsule = PyCapsule::new_with_destructor(py, schema_ptr, |ptr| {
        let _ = unsafe { Box::from_raw(ptr as *mut FFI_ArrowSchema) };
    })?;

    // 3. pyarrow.Array._import_from_c で生成
    let pa = py.import_bound("pyarrow")?;
    let pa_array_cls = pa.getattr("Array")?;
    let py_array = pa_array_cls.call_method1("_import_from_c", (array_capsule, schema_capsule))?;
    
    Ok(py_array.into())
}
```

## 備考

- 現在の実装では`slice.to_vec()`でメモリコピーが発生している
- 提案実装により100,000要素で約50%の性能改善が期待される
- Arrow C Data Interfaceは業界標準のため、長期的な互換性も確保される
- 実装完了後は`arrow_native.rs`の旧実装を削除し、`arrow_native_true.rs`を正式版とする
- この実装により、"Arrow Native"という名前にふさわしい真のゼロコピー実装が実現される
- **重要**: NumPyデータ型（PyArray1、numpy::*）は一切使用しない。純粋なArrow FFIのみを使用することで、不要な依存関係と変換オーバーヘッドを完全に排除する
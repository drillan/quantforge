# [Rust] Arrow Zero-Copy FFI 実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 800-1000
- **対象モジュール**: bindings/python/src/models.rs, bindings/python/src/arrow_native.rs, python/quantforge/

## タスク規模判定

### 判定基準
- [ ] 推定コード行数: 800-1000 行
- [ ] 新規ファイル数: 0 個（削除1個、既存変更3個）
- [ ] 影響範囲: 複数モジュール（PyO3バインディング全体）
- [ ] PyO3バインディング: 必要（メインタスク）
- [ ] SIMD最適化: 不要
- [ ] 並列化: 既存実装を維持

### 規模判定結果
**大規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | ✅ | ✅ | ✅ | `cargo test --all` |
| cargo clippy | ✅ | ✅ | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | ✅ | ✅ | `cargo fmt --check` |
| similarity-rs | - | 条件付き | ✅ | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | - | 条件付き | ✅ | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | - | 推奨 | ✅ | `cargo bench` |
| miri（安全性） | - | - | 推奨 | `cargo +nightly miri test` |

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
  - name: "is_call"
    meaning: "コール/プットフラグ"
    source: "naming_conventions.md#共通パラメータ"
```

### 4.2 新規提案命名（必要な場合）
```yaml
proposed_names: []  # 新規命名なし（既存カタログで完全対応）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## フェーズ構成

### Phase 1: 設計フェーズ（完了）
- [x] 現状分析（メモリコピー箇所特定）
- [x] pyo3-arrow統合設計
- [x] エラーハンドリング設計
- [x] 互換性戦略（破壊的変更許可）

### Phase 2: 段階的実装（3-5日）

#### マイルストーン1: models.rs Arrow Native化
- [ ] **numpy_to_arrow_direct削除**
  ```rust
  // 現在（メモリコピー発生）
  fn numpy_to_arrow_direct(arr: PyReadonlyArray1<f64>) -> Result<Float64Array, ArrowError> {
      let slice = arr.as_slice()?;
      Ok(Float64Array::from(slice.to_vec()))  // ここでコピー
  }
  
  // 変更後（ゼロコピー）
  fn extract_arrow_array(py_array: PyArray) -> Result<Float64Array, ArrowError> {
      let array_ref = py_array.as_ref();
      array_ref.as_any()
          .downcast_ref::<Float64Array>()
          .ok_or_else(|| ArrowError::CastError("Expected Float64Array".into()))
          .map(|arr| arr.clone())  // Arc<dyn Array>のクローン（データコピーなし）
  }
  ```

- [ ] **arrayref_to_numpy削除**
  ```rust
  // 現在（メモリコピー発生）
  fn arrayref_to_numpy<'py>(py: Python<'py>, arr: ArrayRef) -> PyResult<Bound<'py, PyArray1<f64>>> {
      let vec: Vec<f64> = (0..float_array.len())
          .map(|i| float_array.value(i))
          .collect();  // ここでコピー
      Ok(PyArray1::from_vec(py, vec))
  }
  
  // 変更後（Arrow直接返却）
  fn wrap_array_result(py: Python, result: ArrayRef) -> PyArrowResult<PyObject> {
      let field = Arc::new(Field::new("result", DataType::Float64, false));
      let py_array = PyArray::new(result, field);
      py_array.to_arro3(py).map(|obj| obj.into())
  }
  ```

- [ ] **バッチ処理関数の変更**
  - call_price_batch: PyReadonlyArray1 → PyArray
  - put_price_batch: PyReadonlyArray1 → PyArray
  - greeks_batch: PyReadonlyArray1 → PyArray

- [ ] **中間品質チェック**
  ```bash
  cargo test --lib
  cargo clippy -- -D warnings
  similarity-rs --threshold 0.80 bindings/python/src/
  ```

#### マイルストーン2: Python API統合
- [ ] **black_scholes.py更新**
  ```python
  # 現在
  def call_price_batch(spots, strikes, times, rates, sigmas):
      spots = _ensure_array(spots)
      # NumPy配列として渡す
      return _native.call_price_batch(spots, strikes, times, rates, sigmas)
  
  # 変更後
  def call_price_batch(spots, strikes, times, rates, sigmas):
      import pyarrow as pa
      spots_arrow = pa.array(spots, type=pa.float64())
      # Arrow配列として渡す
      result = _native.call_price_batch(spots_arrow, ...)
      return result  # Arrow配列を直接返却
  ```

- [ ] **テスト更新**
  - Arrow配列での入出力テスト
  - パフォーマンステスト
  - 後方互換性テスト（不要だが念のため）

#### マイルストーン3: 統合とクリーンアップ
- [ ] **arrow_native.rs統合**
  - arrow_call_price → models.rsのcall_price_batchに統合
  - arrow_put_price → models.rsのput_price_batchに統合
  - arrow_greeks → models.rsのgreeks_batchに統合

- [ ] **arrow_native.rs削除**
  - ファイル削除（約400行）
  - lib.rsからのモジュール削除
  - __init__.pyからのインポート削除

- [ ] **バージョン更新**
  - Cargo.toml: 0.0.8
  - pyproject.toml: 0.0.8
  - CHANGELOG.md更新

### Phase 3: 統合テスト（1日）
- [ ] 全機能の統合テスト
  - E2Eテスト実行
  - パフォーマンステスト
  - メモリプロファイリング

### Phase 4: リファクタリングフェーズ（必須: 1日）
- [ ] **rust-refactor.md 完全適用**
- [ ] similarity-rs で最終確認
- [ ] コード整理と最適化
- [ ] ドキュメント完成

## 技術要件

### 必須要件
- [x] ゼロコピー実装（pyo3-arrow使用）
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）

### パフォーマンス目標
- [ ] メモリコピー削減: 3箇所 → 0箇所
- [ ] 処理速度向上: 30-50%改善
- [ ] メモリ使用量: 入力データの1.0倍（現在3倍）

### PyO3連携
- [x] pyo3-arrow使用によるゼロコピー
- [x] GIL解放での並列処理（既存維持）
- [x] 適切なエラー変換

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Arrow API破壊的変更 | 高 | ユーザーゼロなので問題なし |
| pyo3-arrow非互換 | 中 | arro3-coreフォールバック |
| パフォーマンス劣化 | 低 | ベンチマークで確認 |

## チェックリスト

### 実装前
- [x] 既存コードの確認（models.rs, arrow_native.rs）
- [x] 依存関係の確認（pyo3-arrow導入済み）
- [x] 設計レビュー（完了）

### 実装中
- [ ] 定期的なテスト実行
- [ ] コミット前の`cargo fmt`
- [ ] 段階的な動作確認

### 実装後
- [ ] 全品質ゲート通過
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 実装コード（bindings/python/src/models.rs）
- [ ] テストコード（tests/以下）
- [ ] ベンチマーク（benchmarks/以下）
- [ ] ドキュメント（rustdoc）
- [ ] PyO3バインディング（更新）

## 期待される改善

### 現在の問題
```
1. numpy_to_arrow_direct: slice.to_vec() でメモリコピー
2. arrayref_to_numpy: 値のcollect() でメモリコピー  
3. broadcast_to_length: vec![value; target_len] でメモリコピー
合計: 入力と出力で最大3回のメモリコピー
```

### 改善後
```
1. PyArrayを直接受け取り（ゼロコピー）
2. ArrayRefを直接返却（ゼロコピー）
3. Arrowネイティブbroadcasting（ゼロコピー）
合計: メモリコピー0回
```

### パフォーマンス影響
- 10,000要素: 245μs → 150μs（推定40%改善）
- 100,000要素: 2.4ms → 1.2ms（推定50%改善）
- メモリ使用量: 3倍 → 1倍

## 備考

- Critical Rules C004/C014遵守: 理想実装のみ、段階的移行なし
- 破壊的変更許可: ユーザーゼロのため完全な自由度
- arrow_native.rsは統合後削除（重複排除）
- NumPy互換性は後で必要になったら追加（現時点では不要）
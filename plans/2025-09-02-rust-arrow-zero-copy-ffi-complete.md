# [Rust] Arrow Zero-Copy FFI 完全移行実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: ACTIVE
- **推定規模**: 中
- **推定コード行数**: 200-300（追加分）
- **対象モジュール**: bindings/python/src/arrow_native.rs, bindings/python/src/models.rs, bindings/python/src/lib.rs
- **対象バージョン**: v0.0.9

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 200-300 行（追加実装）
- [x] 新規ファイル数: 0 個（リネームのみ）
- [x] 影響範囲: 複数モジュール（PyO3バインディング全体）
- [x] PyO3バインディング: 必要（メインタスク）
- [x] SIMD最適化: 不要
- [x] 並列化: 既存実装を維持

### 規模判定結果
**中規模タスク**

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
  - name: "f"
    meaning: "フォワード価格"
    source: "naming_conventions.md#Black76"
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Merton"
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

## フェーズ構成（中規模実装フェーズ）

### Phase 1: 設計（1時間）
- [x] インターフェース設計（完了）
- [x] データ構造定義（PyArrayベース確定）
- [x] エラー型定義（PyArrowResult使用）

### Phase 2: 実装（4-6時間）

#### コア機能実装
- [ ] **スカラー関数の追加**（arrow_native.rsに追加）
  ```rust
  #[pyfunction]
  pub fn call_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
      validate_inputs(s, k, t, r, sigma)?;
      Ok(black_scholes_call_scalar(s, k, t, r, sigma))
  }
  
  #[pyfunction]
  pub fn put_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
      validate_inputs(s, k, t, r, sigma)?;
      Ok(black_scholes_put_scalar(s, k, t, r, sigma))
  }
  
  #[pyfunction]
  pub fn greeks<'py>(
      py: Python<'py>,
      s: f64, k: f64, t: f64, r: f64, sigma: f64, is_call: bool
  ) -> PyResult<Bound<'py, PyDict>> {
      validate_inputs(s, k, t, r, sigma)?;
      let greeks = calculate_greeks(s, k, t, r, sigma, is_call);
      let dict = PyDict::new(py);
      dict.set_item("delta", greeks.delta)?;
      dict.set_item("gamma", greeks.gamma)?;
      dict.set_item("vega", greeks.vega)?;
      dict.set_item("theta", greeks.theta)?;
      dict.set_item("rho", greeks.rho)?;
      Ok(dict)
  }
  ```

- [ ] **Implied Volatility機能の追加**
  ```rust
  #[pyfunction]
  pub fn implied_volatility(
      price: f64, s: f64, k: f64, t: f64, r: f64, is_call: bool
  ) -> PyResult<f64> {
      // Newton-Raphson法実装
      implied_volatility_impl(price, s, k, t, r, is_call)
          .map_err(|e| PyValueError::new_err(e.to_string()))
  }
  
  #[pyfunction]
  pub fn arrow_implied_volatility(
      py: Python,
      prices: PyArray,
      spots: PyArray,
      strikes: PyArray,
      times: PyArray,
      rates: PyArray,
      is_calls: PyArray,
  ) -> PyArrowResult<PyObject> {
      // バッチ版実装
  }
  ```

- [ ] **検証なし高速版の追加**
  ```rust
  #[pyfunction]
  #[pyo3(name = "call_price_batch_no_validation")]
  pub fn call_price_batch_no_validation(
      py: Python,
      spots: PyArray,
      strikes: PyArray,
      times: PyArray,
      rates: PyArray,
      sigmas: PyArray,
  ) -> PyArrowResult<PyObject> {
      // 検証をスキップして直接計算
      // arrow_call_priceの内部実装を流用
  }
  ```

- [ ] **その他モデルの追加**
  ```rust
  #[pyfunction]
  pub fn black76_call_price(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> PyResult<f64> {
      validate_inputs(f, k, t, r, sigma)?;
      Ok(black76_call_scalar(f, k, t, r, sigma))
  }
  
  #[pyfunction]
  pub fn merton_call_price(
      s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64
  ) -> PyResult<f64> {
      validate_inputs(s, k, t, r, sigma)?;
      validate_positive(q, "q")?;
      Ok(merton_call_scalar(s, k, t, r, q, sigma))
  }
  
  #[pyfunction]
  pub fn american_call_price(
      s: f64, k: f64, t: f64, r: f64, sigma: f64
  ) -> PyResult<f64> {
      Err(PyNotImplementedError::new_err("American options not yet implemented"))
  }
  ```

#### ファイル統合
- [ ] **リネーム操作**
  1. models.rsのバックアップ作成
  2. arrow_native.rs → models.rsにリネーム
  3. 旧models.rsからロジックのみ参照（コピペは禁止）
     - 入力は必ずPyArray（ゼロコピー）で受け取る
     - PyReadonlyArray1のコードは一切持ち込まない
     - numpy_to_arrow_direct、arrayref_to_numpyは削除
  4. バックアップ削除

- [ ] **lib.rs更新**
  ```rust
  // 削除
  mod arrow_native;
  
  // 関数登録の整理
  black_scholes_module.add_function(wrap_pyfunction!(call_price, &black_scholes_module)?)?;
  black_scholes_module.add_function(wrap_pyfunction!(arrow_call_price, &black_scholes_module)?)?;
  // arrow_call_priceをcall_price_batchとしてもエクスポート
  ```

### Phase 3: 品質チェック（1時間）

```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック
similarity-rs --threshold 0.80 --skip-test bindings/python/src/
# 閾値超えの重複があれば rust-refactor.md 適用
```

### Phase 4: 最適化（必要に応じて）
- [ ] ベンチマーク実施
- [ ] ボトルネック特定
- [ ] 最適化実施

## 技術要件

### 必須要件
- [x] エラー率 < `src/constants.rs::EPSILON`（実務精度）
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）

### パフォーマンス目標
- [ ] 単一計算: < 10 ns
- [ ] バッチ処理: < 150 μs（10,000データ）
- [ ] メモリ使用量: 入力データの1.0倍以内

### PyO3連携
- [x] ゼロコピー実装（pyo3-arrow使用）
- [x] GIL解放での並列処理
- [x] 適切なエラー変換

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| API名の変更 | 低 | Python側でエイリアス対応 |
| テスト失敗 | 中 | 既存テストを確認しながら実装 |
| パフォーマンス劣化 | 低 | ベンチマークで継続確認 |

## チェックリスト

### 実装前
- [x] 既存コードの確認（`similarity-rs`で類似実装チェック）
- [x] 依存関係の確認
- [x] 設計レビュー

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
- [ ] ベンチマーク（benchmark_results/以下）
- [ ] ドキュメント（rustdoc）
- [ ] PyO3バインディング（更新）

## 備考

### 実装方針の根拠
- arrow_native.rs（504行）は既にPyArrayでゼロコピー実装済み
- models.rs（685行）はPyReadonlyArray1でメモリコピーが発生
- arrow_native.rsをベースに不足機能を追加する方が効率的
- Critical Rules遵守：C004（理想実装ファースト）、C012（DRY原則）、C014（妥協実装禁止）

### ⚠️ アーキテクチャ移行の注意点
**絶対に避けるべきこと**：
- PyReadonlyArray1を使用したコードのコピペ
- numpy_to_arrow_direct関数の移植
- arrayref_to_numpy関数の移植
- Vec<f64>への変換を含むコード

**必須の実装パターン**：
```rust
// ❌ 悪い例（旧models.rsのパターン）
fn process(arr: PyReadonlyArray1<f64>) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let slice = arr.as_slice()?;
    let vec = slice.to_vec();  // メモリコピー発生！
}

// ✅ 良い例（arrow_native.rsのパターン）
fn process(py: Python, arr: PyArray) -> PyArrowResult<PyObject> {
    let array_ref = arr.as_ref();  // ゼロコピー参照
    // 直接Arrow配列として処理
}
```

### 期待される改善
- コード量：1189行 → 700行（40%削減）
- メモリコピー：2回 → 0回
- メモリ使用量：3倍 → 1倍
- パフォーマンス：30-50%改善

### バージョン計画
- 現在：v0.0.8（Float64Builder最適化済み）
- 目標：v0.0.9（Arrow Zero-Copy FFI完全移行）

### 実装順序の根拠
1. arrow_native.rsに機能追加（既存のゼロコピー実装を活用）
2. ファイル統合（リネームで簡潔に完了）
3. テスト実行（既存テストで動作確認）
4. ベンチマーク（改善効果を測定）

この順序により、最小限の作業で最大の効果を得られる。
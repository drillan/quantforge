# [Rust] Broadcasting対応の完全実装計画

## メタデータ
- **作成日**: 2025-09-03
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 300-400
- **対象モジュール**: bindings/python/src/models.rs, bindings/python/src/lib.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 300-400 行
- [x] 新規ファイル数: 0 個
- [x] 影響範囲: 複数モジュール（bindings層全体）
- [x] PyO3バインディング: 必要（核心部分）
- [x] SIMD最適化: 不要
- [x] 並列化: 不要（既存実装を利用）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 実行 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test --all` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| similarity-rs | 条件付き | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | 条件付き | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | 推奨 | `cargo bench` |

## フェーズ構成（中規模実装）

### Phase 1: 設計（1時間）
- [x] 現状分析完了（Rust coreは対応済み、bindings層が未対応）
- [x] インターフェース設計（PyAnyベース）
- [x] エラー型定義（既存のQuantForgeErrorを利用）

### Phase 2: 実装（3-4時間）

#### 2.1 共通ユーティリティ実装
- [ ] PyAny → Arrow変換関数の実装
  ```rust
  fn pyany_to_arrow(py: Python, value: &PyAny) -> PyResult<PyArray> {
      if let Ok(array) = value.extract::<PyArray>() {
          Ok(array)
      } else if let Ok(scalar) = value.extract::<f64>() {
          // スカラーをlength-1のArrow配列に変換
          let array = Float64Array::from(vec![scalar]);
          PyArray::from_array_ref(Arc::new(array))
      } else {
          Err(PyValueError::new_err("Expected float or arrow array"))
      }
  }
  ```

#### 2.2 Black-Scholesモデルの更新
- [ ] `arrow_call_price`関数のシグネチャ変更
  ```rust
  #[pyfunction]
  pub fn arrow_call_price(
      py: Python,
      spots: &PyAny,    // PyArray → PyAny
      strikes: &PyAny,  // PyArray → PyAny
      times: &PyAny,    // PyArray → PyAny
      rates: &PyAny,    // PyArray → PyAny
      sigmas: &PyAny,   // PyArray → PyAny
  ) -> PyArrowResult<PyObject>
  ```
- [ ] 内部変換処理の追加
- [ ] `arrow_put_price`の同様の更新
- [ ] `arrow_greeks`の同様の更新

#### 2.3 Black76モデルの更新
- [ ] `arrow_black76_call_price`の更新
- [ ] `arrow_black76_put_price`の更新
- [ ] `arrow_black76_greeks`の更新

#### 2.4 Mertonモデルの更新
- [ ] `arrow_merton_call_price`の更新
- [ ] `arrow_merton_put_price`の更新
- [ ] `arrow_merton_greeks`の更新

#### 2.5 Americanモデルの更新
- [ ] `arrow_american_call_price`の更新
- [ ] `arrow_american_put_price`の更新

### Phase 3: テスト実装（2時間）
- [ ] 単体テスト作成
  - スカラーのみの入力
  - 配列のみの入力
  - スカラー/配列混合入力
  - エラーケース（不正な型）
- [ ] 統合テスト作成
  - 実際のユースケースシナリオ
  - パフォーマンス計測

### Phase 4: 品質チェック（1時間）
```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック
similarity-rs --threshold 0.80 --skip-test bindings/
# 閾値超えの重複があれば rust-refactor.md 適用

# Python側のテスト
uv run maturin develop --release
uv run pytest tests/test_broadcasting.py -v
```

## 技術要件

### 必須要件
- [x] Rust coreのbroadcasting機能を活用
- [ ] ゼロコピーの維持（Arrow配列入力時）
- [ ] スカラー→Arrow変換の最小オーバーヘッド（~250ns）
- [ ] 後方互換性の維持（既存APIは変更なし）

### パフォーマンス目標
- [ ] スカラー変換: < 500ns
- [ ] 配列処理: 既存と同等
- [ ] メモリ使用量: スカラー入力時も最小限

### PyO3連携
- [ ] PyAnyを使った柔軟な型受け入れ
- [ ] 適切なエラーメッセージ
- [ ] GIL解放での並列処理（既存実装を維持）

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| PyAny型判定のオーバーヘッド | 低 | Rust側で高速判定（~250ns） |
| 既存APIとの互換性 | 中 | 型変換を内部で吸収 |
| エラーメッセージの分かりにくさ | 低 | 明確な型エラーメッセージ実装 |

## 実装詳細

### 1. 共通ユーティリティ（bindings/python/src/utils.rs）
```rust
use pyo3::prelude::*;
use pyo3_arrow::PyArray;
use arrow::array::Float64Array;
use std::sync::Arc;

/// PyAnyをArrow配列に変換（スカラーはlength-1配列に）
pub fn pyany_to_arrow(py: Python, value: &PyAny) -> PyResult<PyArray> {
    // 1. Arrow配列の場合はそのまま返す
    if let Ok(array) = value.extract::<PyArray>() {
        return Ok(array);
    }
    
    // 2. スカラー（float）の場合はlength-1配列に変換
    if let Ok(scalar) = value.extract::<f64>() {
        let arrow_array = Float64Array::from(vec![scalar]);
        return PyArray::from_array_ref(Arc::new(arrow_array));
    }
    
    // 3. それ以外はエラー
    Err(PyValueError::new_err(
        format!("Expected float or arrow array, got {}", value.get_type().name()?)
    ))
}
```

### 2. モデル関数の更新パターン
```rust
#[pyfunction]
#[pyo3(name = "call_price")]
pub fn arrow_call_price(
    py: Python,
    spots: &PyAny,    // 変更: PyArray → PyAny
    strikes: &PyAny,  // 変更: PyArray → PyAny
    times: &PyAny,    // 変更: PyArray → PyAny
    rates: &PyAny,    // 変更: PyArray → PyAny
    sigmas: &PyAny,   // 変更: PyArray → PyAny
) -> PyArrowResult<PyObject> {
    // 型変換（新規追加）
    let spots_array = pyany_to_arrow(py, spots)?;
    let strikes_array = pyany_to_arrow(py, strikes)?;
    let times_array = pyany_to_arrow(py, times)?;
    let rates_array = pyany_to_arrow(py, rates)?;
    let sigmas_array = pyany_to_arrow(py, sigmas)?;
    
    // 既存の処理（変更なし）
    let spots_ref = spots_array.as_ref();
    let strikes_ref = strikes_array.as_ref();
    // ... 以下既存実装
}
```

## チェックリスト

### 実装前
- [x] 既存コードの確認（Rust coreはbroadcasting対応済み）
- [x] 依存関係の確認（pyo3-arrow, arro3-core）
- [x] 設計レビュー（PyAnyベースの設計確定）

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

- [ ] 実装コード（bindings/python/src/以下）
- [ ] テストコード（tests/test_broadcasting.py）
- [ ] ベンチマーク（benchmarks/broadcasting_overhead.py）
- [ ] ドキュメント更新（docs/api/broadcasting.md）
- [ ] PyO3バインディング更新完了

## 実装順序の詳細

1. **utils.rsの作成**（30分）
   - pyany_to_arrow関数の実装
   - エラーハンドリングの統一

2. **Black-Scholesモデルの更新**（1時間）
   - arrow_call_price
   - arrow_put_price  
   - arrow_greeks
   - テスト作成・実行

3. **他モデルへの水平展開**（1.5時間）
   - Black76（3関数）
   - Merton（3関数）
   - American（2関数）
   - 各モデルでテスト確認

4. **統合テスト**（1時間）
   - 全モデルでのbroadcastingテスト
   - パフォーマンステスト
   - エラーケーステスト

5. **ドキュメント更新**（30分）
   - API仕様の更新
   - 使用例の追加

## 備考

- Rust coreは既にbroadcasting対応済み（`get_scalar_or_array_value`関数）
- Python bindings層のみの修正で完了
- 既存のスカラー関数（`call_price`）との責務分離を維持
- オーバーヘッドは最小限（Rust側で~250ns）
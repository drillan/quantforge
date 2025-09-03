# [Rust] Arrow-rs pyarrowフィーチャーによる真のゼロコピー実装計画

## メタデータ
- **作成日**: 2025-09-01
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 300-400
- **対象モジュール**: bindings/python/src/arrow_native.rs, Cargo.toml

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 350 行
- [x] 新規ファイル数: 0 個（既存ファイルの修正）
- [x] 影響範囲: 単一モジュール（arrow_native.rs）
- [x] PyO3バインディング: 必要
- [x] SIMD最適化: 不要（Arrow内部で処理）
- [x] 並列化: 不要（既存実装を活用）

### 規模判定結果
**中規模タスク**

## 背景と問題分析

### 現在の問題
1. **FFIポインタ管理の複雑性**
   - `FFI_ArrowArray`と`FFI_ArrowSchema`の手動管理
   - unsafeブロックの多用
   - メモリ安全性の保証困難

2. **型システムの不一致**
   - PyO3 0.22とarrow-rs 56.0の型システム非互換
   - `from_ffi`の期待型と実際の型の不一致

3. **バージョン互換性**
   - pyo3-arrow 0.2とPyO3 0.22の非互換
   - エコシステムの更新待ち状態

### 提案された解決策
arrow-rs自体の`pyarrow`フィーチャーまたはpyo3-arrowライブラリを活用し、手動FFI操作を排除。

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "call_price"
    meaning: "コールオプション価格計算"
    source: "naming_conventions.md#関数命名パターン"
  - name: "put_price"
    meaning: "プットオプション価格計算"
    source: "naming_conventions.md#関数命名パターン"
  - name: "spots, strikes, times, rates, sigmas"
    meaning: "Black-Scholesパラメータ（複数形）"
    source: "naming_conventions.md#バッチ処理の命名規則"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "PyArrowArray"
    meaning: "PyArrow配列のRust表現型"
    justification: "pyo3-arrowまたはarrow-rsで標準的に使用される型名"
    references: "pyo3-arrow documentation, arro3 project"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装アプローチの選択

### オプション1: arrow-rsのpyarrowフィーチャー（調査優先）
```toml
[dependencies]
arrow = { version = "56.0", features = ["ffi", "pyarrow"] }
```

**調査項目**:
- arrow-rs 56.0に`pyarrow`フィーチャーが存在するか
- PyO3 0.22との互換性
- 使用可能なAPI

### オプション2: pyo3-arrowライブラリ（代替案）
```toml
[dependencies]
pyo3-arrow = "0.5"  # または互換性のある最新版
```

**利点**:
- 実証済みの実装（arro3プロジェクトで使用）
- PyCapsule Interfaceの完全サポート
- unsafeコードの削減

## フェーズ構成（中規模実装）

### Phase 1: 技術調査と依存関係更新（2時間）
- [ ] arrow-rs 56.0の`pyarrow`フィーチャー調査
  - [ ] Cargo.tomlでフィーチャー有効化テスト
  - [ ] 利用可能なAPIの確認
  - [ ] サンプルコードの作成
- [ ] pyo3-arrowの互換性調査（代替案）
  - [ ] PyO3 0.22との互換バージョン特定
  - [ ] インストールとビルドテスト
- [ ] 最適なアプローチの選定

### Phase 2: 実装（4-6時間）

#### 2.1 arrow_native.rsの書き換え
```rust
// 想定される新実装（pyo3-arrow使用の場合）
use pyo3::prelude::*;
use pyo3_arrow::{PyArray, ToPyArrow, FromPyArrow};
use quantforge_core::compute::ArrowNativeCompute;

/// PyArrow配列を直接受け取る（ゼロコピー）
#[pyfunction]
#[pyo3(name = "call_price")]
pub fn arrow_call_price(
    py: Python,
    spots: PyArray<f64>,
    strikes: PyArray<f64>,
    times: PyArray<f64>,
    rates: PyArray<f64>,
    sigmas: PyArray<f64>,
) -> PyResult<PyArray<f64>> {
    // PyCapsule Interfaceによる自動変換（ゼロコピー）
    let spots_arrow = spots.to_arrow()?;
    let strikes_arrow = strikes.to_arrow()?;
    let times_arrow = times.to_arrow()?;
    let rates_arrow = rates.to_arrow()?;
    let sigmas_arrow = sigmas.to_arrow()?;
    
    // GIL解放して計算
    let result = py.allow_threads(|| {
        ArrowNativeCompute::black_scholes_call_price(
            &spots_arrow,
            &strikes_arrow,
            &times_arrow,
            &rates_arrow,
            &sigmas_arrow,
        )
    })?;
    
    // PyArrayとして返却（ゼロコピー）
    Ok(PyArray::from_arrow(result)?)
}
```

#### 2.2 既存コードのクリーンアップ
- [ ] 手動FFI操作コードの削除
- [ ] unsafeブロックの削減
- [ ] エラーハンドリングの簡潔化

#### 2.3 lib.rsの更新
```rust
// arrow_native モジュールの有効化
mod arrow_native;

#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Arrow Native Module
    let arrow_module = PyModule::new_bound(m.py(), "arrow")?;
    arrow_native::register_arrow_functions(&arrow_module)?;
    
    m.add_submodule(&arrow_module)?;
    sys_modules.set_item("quantforge.arrow", &arrow_module)?;
    
    Ok(())
}
```

### Phase 3: テストと検証（2時間）

#### 3.1 ユニットテスト
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::Python;
    
    #[test]
    fn test_zero_copy_conversion() {
        Python::with_gil(|py| {
            // PyArrow配列の作成とテスト
            // ゼロコピーの検証
        });
    }
}
```

#### 3.2 統合テスト
- [ ] Python側からの呼び出しテスト
- [ ] パフォーマンス測定
- [ ] メモリ使用量の確認

### Phase 4: 品質チェックと最適化（1時間）
```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# パフォーマンステスト
cd /home/driller/repo/quantforge
uv run python benchmarks/benchmark_arrow_api.py

# 目標値の確認
# 10,000要素: < 170μs（現在245μs）
```

## 技術要件

### 必須要件
- [x] ゼロコピー変換の実現
- [x] メモリ安全性（unsafeコードの最小化）
- [x] スレッド安全性（Send + Sync）

### パフォーマンス目標
- [ ] 10,000要素バッチ: < 170μs（現在245μs）
- [ ] 100,000要素バッチ: < 1.5ms（現在1.8ms）
- [ ] メモリオーバーヘッド: < 5%

### PyO3連携
- [x] PyCapsule Interfaceの活用
- [x] GIL解放での並列処理
- [x] 適切なエラー変換

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| arrow-rsにpyarrowフィーチャーがない | 高 | pyo3-arrowライブラリを使用 |
| PyO3 0.22との非互換 | 中 | 互換バージョンの調査と選定 |
| パフォーマンス目標未達成 | 中 | プロファイリングとボトルネック特定 |
| 既存テストの破壊 | 低 | 段階的な移行と互換性層の維持 |

## 成功基準

### 機能面
- [ ] Arrow APIが正常に動作
- [ ] 既存のテストがすべてパス
- [ ] Python側からの透過的な利用

### 性能面
- [ ] 10,000要素で170μs未満を達成
- [ ] メモリコピーの排除を確認
- [ ] GIL解放による並列処理の動作

### コード品質
- [ ] unsafeコード80%以上削減
- [ ] cargo clippyエラーゼロ
- [ ] ドキュメントの更新

## チェックリスト

### 実装前
- [ ] arrow-rs/pyo3-arrowの技術調査完了
- [ ] 依存関係の互換性確認
- [ ] 既存実装のバックアップ

### 実装中
- [ ] 定期的なビルドテスト
- [ ] 段階的な機能確認
- [ ] パフォーマンス測定

### 実装後
- [ ] 全テストパス
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新
- [ ] 学習内容の記録

## 成果物

- [ ] 更新されたarrow_native.rs
- [ ] 更新されたCargo.toml
- [ ] テストコード
- [ ] ベンチマーク結果
- [ ] 移行ガイド更新

## 参考資料

- [Arrow C Data Interface](https://arrow.apache.org/docs/format/CDataInterface.html)
- [PyCapsule Interface](https://arrow.apache.org/docs/format/CapsuleInterface.html)
- [pyo3-arrow documentation](https://docs.rs/pyo3-arrow/)
- [arro3 project](https://github.com/kylebarron/arro3)
- 既存実装: bindings/python/src/arrow_native.rs（コメントアウト状態）

## 備考

本計画は、既存のFFI実装の複雑性を解消し、真のゼロコピーArrow処理を実現することを目的とする。arrow-rsの組み込み機能またはpyo3-arrowライブラリを活用することで、保守性とパフォーマンスの両立を目指す。
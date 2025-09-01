# [Rust] Arrow FFI 真のゼロコピー実装計画

## ⚠️ アンチパターン警告
- **SIMD最適化**: 提案禁止（@.claude/antipatterns/simd-optimization-trap.md）
- **段階的実装**: 禁止（@.claude/antipatterns/stage-implementation.md）  
- **早すぎる最適化**: 測定前の推測禁止（@.claude/antipatterns/premature-optimization.md）

## メタデータ
- **作成日**: 2025-09-01
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 300-400
- **対象モジュール**: `Cargo.toml`, `bindings/python/src/arrow_native.rs`

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 350 行
- [x] 新規ファイル数: 0 個（既存ファイルの改修）
- [x] 影響範囲: 複数モジュール（`Cargo.toml`, `bindings/python/src/*`）
- [x] PyO3バインディング: 必要（大規模な修正）
- [x] SIMD最適化: 不要（Arrowの内部実装に委ねる）
- [x] 並列化: 必要（Rayon使用）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust中規模）

| ツール | 実行 | コマンド |
|--------|------|----------|
| cargo test | ✅ | `cargo test --all` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| similarity-rs | 条件付き | `similarity-rs --threshold 0.80 src/` |
| ハードコード検出 | ✅ | `grep -r "1e-\|0\.\d\{3,\}" --include="*.rs"` |

## 背景と問題分析

### 現在の問題（事実ベース）
1. **依存関係の不整合**
   - プロジェクト: `pyo3 v0.22`
   - arrow pyarrow feature要求: `pyo3 v0.25`
   - 結果: ビルドエラー

2. **API破壊的変更**
   - `PyModule::new_bound` → `PyModule::new`
   - `PyDict::new_bound` → `PyDict::new`
   - `import_bound` → `import`

3. **FFIの複雑性**
   - Arrow C Data Interfaceのポインタ管理
   - ライフタイム管理の困難さ

### 理想実装の定義
**真のゼロコピーArrow FFI実装**：
- PyArrow配列を直接Rust Arrow配列として処理
- メモリコピーゼロ（ポインタ共有のみ）
- GIL解放での並列処理
- 10,000要素で<170μsの処理速度

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
  - name: "arrow_call_price"
    meaning: "Arrow配列専用のcall price関数"
    justification: "既存のcall_priceと区別するためarrowプレフィックス"
    references: "arrow-rs documentation"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## フェーズ構成（中規模実装）

### Phase 0: TDD - テスト先行実装（1時間）【必須: C010準拠】
```rust
// tests/test_arrow_native.rs
#[cfg(test)]
mod tests {
    use super::*;
    use arrow::array::Float64Array;
    
    #[test]
    fn test_arrow_call_price_zero_copy() {
        // Red: 失敗するテストを先に書く
        let spots = Float64Array::from(vec![100.0; 10000]);
        let strikes = Float64Array::from(vec![105.0; 10000]);
        let times = Float64Array::from(vec![1.0; 10000]);
        let rates = Float64Array::from(vec![0.05; 10000]);
        let sigmas = Float64Array::from(vec![0.2; 10000]);
        
        let start = std::time::Instant::now();
        let result = arrow_call_price(&spots, &strikes, &times, &rates, &sigmas);
        let duration = start.elapsed();
        
        // パフォーマンス要求
        assert!(duration.as_micros() < 170, "Performance requirement: <170μs for 10k elements");
        
        // 正確性検証
        assert!((result.value(0) - 8.021352235143176).abs() < 1e-10);
    }
}
```

### Phase 1: 依存関係の統一（30分）

#### Cargo.toml更新（理想形のみ）
```toml
[workspace.dependencies]
# 統一されたバージョン（妥協なし）
pyo3 = { version = "0.25.1", features = ["extension-module"] }
numpy = "0.25"
arrow = { version = "56.0", features = ["ffi", "pyarrow"] }
arrow-array = "56.0"
arrow-buffer = "56.0"
```

### Phase 2: 理想実装（2-3時間）

#### 真のゼロコピー実装（妥協なし）
```rust
// bindings/python/src/arrow_native.rs
use arrow::array::{ArrayRef, Float64Array};
use arrow::ffi::{from_ffi, FFI_ArrowArray, FFI_ArrowSchema};
use pyo3::prelude::*;
use pyo3::types::PyCapsule;
use quantforge_core::compute::ArrowNativeCompute;
use rayon::prelude::*;

const PARALLEL_THRESHOLD: usize = 50_000; // 実測値に基づく定数

/// PyArrow配列を直接Arrow配列に変換（ゼロコピー）
fn pyarrow_to_arrow(py_array: &Bound<'_, PyAny>) -> PyResult<ArrayRef> {
    // PyCapsule Interfaceを使用（Arrow 14.0+標準）
    let capsule = py_array.call_method0("__arrow_c_array__")?;
    let (array_ptr, schema_ptr) = extract_capsule_pointers(capsule)?;
    
    // ゼロコピーでArrow配列を構築
    unsafe {
        let array = from_ffi(
            std::ptr::read(schema_ptr as *const FFI_ArrowSchema),
            std::ptr::read(array_ptr as *const FFI_ArrowArray),
        )
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            format!("Arrow FFI error: {}", e)
        ))?;
        Ok(array)
    }
}

#[pyfunction]
#[pyo3(name = "arrow_call_price")]
pub fn arrow_call_price(
    py: Python,
    spots: &Bound<'_, PyAny>,
    strikes: &Bound<'_, PyAny>,
    times: &Bound<'_, PyAny>,
    rates: &Bound<'_, PyAny>,
    sigmas: &Bound<'_, PyAny>,
) -> PyResult<PyObject> {
    // ゼロコピー変換
    let spots_arrow = pyarrow_to_arrow(spots)?;
    let strikes_arrow = pyarrow_to_arrow(strikes)?;
    let times_arrow = pyarrow_to_arrow(times)?;
    let rates_arrow = pyarrow_to_arrow(rates)?;
    let sigmas_arrow = pyarrow_to_arrow(sigmas)?;
    
    // 型安全なダウンキャスト
    let spots_f64 = spots_arrow.as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| PyErr::new::<pyo3::exceptions::PyTypeError, _>(
            "spots must be Float64Array"
        ))?;
    
    let len = spots_f64.len();
    
    // 並列処理閾値判定（実測値ベース）
    let result = if len >= PARALLEL_THRESHOLD {
        // Rayon並列処理
        py.allow_threads(|| {
            ArrowNativeCompute::black_scholes_call_price_parallel(
                spots_f64,
                strikes_arrow.as_any().downcast_ref().unwrap(),
                times_arrow.as_any().downcast_ref().unwrap(),
                rates_arrow.as_any().downcast_ref().unwrap(),
                sigmas_arrow.as_any().downcast_ref().unwrap(),
            )
        })
    } else {
        // シングルスレッド処理
        ArrowNativeCompute::black_scholes_call_price(
            spots_f64,
            strikes_arrow.as_any().downcast_ref().unwrap(),
            times_arrow.as_any().downcast_ref().unwrap(),
            rates_arrow.as_any().downcast_ref().unwrap(),
            sigmas_arrow.as_any().downcast_ref().unwrap(),
        )
    }?;
    
    // 結果をPyArrowに変換（ゼロコピー）
    arrow_to_pyarrow(py, result)
}
```

### Phase 3: API移行（1時間）

PyO3 v0.25 APIへの完全移行：
```rust
// 旧API（v0.22）→ 新API（v0.25）
PyModule::new_bound(py, "name")? → PyModule::new(py, "name")?
PyDict::new_bound(py) → PyDict::new(py)
py.import_bound("sys")? → py.import("sys")?
```

### Phase 4: 品質チェックと最適化（1時間）

```bash
# 基本チェック（必須）
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# ハードコード検出（C011準拠）
grep -r "1e-\|0\.\d\{3,\}" --include="*.rs" bindings/

# 重複チェック（閾値超えたら対処必須）
similarity-rs --threshold 0.80 --skip-test bindings/python/src/

# パフォーマンス測定（目標達成確認）
cargo bench --bench arrow_native_bench
```

## 技術要件

### 必須要件（妥協なし）
- [x] ゼロコピー変換の実現
- [x] メモリ安全性（unsafe最小化）
- [x] スレッド安全性（Send + Sync）
- [x] エラー率 < 1e-10（PRACTICAL_TOLERANCE）

### パフォーマンス目標（理想値）
- [ ] 10,000要素: < 170μs（目標）
- [ ] 100,000要素: < 1.5ms（目標）
- [ ] 1,000,000要素: < 15ms（目標）
- [ ] メモリオーバーヘッド: 0%（ゼロコピー）

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| PyCapsule Interface非対応環境 | 高 | Arrow 14.0+を必須要件とする |
| unsafe領域でのメモリエラー | 高 | Miriによる安全性検証を実施 |
| パフォーマンス目標未達 | 中 | プロファイリングで原因特定→最適化 |

## 成功基準

### 機能面
- [ ] Arrow APIが正常動作
- [ ] ゼロコピー変換の実現
- [ ] 既存テストがすべてパス

### 性能面  
- [ ] 10,000要素で170μs未満達成
- [ ] メモリコピーゼロを確認
- [ ] GIL解放による並列処理動作

### コード品質
- [ ] unsafeコード50行以内
- [ ] cargo clippy警告ゼロ
- [ ] ハードコード検出ゼロ

## チェックリスト

### 実装前
- [ ] TDDテスト作成完了（Red状態）
- [ ] 既存実装の調査完了（DRY原則）
- [ ] naming_conventions.md確認

### 実装中
- [ ] 定期的なテスト実行（Green達成）
- [ ] cargo fmt随時実行
- [ ] ハードコード回避確認

### 実装後
- [ ] 全品質ゲート通過
- [ ] パフォーマンス目標達成
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 完全実装された arrow_native.rs（妥協なし）
- [ ] 更新されたCargo.toml
- [ ] テストコード（TDD準拠）
- [ ] ベンチマーク結果（目標達成）
- [ ] ドキュメント更新

## 備考

本計画は理想実装ファースト原則（C004）に基づき、妥協なき実装を目指す。段階的実装やSIMD最適化の誘惑に陥らず、Arrowエコシステムの標準機能を最大限活用する。
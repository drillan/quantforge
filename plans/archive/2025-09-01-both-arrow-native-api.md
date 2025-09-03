# [Both] Apache Arrow ネイティブAPI実装計画

## メタデータ
- **作成日**: 2025-09-01
- **言語**: Both (Rust Core + Python Bindings)
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 500-700行
- **対象モジュール**: core/src/compute/, bindings/python/src/, python/quantforge/

## エグゼクティブサマリー

### 現状の問題
- **性能**: プロトタイプ（166.71μs）vs 現在（245.35μs）= 約80μsの差
- **設計**: NumPyファーストの設計でArrowの利点を活かせていない
- **変換オーバーヘッド**: 不要なコピー（slice.to_vec()）が発生

### 提案する解決策
**Apache Arrowファーストの設計に全面移行**
- PyArrow Arrayを直接入出力
- 内部処理もArrowネイティブ（真のゼロコピー）
- NumPy変換は別途オプション機能として提供

## 背景と問題分析

### 現在の実装の問題点

#### 1. NumPy中心の設計
```python
# 現在のAPI（NumPyファースト）
import numpy as np
result = quantforge.call_price(np_array, ...)  # NumPy入力 → NumPy出力
```

#### 2. 内部での無駄な変換
```rust
// 現在の内部フロー
PyReadonlyArray1<f64> (NumPy)
    ↓ as_slice()
&[f64] (スライス)
    ↓ slice.to_vec() 【ここでコピー！】
Float64Array (Arrow)
    ↓ 計算
ArrayRef
    ↓ to_numpy()
NumPy配列
```

#### 3. パフォーマンスへの影響
- `slice.to_vec()`: 約30-40μs
- Arrow配列作成: 約20μs
- 変換レイヤー: 約10μs
- **合計**: 約60-70μs（実測差の80μsとほぼ一致）

### プロトタイプの分析

プロトタイプも実はArrowを使用しているが、より効率的：
```rust
// プロトタイプの実装
let spots_arrow = Float64Array::from(spots.to_vec());  // ここでもコピー
```

しかし、プロトタイプが速い理由：
1. シンプルな実装（抽象化レイヤーが少ない）
2. 並列化閾値が適切（10,000）
3. 余計な変換ステップがない

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 500-700行
- [x] 新規ファイル数: 3-4個
- [x] 影響範囲: 全体（API変更含む）
- [x] PyO3バインディング: 大幅変更
- [x] SIMD最適化: 不要
- [x] 並列化: 既存実装を維持

### 規模判定結果
**大規模タスク** - API全体の再設計を含む

## 実装方針（理想実装ファースト）

### 設計原則
1. **Apache Arrowファースト** - PyArrowが第一級市民
2. **真のゼロコピー** - 不要な変換を完全排除
3. **NumPyはオプション** - 必要な人向けの変換機能

### 新しいアーキテクチャ

```
┌─────────────────────────────────────────────┐
│              Python API Layer               │
├─────────────────────────────────────────────┤
│  PyArrow Native API (Primary)               │
│  - call_price(pa.Array) → pa.Array          │
│  - put_price(pa.Array) → pa.Array           │
│                                             │
│  NumPy Compatibility Layer (Optional)       │
│  - call_price_numpy(np.array) → np.array    │
│  - from_numpy() / to_numpy() utilities      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│           Rust Bindings Layer               │
├─────────────────────────────────────────────┤
│  PyArrow → Arrow (Zero Copy)                │
│  Direct buffer access, no vec creation      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│              Rust Core Layer                │
├─────────────────────────────────────────────┤
│  Arrow Native Processing                    │
│  Parallel computation with Rayon            │
└─────────────────────────────────────────────┘
```

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "call_price"
    meaning: "コールオプション価格計算（Arrow版）"
    source: "naming_conventions.md#関数命名パターン"
  - name: "spots, strikes, times, rates, sigmas"
    meaning: "Black-Scholesパラメータ"
    source: "naming_conventions.md#共通パラメータ"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "call_price_numpy"
    meaning: "NumPy互換版の価格計算"
    justification: "NumPyユーザー向けの明示的な関数名"
    status: "pending_approval"
  - name: "to_numpy"
    meaning: "Arrow配列をNumPyに変換"
    justification: "業界標準的な命名規則"
    references: "pandas.DataFrame.to_numpy()"
    status: "pending_approval"
  - name: "from_numpy"
    meaning: "NumPy配列をArrowに変換"
    justification: "対称的な命名"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 実装フェーズ

### Phase 1: Core層のArrow最適化（1日）

#### 1.1 ゼロコピーArrow実装
```rust
// core/src/compute/arrow_native.rs
use arrow::array::{Float64Array, ArrayRef};
use arrow::buffer::Buffer;
use std::sync::Arc;

pub struct ArrowNativeCompute;

impl ArrowNativeCompute {
    /// 真のゼロコピー実装
    pub fn call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ComputeError> {
        // 直接値アクセス（コピーなし）
        let len = spots.len();
        
        // 並列処理の判定
        if len >= get_parallel_threshold() {
            let values: Vec<f64> = (0..len)
                .into_par_iter()
                .map(|i| {
                    // 直接値取得（value()メソッドは高速）
                    let s = spots.value(i);
                    let k = strikes.value(i);
                    let t = times.value(i);
                    let r = rates.value(i);
                    let sigma = sigmas.value(i);
                    
                    // Black-Scholes計算
                    compute_call_price(s, k, t, r, sigma)
                })
                .collect();
            
            // Arrowバッファ作成（一度だけ）
            Ok(Arc::new(Float64Array::from(values)))
        } else {
            // シーケンシャル処理も同様
            let mut builder = Float64Builder::with_capacity(len);
            for i in 0..len {
                let price = compute_call_price(
                    spots.value(i),
                    strikes.value(i),
                    times.value(i),
                    rates.value(i),
                    sigmas.value(i),
                );
                builder.append_value(price);
            }
            Ok(Arc::new(builder.finish()))
        }
    }
}
```

### Phase 2: PyArrowネイティブバインディング（1日）

#### 2.1 PyArrow直接サポート
```rust
// bindings/python/src/arrow_native.rs
use pyo3::prelude::*;
use arrow::pyarrow::PyArrowType;

/// PyArrow配列を直接受け取る
#[pyfunction]
pub fn call_price<'py>(
    py: Python<'py>,
    spots: PyArrowType<Float64Array>,
    strikes: PyArrowType<Float64Array>,
    times: PyArrowType<Float64Array>,
    rates: PyArrowType<Float64Array>,
    sigmas: PyArrowType<Float64Array>,
) -> PyResult<PyArrowType<Float64Array>> {
    // GIL解放して計算（ゼロコピー）
    let result = py.allow_threads(|| {
        ArrowNativeCompute::call_price(
            &spots.0,  // 直接Arrow配列参照
            &strikes.0,
            &times.0,
            &rates.0,
            &sigmas.0,
        )
    })?;
    
    // PyArrowとして返却
    Ok(PyArrowType(result.as_any().downcast_ref::<Float64Array>().unwrap().clone()))
}
```

### Phase 3: Python APIレイヤー（1日）

#### 3.1 メインAPI（PyArrowネイティブ）
```python
# python/quantforge/arrow_api.py
import pyarrow as pa
from typing import Union
from . import _rust  # Rustバインディング

def call_price(
    spots: pa.Array,
    strikes: pa.Array,
    times: pa.Array,
    rates: pa.Array,
    sigmas: pa.Array,
) -> pa.Array:
    """
    Calculate Black-Scholes call prices (Arrow native).
    
    Parameters
    ----------
    spots : pyarrow.Array
        Spot prices
    strikes : pyarrow.Array
        Strike prices
    times : pyarrow.Array
        Times to maturity
    rates : pyarrow.Array
        Risk-free rates
    sigmas : pyarrow.Array
        Volatilities
        
    Returns
    -------
    pyarrow.Array
        Call option prices
    """
    # 型チェック（必要に応じて）
    spots = pa.array(spots) if not isinstance(spots, pa.Array) else spots
    strikes = pa.array(strikes) if not isinstance(strikes, pa.Array) else strikes
    times = pa.array(times) if not isinstance(times, pa.Array) else times
    rates = pa.array(rates) if not isinstance(rates, pa.Array) else rates
    sigmas = pa.array(sigmas) if not isinstance(sigmas, pa.Array) else sigmas
    
    # Rust実装を呼び出し
    return _rust.call_price(spots, strikes, times, rates, sigmas)
```

#### 3.2 NumPy互換レイヤー（オプション）
```python
# python/quantforge/numpy_compat.py
import numpy as np
import pyarrow as pa
from .arrow_api import call_price as _arrow_call_price

def call_price_numpy(
    spots: np.ndarray,
    strikes: np.ndarray,
    times: np.ndarray,
    rates: np.ndarray,
    sigmas: np.ndarray,
) -> np.ndarray:
    """
    NumPy compatibility wrapper for call_price.
    
    This is a convenience function for NumPy users.
    For best performance, use the Arrow API directly.
    """
    # NumPy → Arrow変換
    spots_arrow = pa.array(spots)
    strikes_arrow = pa.array(strikes)
    times_arrow = pa.array(times)
    rates_arrow = pa.array(rates)
    sigmas_arrow = pa.array(sigmas)
    
    # Arrow APIを呼び出し
    result_arrow = _arrow_call_price(
        spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow
    )
    
    # Arrow → NumPy変換
    return result_arrow.to_numpy()

# ユーティリティ関数
def to_numpy(arrow_array: pa.Array) -> np.ndarray:
    """Convert Arrow array to NumPy array."""
    return arrow_array.to_numpy()

def from_numpy(numpy_array: np.ndarray) -> pa.Array:
    """Convert NumPy array to Arrow array."""
    return pa.array(numpy_array)
```

### Phase 4: ベンチマークと検証（1日）

#### 4.1 パフォーマンステスト
```python
# benchmarks/test_arrow_native.py
import pyarrow as pa
import time

def benchmark_arrow_native():
    # PyArrow配列作成
    size = 10_000
    spots = pa.array(np.random.uniform(80, 120, size))
    strikes = pa.array(np.full(size, 100.0))
    times = pa.array(np.full(size, 1.0))
    rates = pa.array(np.full(size, 0.05))
    sigmas = pa.array(np.random.uniform(0.15, 0.35, size))
    
    # ベンチマーク
    start = time.perf_counter()
    result = quantforge.call_price(spots, strikes, times, rates, sigmas)
    end = time.perf_counter()
    
    print(f"Arrow Native: {(end - start) * 1e6:.2f}μs")
    # 目標: < 170μs（プロトタイプ同等）
```

### Phase 5: 移行とドキュメント（0.5日）

#### 5.1 移行ガイド
```markdown
# Migration Guide

## Breaking Changes
- Primary API now uses PyArrow Arrays
- NumPy support moved to `numpy_compat` module

## Migration Examples

### Before (v0.0.6)
```python
import numpy as np
result = quantforge.call_price(np_array, ...)
```

### After (v0.1.0)
```python
# Option 1: Use Arrow directly (recommended)
import pyarrow as pa
result = quantforge.call_price(pa.array(data), ...)

# Option 2: Use NumPy compatibility layer
from quantforge.numpy_compat import call_price_numpy
result = call_price_numpy(np_array, ...)
```

## 技術要件

### 必須要件
- [x] 真のゼロコピー実装
- [x] プロトタイプと同等の性能（< 170μs）
- [x] PyArrowネイティブAPI
- [x] NumPy互換性（オプション機能として）

### パフォーマンス目標
- 10,000要素: < 170μs（現在245.35μs）
- 100,000要素: < 1,200μs
- メモリ使用量: 入力データの1.0倍（コピーなし）

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| API破壊的変更 | 高 | v0.1.0としてメジャーバージョンアップ |
| NumPyユーザーの混乱 | 中 | 明確な移行ガイドとnumpy_compatモジュール |
| PyArrow依存 | 低 | 既に多くのデータツールで標準 |
| PyO3のArrowサポート | 中 | arrow-rsのPyO3統合を使用 |

## チェックリスト

### 実装前
- [ ] arrow-rsのPyO3統合調査
- [ ] PyArrowのゼロコピー確認
- [ ] ベンチマーク環境準備

### 実装中
- [ ] ゼロコピー動作の検証
- [ ] パフォーマンス測定（逐次）
- [ ] メモリプロファイリング

### 実装後
- [ ] 目標性能達成（< 170μs）
- [ ] API互換性テスト
- [ ] 移行ガイド完成
- [ ] バージョン番号更新（0.1.0）

## 成果物

- [ ] Arrow最適化Core層（core/src/compute/arrow_native.rs）
- [ ] PyArrowネイティブバインディング（bindings/python/src/arrow_native.rs）  
- [ ] Python APIレイヤー（python/quantforge/arrow_api.py）
- [ ] NumPy互換モジュール（python/quantforge/numpy_compat.py）
- [ ] 移行ガイド（docs/migration/v0.1.0.md）
- [ ] パフォーマンステスト結果

## 成功基準

1. **性能**: 10,000要素で170μs以下（プロトタイプ同等）
2. **メモリ**: 真のゼロコピー実現（メモリ使用量1.0倍）
3. **API**: PyArrowネイティブ + NumPy互換性
4. **保守性**: シンプルで理解しやすい実装

## 備考

### なぜApache Arrowファーストなのか

1. **現代的なデータエコシステム**
   - Parquet、データベース、分散処理すべてArrow対応
   - pandas 2.0もArrowバックエンド採用
   - Polars、DuckDBなど新世代ツールはArrowネイティブ

2. **真のゼロコピー**
   - NumPy変換を挟まない直接処理
   - メモリ効率とパフォーマンスの両立

3. **将来性**
   - Arrow Compute Functionsとの統合可能
   - SIMD最適化の恩恵を自動的に享受
   - クロスプラットフォーム対応

### 段階的移行ではない理由

Critical Rule C004（理想実装ファースト）に従い、段階的移行は行わない。
v0.1.0として破壊的変更を明確にし、一度で理想形に移行する。
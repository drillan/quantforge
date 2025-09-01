# QuantForge Arrow-Native完全移行計画

## メタデータ
- **作成日**: 2025-09-01
- **言語**: Rust + Python
- **ステータス**: DRAFT
- **推定規模**: 大規模（全コード置換）
- **推定期間**: 5営業日
- **影響範囲**: プロジェクト全体

## 背景

### プロトタイプ実証結果
- **パフォーマンス**: 60.5%改善（10,000要素）
- **処理速度**: 2.53倍高速化
- **メモリコピー**: 完全排除

### 重要な前提
- **既存ユーザー**: ゼロ（破壊的変更可能）
- **技術的負債**: 許容しない（C004/C014原則）
- **レガシーコード**: 完全削除

## アーキテクチャ設計

### 移行戦略
現在のディレクトリ構造（`core/`、`bindings/python/`）を維持しつつ、内容を完全にArrow-nativeに置き換える。

```
quantforge/
├── Cargo.toml               # workspace定義（変更なし）
│
├── core/                    # Arrow-native計算エンジン（内容完全置換）
│   ├── Cargo.toml          # arrow依存追加、ndarray削除
│   ├── src/
│   │   ├── compute/        # Arrow Computeカーネル（新規）
│   │   │   ├── black_scholes.rs
│   │   │   ├── black76.rs
│   │   │   ├── merton.rs
│   │   │   ├── american.rs
│   │   │   └── greeks.rs
│   │   ├── math/           # 数学関数（libm維持）
│   │   │   └── distributions.rs
│   │   └── lib.rs          # Arrow中心のAPI
│   ├── tests/              # Arrow計算のテスト
│   └── benches/            # criterionベンチマーク
│
├── bindings/python/        # Python専用バインディング（内容完全置換）
│   ├── Cargo.toml          # pyo3 + arrow依存
│   ├── pyproject.toml      # pyarrow依存追加
│   ├── src/
│   │   ├── lib.rs          # 最小限のFFI
│   │   ├── convert.rs      # Arrow ⟷ NumPy変換（オプション）
│   │   └── api/            # Python API実装
│   │       ├── arrow.rs    # Arrow直接API（メイン）
│   │       └── numpy.rs    # NumPy互換API（薄いラッパー）
│   └── python/
│       └── quantforge/
│           ├── __init__.py # Arrow API公開
│           └── numpy_compat.py # NumPy互換レイヤー
│
├── tests/                  # 統合テスト（維持）
├── benchmarks/             # パフォーマンステスト（更新）
│
└── [削除対象]
    └── src/                # 現在の混在実装 → 完全削除
```

## 実装詳細

### Phase 1: 準備（0.5日）

#### 1.1 プロジェクトバックアップ
```bash
git checkout -b arrow-native-migration
git tag pre-arrow-migration
```

#### 1.2 依存関係準備
```toml
# workspace.dependencies に追加
arrow = "56.0"
arrow-array = "56.0"
arrow-buffer = "56.0"
libm = "0.2"  # 既存
```

### Phase 2: Core層のArrow化（2日）

#### 2.1 既存コード退避と削除
```bash
# 現在のcore実装を一時退避（参照用）
cp -r core/ core.backup/

# core/src/内容を完全削除
rm -rf core/src/*
```

#### 2.2 Arrow-native実装
```rust
// core/src/compute/black_scholes.rs
use arrow::array::{Float64Array, ArrayRef};
use arrow::compute::kernels::numeric::*;
use libm::erf;

pub struct BlackScholesParams {
    pub spots: ArrayRef,    // Float64Array
    pub strikes: ArrayRef,
    pub times: ArrayRef,
    pub rates: ArrayRef,
    pub sigmas: ArrayRef,
}

pub fn call_price(params: &BlackScholesParams) -> Result<ArrayRef, ArrowError> {
    // Arrow-native計算
    // ゼロコピー、SIMD自動最適化
}
```

#### 2.3 数学関数移植
```rust
// core/src/math/distributions.rs
use arrow::array::Float64Array;

#[inline]
pub fn norm_cdf_array(values: &Float64Array) -> Float64Array {
    // libm::erfベースの実装
    // プロトタイプで実証済み
}
```

### Phase 3: Bindings層のArrow化（1.5日）

#### 3.1 既存バインディング退避と削除
```bash
# 現在のバインディングを一時退避
cp -r bindings/python/ bindings/python.backup/

# bindings/python/src/内容を完全削除
rm -rf bindings/python/src/*
```

#### 3.2 最小限のFFI実装
```rust
// bindings/python/src/lib.rs
use pyo3::prelude::*;
use numpy::{PyArray1, PyReadonlyArray1};
use arrow::array::Float64Array;

#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_submodule(arrow_api::create_module(m.py())?)?;
    m.add_submodule(numpy_api::create_module(m.py())?)?;
    Ok(())
}
```

#### 3.3 Arrow直接API
```rust
// bindings/python/src/api/arrow.rs
#[pyfunction]
fn call_price_arrow(
    py: Python<'_>,
    spots: PyArrowType<Float64Array>,
    strikes: PyArrowType<Float64Array>,
    // ...
) -> PyResult<PyArrowType<Float64Array>> {
    py.allow_threads(|| {
        // 直接Arrow計算呼び出し
        quantforge_core::compute::black_scholes::call_price(...)
    })
}
```

#### 3.4 NumPy互換レイヤー（オプション）
```python
# bindings/python/python/quantforge/numpy_compat.py
import numpy as np
import pyarrow as pa
from . import arrow_api

def call_price(spots, strikes, times, rates, sigmas):
    """NumPy互換インターフェース（内部でArrow使用）"""
    # NumPy → Arrow変換
    spots_arrow = pa.array(np.asarray(spots))
    # ...
    
    # Arrow計算
    result_arrow = arrow_api.call_price_arrow(
        spots_arrow, strikes_arrow, times_arrow, rates_arrow, sigmas_arrow
    )
    
    # Arrow → NumPy変換
    return result_arrow.to_numpy()
```

### Phase 4: 旧コード完全削除（0.5日）

#### 4.1 src/ディレクトリ削除
```bash
rm -rf src/
git rm -r src/
```

#### 4.2 バックアップ削除
```bash
rm -rf core.backup/
rm -rf bindings/python.backup/
```

#### 4.3 ワークスペース更新
```toml
# Cargo.toml
[workspace]
resolver = "2"
members = [
    "core",              # Arrow-native
    "bindings/python"    # Arrow-first bindings
]
```

### Phase 5: テスト・検証（1日）

#### 5.1 正確性テスト
```python
# tests/test_correctness.py
def test_arrow_accuracy():
    # Golden Masterとの比較
    # 相対誤差 < 1e-15
```

#### 5.2 パフォーマンステスト
```python
# benchmarks/test_performance.py
def test_arrow_performance():
    # 目標性能
    assert time_10000 < 200  # μs
    assert time_1000000 < 10000  # μs (10ms)
```

## 期待される成果

### パフォーマンス
| データサイズ | 現在 | Arrow化後 | 改善率 |
|------------|------|-----------|--------|
| 100 | 13.46μs | 10μs | 26% |
| 1,000 | 80.91μs | 45μs | 44% |
| 10,000 | 421.69μs | 160μs | 62% |
| 100,000 | 1977μs | 850μs | 57% |

### コード品質
- **行数**: 15,000 → 5,000（67%削減）
- **依存関係**: 20+ → 8（60%削減）
- **複雑性**: 大幅削減（単一データ表現）

## リスクと対策

### リスク1: Arrow APIの学習曲線
**対策**: 
- 包括的なドキュメント作成
- サンプルコード充実
- NumPy互換レイヤー提供

### リスク2: デバッグ困難性
**対策**:
- 詳細なロギング
- Arrow配列の可視化ツール
- 段階的なテスト

## 成功基準

1. **性能**: 10,000要素で200μs以下
2. **正確性**: Golden Master完全一致
3. **メモリ**: ゼロコピー実現
4. **コード**: レガシーコード完全削除

## 実装チェックリスト

- [ ] Phase 1: 準備完了
- [ ] Phase 2: Core層Arrow化完了
- [ ] Phase 3: Bindings層Arrow化完了
- [ ] Phase 4: 旧コード削除完了
- [ ] Phase 5: テスト合格

## 結論

この計画により：
- **技術的負債ゼロ**（C004/C014完全準拠）
- **最高性能**（プロトタイプで実証済み）
- **シンプルな構造**（Arrow単一表現）

を実現し、QuantForgeを真のArrow-nativeライブラリとして再構築します。
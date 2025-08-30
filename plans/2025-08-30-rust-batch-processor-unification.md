# [Rust] BatchProcessor統一による全モデル最適化 実装計画

## メタデータ
- **作成日**: 2025-08-30
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中規模
- **推定コード行数**: 500行
- **対象モジュール**: src/models/black76/, src/models/merton/, src/traits/

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 500行
- [x] 新規ファイル数: 0個（既存ファイルの修正のみ）
- [x] 影響範囲: 複数モジュール（Black76, Merton）
- [x] PyO3バインディング: 必要（Python APIに影響）
- [x] SIMD最適化: 不要（既存の最適化を活用）
- [x] 並列化: 必要（既存のParallelStrategy活用）

### 規模判定結果
**中規模タスク** - 既存のBatchProcessorトレイトとParallelStrategyを活用した統一実装

## 現状分析

### 問題点
1. **ハードコードされた並列化閾値**
   ```rust
   // src/models/black76/batch.rs
   const PARALLELIZATION_THRESHOLD: usize = 10_000;  // ハードコード
   
   // src/models/merton/batch.rs
   const PARALLELIZATION_THRESHOLD: usize = 10_000;  // 重複
   ```

2. **重複したバッチ処理ロジック**
   - 各モデルで似たようなバッチ処理コードが重複
   - Black-Scholesは動的戦略を使用、他は未適用
   - 保守性とパフォーマンスの不均一

3. **将来の拡張性問題**
   - 新モデル追加時に同じコードを再実装必要
   - 最適化が一部モデルにしか適用されない

## 実装方針

### Phase 1: BatchProcessorトレイトの完全活用

#### 1.1 Black76用プロセッサ実装
```rust
// src/models/black76/processor.rs
use crate::traits::{BatchProcessor, BatchProcessorWithDividend};
use crate::models::black76::{Black76, Black76Params};
use crate::models::PricingModel;

pub struct Black76CallProcessor;
pub struct Black76PutProcessor;
pub struct Black76GreeksProcessor;

impl BatchProcessor for Black76CallProcessor {
    type Params = Black76Params;
    type Output = f64;
    
    fn create_params(&self, f: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        Black76Params::new(f, k, t, r, sigma)
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        Black76::call_price(params)
    }
}

impl BatchProcessor for Black76PutProcessor {
    type Params = Black76Params;
    type Output = f64;
    
    fn create_params(&self, f: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        Black76Params::new(f, k, t, r, sigma)
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        Black76::put_price(params)
    }
}
```

#### 1.2 Merton用プロセッサ実装（配当対応）
```rust
// src/models/merton/processor.rs
use crate::traits::BatchProcessorWithDividend;
use crate::models::merton::{MertonModel, MertonParams};

pub struct MertonCallProcessor;
pub struct MertonPutProcessor;

impl BatchProcessorWithDividend for MertonCallProcessor {
    type Params = MertonParams;  // 基本パラメータ
    type ParamsWithDividend = MertonParams;  // 配当付きパラメータ
    type Output = f64;
    
    fn create_params(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params {
        MertonParams::new(s, k, t, r, 0.0, sigma)  // q=0でデフォルト
    }
    
    fn create_params_with_dividend(
        &self, 
        s: f64, 
        k: f64, 
        t: f64, 
        r: f64, 
        q: f64, 
        sigma: f64
    ) -> Self::ParamsWithDividend {
        MertonParams::new(s, k, t, r, q, sigma)
    }
    
    fn process_single(&self, params: &Self::Params) -> Self::Output {
        MertonModel::call_price(params)
    }
    
    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output {
        MertonModel::call_price(params)
    }
}
```

### Phase 2: バッチ処理の統一実装

#### 2.1 Black76バッチ処理の簡素化
```rust
// src/models/black76/batch.rs
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::optimization::ParallelStrategy;
use super::processor::{Black76CallProcessor, Black76PutProcessor};
use crate::traits::BatchProcessor;

pub fn call_price_batch(
    forwards: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![forwards, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let values: Vec<_> = iter.collect();
    
    // 動的戦略を使用
    let strategy = ParallelStrategy::select(values.len());
    let processor = Black76CallProcessor;
    
    Ok(strategy.process_batch(&values, |vals| {
        let params = processor.create_params(vals[0], vals[1], vals[2], vals[3], vals[4]);
        processor.process_single(&params)
    }))
}

pub fn put_price_batch(
    forwards: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    // 同様の実装
    let inputs = vec![forwards, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let values: Vec<_> = iter.collect();
    
    let strategy = ParallelStrategy::select(values.len());
    let processor = Black76PutProcessor;
    
    Ok(strategy.process_batch(&values, |vals| {
        let params = processor.create_params(vals[0], vals[1], vals[2], vals[3], vals[4]);
        processor.process_single(&params)
    }))
}
```

#### 2.2 Mertonバッチ処理の統一
```rust
// src/models/merton/batch.rs
use crate::optimization::ParallelStrategy;
use super::processor::{MertonCallProcessor, MertonPutProcessor};

pub fn call_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    dividend_yields: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, dividend_yields, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let values: Vec<_> = iter.collect();
    
    let strategy = ParallelStrategy::select(values.len());
    let processor = MertonCallProcessor;
    
    Ok(strategy.process_batch(&values, |vals| {
        let params = processor.create_params_with_dividend(
            vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]
        );
        processor.process_single_with_dividend(&params)
    }))
}
```

### Phase 3: Python APIの統合

#### 3.1 共通バッチ処理関数
```rust
// src/python_modules.rs
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

/// 汎用バッチ処理関数
fn process_batch_generic<P>(
    py: Python<'_>,
    processor: P,
    prices: PyReadonlyArray1<f64>,
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
) -> PyResult<Bound<'_, PyArray1<f64>>>
where
    P: BatchProcessor,
    P::Output: Into<f64> + Send,
    P::Params: Send + Sync,
{
    processor.process_batch_parallel(py, prices, k, t, r, sigma, "price")
}
```

## 技術要件

### 必須要件
- [x] 既存APIとの完全な後方互換性
- [x] パフォーマンスの維持または向上
- [x] エラーハンドリングの一貫性

### パフォーマンス目標
- [x] Black76: 現状と同等以上（100万件 < 20ms）
- [x] Merton: 現状と同等以上（100万件 < 25ms）
- [x] 全モデル: 動的戦略により100,000件で4倍以上高速化

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| APIの破壊的変更 | 高 | Python側のインターフェースは変更しない |
| パフォーマンス劣化 | 中 | ベンチマークで検証、問題があれば元に戻す |
| トレイト境界の複雑化 | 低 | Send + Syncの適切な付与で解決 |

## 実装手順

### Phase 1: Black76の移行（2時間）
1. [ ] processor.rsファイル作成
2. [ ] BatchProcessor実装
3. [ ] batch.rsの簡素化
4. [ ] テスト実行・検証

### Phase 2: Mertonの移行（2時間）
1. [ ] processor.rsファイル作成
2. [ ] BatchProcessorWithDividend実装
3. [ ] batch.rsの簡素化
4. [ ] テスト実行・検証

### Phase 3: 統合テスト（1時間）
1. [ ] パフォーマンステスト
2. [ ] 回帰テスト
3. [ ] ドキュメント更新

## チェックリスト

### 実装前
- [x] 既存コードのバックアップ
- [x] ベンチマーク基準値の記録
- [x] 影響範囲の確認

### 実装中
- [ ] 各フェーズごとのテスト実行
- [ ] パフォーマンス測定
- [ ] エラーハンドリング確認

### 実装後
- [ ] 全テストパス確認
- [ ] パフォーマンス改善確認
- [ ] ドキュメント更新
- [ ] 計画書のCOMPLETED化とarchive移動

## 成果物

- [ ] src/models/black76/processor.rs（新規）
- [ ] src/models/merton/processor.rs（新規）
- [ ] src/models/black76/batch.rs（更新）
- [ ] src/models/merton/batch.rs（更新）
- [ ] ベンチマーク結果レポート
- [ ] 更新されたドキュメント

## 期待される効果

1. **コード削減**: 重複コード約300行削減
2. **保守性向上**: 単一の最適化実装で全モデルが恩恵
3. **拡張性向上**: 新モデル追加が容易に
4. **パフォーマンス向上**: 全モデルで100,000件処理が4倍以上高速化

## 備考

- 既存の動的並列化戦略（ParallelStrategy）を最大限活用
- Critical Rules C011-3（ハードコード禁止）、C012（DRY原則）を遵守
- 将来的にはAmericanオプションモデルも同様に統合可能
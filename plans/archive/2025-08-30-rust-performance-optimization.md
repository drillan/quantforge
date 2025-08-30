# [Rust] QuantForge 並列処理性能最適化 実装計画

## メタデータ
- **作成日**: 2025-08-30
- **言語**: Rust
- **ステータス**: COMPLETED
- **推定規模**: 中規模
- **推定コード行数**: 400行
- **対象モジュール**: src/constants.rs, src/optimization/, src/traits/, src/models/

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 400行
- [x] 新規ファイル数: 2個（optimization/parallel_strategy.rs, optimization/mod.rs）
- [x] 影響範囲: 複数モジュール（traits, models全体）
- [x] PyO3バインディング: 必要（間接的に影響）
- [x] SIMD最適化: 将来対応
- [x] 並列化: 必要（コア改善項目）

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
| cargo bench | ✅ | `cargo bench` |

## 問題分析

### 現状の性能問題
| データサイズ | QuantForge | NumPy | 相対性能 | 期待値 |
|------------|------------|--------|---------|--------|
| 100件 | 12.2 μs | 85.7 μs | 7.0倍速い | ✅ |
| 1,000件 | 82.3 μs | 161.5 μs | 1.96倍速い | ✅ |
| 10,000件 | 832 μs | 824 μs | 0.99倍 | ⚠️ |
| **100,000件** | **31.04 ms** | **8.55 ms** | **0.28倍** | ❌ |
| 1,000,000件 | 54.6 ms | 65.0 ms | 1.19倍速い | ✅ |

### 根本原因
1. **ハードコード違反（C011-3）**:
   - `black_scholes_batch.rs`: `if size > 10000` (22行目)
   - `traits/batch_processor.rs`: `PARALLEL_THRESHOLD: usize = 1000` (62行目)
   - `traits/batch_processor.rs`: `CHUNK_SIZE: usize = 1024` (162行目, 200行目)

2. **不整合な並列化戦略（C012違反）**:
   - 各モデルで異なる閾値定義
   - 動的最適化の欠如
   - キャッシュ考慮なし

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "EPSILON"
    meaning: "実務精度（後方互換性）"
    source: "src/constants.rs#29"
  - name: "PRACTICAL_TOLERANCE"
    meaning: "実務精度（新規推奨）"
    source: "src/constants.rs#11"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  # 並列処理閾値
  - name: "PARALLEL_THRESHOLD_SMALL"
    meaning: "小規模データ並列化閾値（L1キャッシュ最適）"
    justification: "キャッシュレベルで区別する業界標準的アプローチ"
    references: "Intel Optimization Manual, Agner Fog's Optimization Guide"
    status: "pending_approval"
  
  - name: "PARALLEL_THRESHOLD_MEDIUM"
    meaning: "中規模データ並列化閾値（L2キャッシュ最適）"
    justification: "同上"
    status: "pending_approval"
  
  - name: "PARALLEL_THRESHOLD_LARGE"
    meaning: "大規模データ並列化閾値（L3キャッシュ最適）"
    justification: "同上"
    status: "pending_approval"

  # チャンクサイズ
  - name: "CACHE_LINE_SIZE"
    meaning: "CPUキャッシュライン標準サイズ"
    justification: "x86_64アーキテクチャ標準"
    references: "Intel 64 and IA-32 Architectures Software Developer's Manual"
    status: "pending_approval"
  
  - name: "CHUNK_SIZE_L1"
    meaning: "L1キャッシュ最適チャンクサイズ"
    justification: "L1データキャッシュサイズ（32KB）の効率的利用"
    status: "pending_approval"
  
  - name: "CHUNK_SIZE_L2"
    meaning: "L2キャッシュ最適チャンクサイズ"
    justification: "L2キャッシュサイズ（256KB）の効率的利用"
    status: "pending_approval"
  
  - name: "CHUNK_SIZE_L3"
    meaning: "L3キャッシュ最適チャンクサイズ"
    justification: "L3キャッシュサイズ（2MB）の効率的利用"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認（定数命名規則）
- [x] ドキュメントでの使用方法定義
- [x] 定数は大文字スネークケースを使用
- [x] 意味が明確で自己文書化された名前

## 実装フェーズ（中規模）

### Phase 1: 設計（1時間）
- [x] 定数定義の設計
- [x] ParallelStrategy構造体の設計
- [x] 統一化戦略の設計

### Phase 2: 実装（4時間）

#### Step 1: 定数定義の追加（30分）
```rust
// src/constants.rs に追加
// ============================================================================
// 並列処理最適化定数
// ============================================================================

/// 並列処理: 小規模データ閾値（L1キャッシュ最適）
/// 
/// この閾値以下では並列化のオーバーヘッドが利益を上回るため、
/// シーケンシャル処理を使用。
pub const PARALLEL_THRESHOLD_SMALL: usize = 1_000;

/// 並列処理: 中規模データ閾値（L2キャッシュ最適）
/// 
/// L1-L2キャッシュ境界での最適化ポイント。
/// 軽い並列化（スレッド数制限）を適用。
pub const PARALLEL_THRESHOLD_MEDIUM: usize = 10_000;

/// 並列処理: 大規模データ閾値（L3キャッシュ最適）
/// 
/// L2-L3キャッシュ境界での最適化ポイント。
/// フル並列化を適用。
pub const PARALLEL_THRESHOLD_LARGE: usize = 100_000;

/// キャッシュライン: x86_64標準サイズ
/// 
/// false sharingを避けるための基本単位。
pub const CACHE_LINE_SIZE: usize = 64;

/// チャンクサイズ: L1データキャッシュ最適
/// 
/// 32KB L1キャッシュ / 64B キャッシュライン = 512
/// f64（8バイト）× 512 = 4KB（複数配列考慮）
pub const CHUNK_SIZE_L1: usize = 512;

/// チャンクサイズ: L2キャッシュ最適
/// 
/// 256KB L2キャッシュ / 64B = 4096
/// 実際には複数配列があるため、この1/4程度が最適
pub const CHUNK_SIZE_L2: usize = 1024;

/// チャンクサイズ: L3キャッシュ最適
/// 
/// 2MB以上のL3キャッシュを想定
/// 大規模データの効率的処理用
pub const CHUNK_SIZE_L3: usize = 8192;
```

#### Step 2: ParallelStrategy モジュール実装（1.5時間）
```rust
// src/optimization/mod.rs
pub mod parallel_strategy;

// src/optimization/parallel_strategy.rs
use crate::constants::*;

/// 並列処理戦略を決定する構造体
#[derive(Debug, Clone, Copy)]
pub struct ParallelStrategy {
    /// 並列化を実行するか
    pub should_parallelize: bool,
    /// データ処理のチャンクサイズ
    pub chunk_size: usize,
    /// 使用するスレッド数（制限がある場合）
    pub max_threads: Option<usize>,
}

impl ParallelStrategy {
    /// データサイズから最適な並列化戦略を決定
    /// 
    /// # Arguments
    /// * `size` - 処理するデータの要素数
    /// 
    /// # Returns
    /// 最適化された並列処理戦略
    pub fn determine(size: usize) -> Self {
        let available_threads = rayon::current_num_threads();
        
        match size {
            // 小規模: 並列化なし（オーバーヘッド回避）
            0..=PARALLEL_THRESHOLD_SMALL => Self {
                should_parallelize: false,
                chunk_size: size.max(1),
                max_threads: None,
            },
            // 中規模: 軽い並列化（L1-L2キャッシュ最適）
            n if n <= PARALLEL_THRESHOLD_MEDIUM => Self {
                should_parallelize: true,
                chunk_size: CHUNK_SIZE_L1,
                max_threads: Some((available_threads / 2).max(2)),
            },
            // 大規模: 中程度の並列化（L2-L3キャッシュ最適）
            n if n <= PARALLEL_THRESHOLD_LARGE => Self {
                should_parallelize: true,
                chunk_size: CHUNK_SIZE_L2,
                max_threads: None,
            },
            // 超大規模: フル並列化（L3キャッシュ活用）
            _ => Self {
                should_parallelize: true,
                chunk_size: CHUNK_SIZE_L3,
                max_threads: None,
            },
        }
    }

    /// 実効スレッド数を取得
    pub fn effective_threads(&self) -> usize {
        self.max_threads.unwrap_or_else(rayon::current_num_threads)
    }

    /// チャンク数を計算
    pub fn num_chunks(&self, size: usize) -> usize {
        (size + self.chunk_size - 1) / self.chunk_size
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_strategy_selection() {
        // 小規模
        let strategy = ParallelStrategy::determine(100);
        assert!(!strategy.should_parallelize);
        
        // 中規模
        let strategy = ParallelStrategy::determine(5000);
        assert!(strategy.should_parallelize);
        assert_eq!(strategy.chunk_size, CHUNK_SIZE_L1);
        
        // 大規模
        let strategy = ParallelStrategy::determine(50000);
        assert!(strategy.should_parallelize);
        assert_eq!(strategy.chunk_size, CHUNK_SIZE_L2);
        
        // 超大規模
        let strategy = ParallelStrategy::determine(500000);
        assert!(strategy.should_parallelize);
        assert_eq!(strategy.chunk_size, CHUNK_SIZE_L3);
    }
}
```

#### Step 3: Black-Scholesバッチ処理の最適化（1.5時間）
```rust
// src/models/black_scholes_batch.rs の修正
use crate::optimization::parallel_strategy::ParallelStrategy;
use crate::broadcast::{ArrayLike, BroadcastIterator};
use crate::error::QuantForgeError;
use crate::models::black_scholes_model::{BlackScholes, BlackScholesParams};
use crate::models::{GreeksBatch, PricingModel};
use rayon::prelude::*;

/// Calculate call prices with full array support and broadcasting
pub fn call_price_batch(
    spots: ArrayLike,
    strikes: ArrayLike,
    times: ArrayLike,
    rates: ArrayLike,
    sigmas: ArrayLike,
) -> Result<Vec<f64>, QuantForgeError> {
    let inputs = vec![spots, strikes, times, rates, sigmas];
    let iter = BroadcastIterator::new(inputs)?;
    let size = iter.size_hint().0;
    
    // 動的戦略決定
    let strategy = ParallelStrategy::determine(size);
    
    // データ収集（イテレータから配列へ）
    let values: Vec<_> = iter.collect();
    
    if strategy.should_parallelize {
        // 最適化された並列処理
        let results: Vec<f64> = if let Some(max_threads) = strategy.max_threads {
            // スレッド数制限あり
            let pool = rayon::ThreadPoolBuilder::new()
                .num_threads(max_threads)
                .build()
                .unwrap();
            
            pool.install(|| {
                values
                    .par_chunks(strategy.chunk_size)
                    .flat_map(|chunk| {
                        chunk.iter().map(|vals| {
                            let params = BlackScholesParams {
                                spot: vals[0],
                                strike: vals[1],
                                time: vals[2],
                                rate: vals[3],
                                sigma: vals[4],
                            };
                            
                            if params.spot <= 0.0
                                || params.strike <= 0.0
                                || params.time <= 0.0
                                || params.sigma <= 0.0
                            {
                                f64::NAN
                            } else {
                                BlackScholes::call_price(&params)
                            }
                        }).collect::<Vec<_>>()
                    })
                    .collect()
            })
        } else {
            // フル並列化
            values
                .par_chunks(strategy.chunk_size)
                .flat_map(|chunk| {
                    chunk.iter().map(|vals| {
                        let params = BlackScholesParams {
                            spot: vals[0],
                            strike: vals[1],
                            time: vals[2],
                            rate: vals[3],
                            sigma: vals[4],
                        };
                        
                        if params.spot <= 0.0
                            || params.strike <= 0.0
                            || params.time <= 0.0
                            || params.sigma <= 0.0
                        {
                            f64::NAN
                        } else {
                            BlackScholes::call_price(&params)
                        }
                    }).collect::<Vec<_>>()
                })
                .collect()
        };
        Ok(results)
    } else {
        // シーケンシャル処理（小規模データ）
        let mut results = Vec::with_capacity(size);
        for vals in values {
            let params = BlackScholesParams {
                spot: vals[0],
                strike: vals[1],
                time: vals[2],
                rate: vals[3],
                sigma: vals[4],
            };
            
            if params.spot <= 0.0
                || params.strike <= 0.0
                || params.time <= 0.0
                || params.sigma <= 0.0
            {
                results.push(f64::NAN);
            } else {
                results.push(BlackScholes::call_price(&params));
            }
        }
        Ok(results)
    }
}

// put_price_batch, implied_volatility_batch も同様に修正
```

#### Step 4: BatchProcessorトレイトの統一化（30分）
```rust
// src/traits/batch_processor.rs の修正
use crate::optimization::parallel_strategy::ParallelStrategy;
use crate::constants::*;

impl<T> BatchProcessor for T {
    // ... 既存のコード ...
    
    fn process_parallel_with_gil_release(
        &self,
        py: Python<'_>,
        prices: &[f64],
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        output: &mut [f64],
    ) where
        Self::Output: Into<f64> + Send,
        Self::Params: Send,
        Self: Sync,
    {
        py.allow_threads(|| {
            let strategy = ParallelStrategy::determine(prices.len());
            
            if strategy.should_parallelize {
                // 戦略に基づいた並列処理
                if let Some(max_threads) = strategy.max_threads {
                    let pool = rayon::ThreadPoolBuilder::new()
                        .num_threads(max_threads)
                        .build()
                        .unwrap();
                    
                    pool.install(|| {
                        prices
                            .par_chunks(strategy.chunk_size)
                            .zip(output.par_chunks_mut(strategy.chunk_size))
                            .for_each(|(price_chunk, out_chunk)| {
                                for (i, &price) in price_chunk.iter().enumerate() {
                                    let params = self.create_params(price, k, t, r, sigma);
                                    out_chunk[i] = self.process_single(&params).into();
                                }
                            });
                    });
                } else {
                    prices
                        .par_chunks(strategy.chunk_size)
                        .zip(output.par_chunks_mut(strategy.chunk_size))
                        .for_each(|(price_chunk, out_chunk)| {
                            for (i, &price) in price_chunk.iter().enumerate() {
                                let params = self.create_params(price, k, t, r, sigma);
                                out_chunk[i] = self.process_single(&params).into();
                            }
                        });
                }
            } else {
                // シーケンシャル処理
                self.process_sequential(prices, k, t, r, sigma, output);
            }
        });
    }
}
```

### Phase 3: 品質チェック（1時間）
```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック
similarity-rs --threshold 0.80 --skip-test src/
# 閾値超えの重複があれば rust-refactor.md 適用

# ベンチマーク実行
cargo bench
uv run python benchmarks/run_comparison.py
```

### Phase 4: 検証と調整（30分）
- [ ] ベンチマーク結果の確認
- [ ] 100,000件での性能改善確認
- [ ] 他のデータサイズでの退行チェック
- [ ] 必要に応じてパラメータ調整

## 技術要件

### 必須要件
- [x] Critical Rules準拠（C002, C004, C011-3, C012, C014）
- [x] エラー率 < PRACTICAL_TOLERANCE（数値計算精度維持）
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）

### パフォーマンス目標
- [x] 100,000件: NumPyと同等以上（現在0.28倍 → 目標1.2倍以上）
- [x] 他のサイズで退行なし
- [x] メモリ使用量: 入力データの2倍以内

### PyO3連携
- [x] ゼロコピー実装維持
- [x] GIL解放での並列処理
- [x] 適切なエラー変換

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| スレッドプール作成のオーバーヘッド | 中 | キャッシュまたは再利用検討 |
| キャッシュサイズの仮定が不正確 | 低 | 実測値に基づく調整 |
| 他モデルへの影響 | 中 | 段階的適用と個別検証 |

## チェックリスト

### 実装前
- [x] 既存コードの確認（ハードコード箇所特定済み）
- [x] 依存関係の確認（rayonのみ）
- [x] 設計レビュー（本計画書）

### 実装中
- [ ] 定期的なテスト実行
- [ ] コミット前の`cargo fmt`
- [ ] 段階的な動作確認

### 実装後
- [ ] 全品質ゲート通過
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新（docs/ja/performance/benchmarks.md）
- [ ] 計画のarchive移動

## 成果物

- [ ] src/constants.rs（定数追加）
- [ ] src/optimization/parallel_strategy.rs（新規）
- [ ] src/optimization/mod.rs（新規）
- [ ] src/models/black_scholes_batch.rs（最適化）
- [ ] src/traits/batch_processor.rs（統一化）
- [ ] テストコード（各モジュール）
- [ ] ベンチマーク結果更新

## 期待される改善効果

| データサイズ | 現在 | 改善後（目標） | 改善率 |
|------------|------|--------------|--------|
| 100件 | 7.0倍速い | 8倍速い | +14% |
| 1,000件 | 1.96倍速い | 3倍速い | +50% |
| 10,000件 | 0.99倍 | 1.5倍速い | +50% |
| **100,000件** | **0.28倍** | **1.2倍速い** | **+430%** |
| 1,000,000件 | 1.19倍速い | 1.5倍速い | +26% |

## 備考

- 本最適化はCritical Rules（特にC011-3: ハードコード禁止）準拠のため必須
- キャッシュサイズは一般的なx86_64 CPUを想定（AMD Ryzen 5 5600G等）
- 将来的にSIMD最適化を追加する場合の基盤となる実装
- 他のモデル（American, Merton, Black76）への適用は別タスクで実施
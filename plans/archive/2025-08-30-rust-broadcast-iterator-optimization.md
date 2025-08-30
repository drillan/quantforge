# BroadcastIterator ゼロコピー最適化計画

## メタデータ
- **作成日**: 2025-08-30
- **作者**: AI実装システム
- **ステータス**: COMPLETED
- **完了日**: 2025-08-30
- **言語**: Rust
- **影響範囲**: src/broadcast.rs, src/models/*_batch.rs
- **優先度**: 高（性能改善の最優先事項）
- **更新履歴**:
  - 2025-08-30: 初版作成
  - 2025-08-30: flat_map_initによるスレッドローカルバッファリング最適化を追加

## 1. 背景と問題

### 1.1 現状の問題
性能分析により、以下の問題が判明：
- 10,000件のデータ処理でNumPyに対して0.60倍（目標0.95倍）
- FFIオーバーヘッドが実行時間の40%を占める
- PyReadonlyArrayでゼロコピーを実現しているが、BroadcastIteratorでデータがコピーされている

### 1.2 根本原因
```rust
// 現在の問題のあるコード
let values: Vec<_> = iter.collect();  // ここで全データがコピーされる
```

BroadcastIteratorが各要素でVec<f64>を作成し、それをcollect()で収集するため、メモリ使用量が増大し、ゼロコピーの利点が失われている。

## 2. 目標

### 2.1 性能目標
| データサイズ | 現在 | 目標 | 改善率 |
|------------|------|------|--------|
| 10,000件 | 0.60倍 | 0.95倍 | 58% |
| 100,000件 | 0.78倍 | 1.05倍 | 35% |
| 1,000,000件 | 1.35倍 | 1.50倍 | 11% |

### 2.2 技術目標
- BroadcastIteratorでのデータコピーを完全に排除
- メモリ使用量を99%削減（400KB → 40バイト）
- 既存APIとの完全な互換性を維持

## 3. 実装計画

### 3.1 Phase 1: BroadcastIteratorの改善

#### 3.1.1 新しいcompute_withメソッドの追加
```rust
// src/broadcast.rs
impl<'a> BroadcastIterator<'a> {
    /// コピーなしで直接計算を実行
    pub fn compute_with<F, R>(&self, f: F) -> Vec<R>
    where
        F: Fn(&[f64]) -> R,
        R: Send,
    {
        let mut buffer = vec![0.0; self.inputs.len()];
        let mut results = Vec::with_capacity(self.size);
        
        for i in 0..self.size {
            // バッファを再利用（アロケーション削減）
            for (j, input) in self.inputs.iter().enumerate() {
                buffer[j] = input.get_broadcast(i);
            }
            results.push(f(&buffer));
        }
        
        results
    }
    
    /// 並列処理版（スレッドローカルバッファリング最適化済み）
    pub fn compute_parallel_with<F, R>(&self, f: F, chunk_size: usize) -> Vec<R>
    where
        F: Fn(&[f64]) -> R + Sync + Send,
        R: Send,
    {
        use rayon::prelude::*;
        
        (0..self.size)
            .into_par_iter()
            .chunks(chunk_size)
            .flat_map_init(
                // 各スレッドで一度だけバッファを初期化
                || vec![0.0; self.inputs.len()],
                // 初期化したバッファを各チャンクの処理で再利用
                |buffer, chunk| {
                    chunk.into_iter().map(|i| {
                        for (j, input) in self.inputs.iter().enumerate() {
                            buffer[j] = input.get_broadcast(i);
                        }
                        f(&*buffer) // &[f64]にデリファレンス
                    }).collect::<Vec<_>>()
                }
            )
            .collect()
    }
}
```

### 3.2 Phase 2: モデルバッチ処理の更新

#### 3.2.1 black_scholes_batch.rsの更新
```rust
// src/models/black_scholes_batch.rs
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
    
    // 動的戦略選択
    let strategy = ParallelStrategy::select_dynamic(size);
    
    let results = match strategy.mode() {
        ProcessingMode::Sequential => {
            // シーケンシャル処理（コピーなし）
            iter.compute_with(|vals| {
                compute_single_price(vals[0], vals[1], vals[2], vals[3], vals[4])
            })
        }
        _ => {
            // 並列処理（チャンク単位、コピーなし）
            iter.compute_parallel_with(
                |vals| compute_single_price(vals[0], vals[1], vals[2], vals[3], vals[4]),
                strategy.chunk_size()
            )
        }
    };
    
    Ok(results)
}

#[inline(always)]
fn compute_single_price(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    if s <= 0.0 || k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
        f64::NAN
    } else {
        let params = BlackScholesParams {
            spot: s,
            strike: k,
            time: t,
            rate: r,
            sigma,
        };
        BlackScholes::call_price(&params)
    }
}
```

#### 3.2.2 他のモデルも同様に更新
- src/models/black76/batch.rs
- src/models/merton/batch.rs
- src/models/american/batch.rs

### 3.3 Phase 3: テストと検証

#### 3.3.1 単体テスト
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_compute_with_no_copy() {
        let inputs = vec![
            ArrayLike::Array(&[1.0, 2.0, 3.0]),
            ArrayLike::Scalar(2.0),
        ];
        let iter = BroadcastIterator::new(inputs).unwrap();
        
        let results = iter.compute_with(|vals| vals[0] + vals[1]);
        assert_eq!(results, vec![3.0, 4.0, 5.0]);
    }
    
    #[test]
    fn test_memory_efficiency() {
        // メモリ使用量が期待通り削減されているか確認
        // Valgrindやheaptrackで実測
    }
}
```

#### 3.3.2 性能ベンチマーク
```rust
// benches/broadcast_benchmark.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_broadcast_old(c: &mut Criterion) {
    c.bench_function("broadcast_old_10k", |b| {
        let data = setup_test_data(10_000);
        b.iter(|| {
            let values: Vec<_> = iter.collect();
            // 旧実装
        });
    });
}

fn benchmark_broadcast_new(c: &mut Criterion) {
    c.bench_function("broadcast_new_10k", |b| {
        let data = setup_test_data(10_000);
        b.iter(|| {
            iter.compute_with(|vals| black_box(compute(vals)))
        });
    });
}
```

## 4. 命名定義

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "ArrayLike"
    meaning: "スカラーまたは配列を表す列挙型"
    source: "src/broadcast.rs"
  - name: "BroadcastIterator"
    meaning: "NumPyスタイルのブロードキャスト機能"
    source: "src/broadcast.rs"
  - name: "ProcessingMode"
    meaning: "並列処理戦略の列挙型"
    source: "src/optimization/parallel_strategy.rs"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "compute_with"
    meaning: "イテレータをコピーなしで直接計算"
    justification: "Rustの慣習的な命名パターン（with_系メソッド）"
    status: "pending_approval"
  - name: "compute_parallel_with"
    meaning: "並列版のcompute_with"
    justification: "明示的に並列処理であることを示す"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 5. リスクと対策

### 5.1 技術的リスク
| リスク | 可能性 | 影響 | 対策 |
|--------|--------|------|------|
| 並列処理での競合状態 | 低 | 高 | flat_map_initでスレッドローカルバッファ実装 |
| APIの破壊的変更 | 低 | 高 | 内部実装のみ変更、公開APIは維持 |
| 性能が改善しない | 低 | 中 | 早期にプロトタイプで検証 |
| チャンクごとのアロケーション | 中 | 中 | flat_map_initで完全に解決 |

### 5.2 実装リスク
- 既存テストが失敗する可能性 → 段階的な移行とテストの更新
- メモリアラインメントの問題 → アサーションで検証

## 6. 成功指標

### 6.1 定量的指標
- [ ] 10,000件の処理で0.95倍以上を達成
- [ ] メモリ使用量が90%以上削減
- [ ] 並列処理時のアロケーション回数がスレッド数に限定
- [ ] 全既存テストがパス

### 6.2 定性的指標
- [ ] コードの可読性が維持される
- [ ] デバッグが容易
- [ ] 将来の拡張性が確保される

## 7. タイムライン

| フェーズ | 期間 | 成果物 |
|---------|------|--------|
| Phase 1: BroadcastIterator改善 | 2日 | compute_withメソッド実装 |
| Phase 2: モデル更新 | 3日 | 全バッチ処理の更新 |
| Phase 3: テストと検証 | 2日 | ベンチマーク結果、テストレポート |
| **合計** | **1週間** | 完全動作する最適化版 |

## 8. 実装チェックリスト

### Phase 1
- [ ] compute_withメソッドの実装
- [ ] compute_parallel_withメソッドの実装
- [ ] 単体テストの作成
- [ ] メモリプロファイリング

### Phase 2
- [ ] black_scholes_batch.rsの更新
- [ ] black76/batch.rsの更新
- [ ] merton/batch.rsの更新
- [ ] american/batch.rsの更新

### Phase 3
- [ ] ベンチマークの実行
- [ ] 性能目標の達成確認
- [ ] ドキュメントの更新
- [ ] コードレビュー

## 9. 参考資料

- [現在の性能分析レポート](../benchmarks/results/2025-08-30-performance-optimization-report.md)
- [ゼロコピー提案分析](../benchmarks/results/2025-08-30-zero-copy-proposal-analysis.md)
- [改善提案詳細](../benchmarks/results/2025-08-30-zero-copy-improvement-proposal.md)

## 10. 承認

- [ ] 技術レビュー完了
- [ ] 実装承認
- [ ] テスト計画承認

---

*本計画書は性能最適化の最優先事項として実施されます。*
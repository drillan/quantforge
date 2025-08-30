# [Rust] 現実的なパフォーマンス最適化計画

## メタデータ
- **作成日**: 2025-08-30
- **言語**: Rust
- **ステータス**: COMPLETED
- **完了日**: 2025-08-30
- **推定規模**: 小規模
- **推定コード行数**: 50行（主に定数調整）
- **対象モジュール**: src/constants.rs, src/optimization/, playground/profiling/

## 背景

### アンチパターンからの学習
- **SIMD最適化**: 2025-08-27に210行削除済み → 永遠に不要
- **段階的実装**: Critical Rules違反 → 理想実装のみ
- **早すぎる最適化**: 測定なしの推測 → プロファイリング必須

詳細: @.claude/antipatterns/README.md

### 現在の問題（実測済み）
| データサイズ | QuantForge | NumPy | 相対性能 | 問題 |
|------------|------------|--------|---------|------|
| 10,000件 | 631 μs | 560 μs | 0.89倍 | ❌ |
| 100,000件 | 6,452 μs | 4,947 μs | 0.77倍 | ❌ |

原因: 並列化閾値が低すぎる（1,000件で並列化開始）

## 実装計画（プロファイリング駆動）

### Phase 1: プロファイリング環境構築（1時間）

#### 1.1 flamegraphセットアップ
```bash
# playground/profiling/setup.sh
#!/bin/bash
cargo install flamegraph
cargo install cargo-profiling

# プロファイル用ビルド
cargo build --release --features profiling
```

#### 1.2 測定ハーネス作成
```rust
// playground/profiling/bench_harness.rs
use quantforge::models::black_scholes::*;
use std::time::Instant;

fn measure_threshold(threshold: usize, data_size: usize) -> f64 {
    // 閾値を動的に設定して測定
    std::env::set_var("PARALLEL_THRESHOLD", threshold.to_string());
    
    let spots = vec![100.0; data_size];
    let start = Instant::now();
    let _ = call_price_batch(&spots, 100.0, 1.0, 0.05, 0.2);
    start.elapsed().as_secs_f64()
}

fn main() {
    // 10^2から10^6まで対数的にテスト
    let sizes = [100, 1000, 10_000, 100_000, 1_000_000];
    let thresholds = [100, 500, 1000, 5000, 10_000, 50_000, 100_000];
    
    println!("size,threshold,time_ms");
    for size in sizes {
        for threshold in thresholds {
            let time = measure_threshold(threshold, size);
            println!("{},{},{:.3}", size, threshold, time * 1000.0);
        }
    }
}
```

### Phase 2: 実測に基づく閾値調整（30分）

#### 2.1 定数調整（ハードコード違反の修正含む）
```rust
// src/constants.rs の修正
// 実測値に基づく調整（プロファイリング後に決定）
pub const PARALLEL_THRESHOLD_SMALL: usize = 50_000;   // 1,000 → 50,000
pub const PARALLEL_THRESHOLD_MEDIUM: usize = 200_000; // 10,000 → 200,000
pub const PARALLEL_THRESHOLD_LARGE: usize = 1_000_000; // 100,000 → 1,000,000
```

#### 2.2 ハードコード違反の修正
```rust
// src/models/black_scholes_parallel.rs（30行目）
- const PARALLEL_THRESHOLD: usize = 30000;  // ハードコード
+ use crate::constants::PARALLEL_THRESHOLD_MEDIUM;

// src/models/greeks_parallel.rs（13行目）
- const PARALLEL_THRESHOLD: usize = 30_000;  // ハードコード
+ use crate::constants::PARALLEL_THRESHOLD_MEDIUM;

// src/models/implied_volatility.rs（270行目）
- const PARALLEL_THRESHOLD: usize = 1000;  // ハードコード
+ use crate::constants::PARALLEL_THRESHOLD_SMALL;
```

### Phase 3: キャッシュ最適化（30分）

#### 3.1 ループアンローリング
```rust
// src/models/black_scholes_batch.rs に追加
#[inline(always)]
fn process_chunk_4(chunk: &[f64], k: f64, t: f64, r: f64, sigma: f64) -> [f64; 4] {
    // コンパイラが自動ベクトル化しやすい形
    let (s0, s1, s2, s3) = (chunk[0], chunk[1], chunk[2], chunk[3]);
    [
        black_scholes_call(s0, k, t, r, sigma),
        black_scholes_call(s1, k, t, r, sigma),
        black_scholes_call(s2, k, t, r, sigma),
        black_scholes_call(s3, k, t, r, sigma),
    ]
}
```

#### 3.2 プリフェッチヒント
```rust
// コンパイラヒントの追加
#[cold]
fn handle_error_path() { /* まれなエラー処理 */ }

#[inline(always)]
fn hot_path_calculation() { /* 頻繁に呼ばれる計算 */ }
```

### Phase 4: 検証（30分）

#### 4.1 ベンチマーク実行
```bash
# 改善前
uv run python benchmarks/run_practical_scenarios.py > before.txt

# 改善後
uv run python benchmarks/run_practical_scenarios.py > after.txt

# 比較
diff before.txt after.txt
```

#### 4.2 成功基準
| データサイズ | 現在 | 目標 | 許容範囲 |
|------------|------|------|---------|
| 10,000件 | 0.89倍 | 1.5倍 | ±10% |
| 100,000件 | 0.77倍 | 1.0倍 | ±10% |

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 測定環境の影響 | 中 | 複数回測定、中央値使用 |
| プラットフォーム依存 | 低 | 環境変数で調整可能に |
| 小規模データの退行 | 低 | 閾値調整で対応 |

## チェックリスト

### 実装前
- [ ] アンチパターン文書を確認
- [ ] プロファイリング環境構築
- [ ] ベースライン測定

### 実装中
- [ ] ハードコード違反の修正
- [ ] 測定に基づく調整のみ
- [ ] 推測による最適化禁止

### 実装後
- [ ] ベンチマーク実行
- [ ] 目標達成確認
- [ ] ドキュメント更新

## 期待される改善

### 現実的な目標
- **小規模（〜1,000）**: 現状維持（既に10倍高速）
- **中規模（10,000）**: NumPyの1.5倍（閾値調整で実現）
- **大規模（100,000+）**: NumPyと同等（十分な成果）

### 改善しないこと
- SIMD実装（永遠に不要）
- 複雑な最適化（保守性優先）
- NumPyを圧倒的に超える性能（非現実的）

## サブタスク

### プロファイリング駆動イテレーション
詳細な実装計画: [plans/2025-08-30-profiling-iteration-subtask.md](./2025-08-30-profiling-iteration-subtask.md)

- 最大10回のイテレーションで系統的に最適化
- プロファイリングツールによるボトルネック特定
- データ駆動の閾値調整
- 明確な収束条件と打ち切り条件

## 結論

**測定に基づく最小限の調整で最大の効果を狙う**

主な変更:
1. 並列化閾値を50,000に調整（実測値）
2. ハードコード違反の修正（C011-3準拠）
3. 簡単なキャッシュ最適化

これにより、10,000件でNumPyの1.5倍程度の性能を達成可能。

## 参考資料

- アンチパターン集: @.claude/antipatterns/README.md
- 測定データ: debug/2025-08-30-parallel-processing-performance-issue.md
- Critical Rules: @.claude/critical-rules.xml
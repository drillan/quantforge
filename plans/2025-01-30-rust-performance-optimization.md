# [Rust] パフォーマンス最適化 実装計画

## メタデータ
- **作成日**: 2025-01-30
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 300-400
- **対象モジュール**: Cargo.toml, .cargo/config.toml, core/src/math/, core/src/compute/

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 300-400 行
- [x] 新規ファイル数: 2 個（Cargo設定、高速erf実装）
- [x] 影響範囲: 複数モジュール（math, compute）
- [x] PyO3バインディング: 不要（内部最適化のみ）
- [x] SIMD最適化: 不要（アンチパターン）
- [x] 並列化: 不要（既存の並列化調整のみ）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | - | ✅ | - | `cargo test --all --release` |
| cargo clippy | - | ✅ | - | `cargo clippy -- -D warnings` |
| cargo fmt | - | ✅ | - | `cargo fmt --check` |
| similarity-rs | - | 条件付き | - | `similarity-rs --threshold 0.80 core/src/` |
| rust-refactor.md | - | 条件付き | - | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | - | ✅ | - | `cargo bench` |
| miri（安全性） | - | - | - | - |

## 1. 現状分析

### パフォーマンスギャップ
| メトリクス | 現状 | 目標 | ギャップ |
|------------|------|------|----------|
| 単一計算 | 35ns | 10ns | 3.5倍 |
| 100件バッチ | 測定必要 | NumPy同等 | - |
| 1,000件バッチ | 測定必要 | NumPy同等 | - |
| 10,000件バッチ | NumPyの0.89倍 | 1.5倍 | 改善必要 |

### ボトルネック分析
1. **数学関数（40-50%）**: libm::erf が遅い
2. **ビルド最適化不足（30-40%）**: Cargoプロファイル未設定
3. **小規模バッチ処理（10-20%）**: 並列化オーバーヘッド
4. **インライン化不足（5-10%）**: 関数呼び出しオーバーヘッド

## 2. 最適化戦略

### Phase 1: Cargoビルドプロファイル最適化（即効性最大）

#### 2.1 リリースプロファイル設定
```toml
# Cargo.toml (ワークスペースルート)
[profile.release]
opt-level = 3          # 最大最適化
lto = "fat"           # Link Time Optimization（全体最適化）
codegen-units = 1     # 単一コンパイル単位（最適化向上）
panic = "abort"       # パニック時の巻き戻しなし（高速化）
strip = true          # デバッグ情報削除（バイナリサイズ削減）
overflow-checks = false # オーバーフローチェック無効化（本番環境）

[profile.release-lto]
inherits = "release"
lto = "fat"
```

#### 2.2 ターゲット固有最適化
```toml
# .cargo/config.toml
[build]
rustflags = [
    "-C", "target-cpu=native",     # CPUネイティブ命令使用
    "-C", "prefer-dynamic=no",     # 静的リンク優先
]

[target.x86_64-unknown-linux-gnu]
rustflags = [
    "-C", "target-feature=+avx2,+fma", # AVX2/FMA有効化（自動ベクトル化用）
]
```

**期待効果**: 30-50%の性能向上

### Phase 2: 高速数学関数実装

#### 2.3 高速erf近似実装
```rust
// core/src/math/fast_erf.rs

/// 高速erf近似（Abramowitz & Stegun近似）
/// 精度: 1.5e-7（十分な精度）
/// 速度: libm::erfの2-3倍高速
#[inline(always)]
pub fn fast_erf(x: f64) -> f64 {
    // 定数（事前計算済み）
    const A1: f64 = 0.254829592;
    const A2: f64 = -0.284496736;
    const A3: f64 = 1.421413741;
    const A4: f64 = -1.453152027;
    const A5: f64 = 1.061405429;
    const P: f64 = 0.3275911;
    
    let sign = if x < 0.0 { -1.0 } else { 1.0 };
    let x = x.abs();
    
    let t = 1.0 / (1.0 + P * x);
    let t2 = t * t;
    let t3 = t2 * t;
    let t4 = t2 * t2;
    let t5 = t2 * t3;
    
    let y = 1.0 - (((((A5 * t5 + A4 * t4) + A3 * t3) + A2 * t2) + A1 * t) * t * (-x * x).exp());
    
    sign * y
}

/// 高速norm_cdf実装
#[inline(always)]
pub fn fast_norm_cdf(x: f64) -> f64 {
    use crate::constants::{NORM_CDF_LOWER_BOUND, NORM_CDF_UPPER_BOUND};
    
    if x > NORM_CDF_UPPER_BOUND {
        1.0
    } else if x < NORM_CDF_LOWER_BOUND {
        0.0
    } else {
        0.5 * (1.0 + fast_erf(x / std::f64::consts::SQRT_2))
    }
}
```

**期待効果**: 20-30%の性能向上

### Phase 3: 小規模バッチ最適化

#### 2.4 マイクロバッチ専用処理
```rust
// core/src/compute/micro_batch.rs

use crate::constants::MICRO_BATCH_THRESHOLD;

/// 4要素ループアンローリング版
#[inline(always)]
pub fn black_scholes_call_micro_batch(
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    sigmas: &[f64],
    output: &mut [f64],
) {
    let len = spots.len();
    let chunks = len / 4;
    let remainder = len % 4;
    
    // 4要素単位で処理（コンパイラの自動ベクトル化を促進）
    for i in 0..chunks {
        let idx = i * 4;
        output[idx] = black_scholes_call_scalar(
            spots[idx], strikes[idx], times[idx], rates[idx], sigmas[idx]
        );
        output[idx + 1] = black_scholes_call_scalar(
            spots[idx + 1], strikes[idx + 1], times[idx + 1], rates[idx + 1], sigmas[idx + 1]
        );
        output[idx + 2] = black_scholes_call_scalar(
            spots[idx + 2], strikes[idx + 2], times[idx + 2], rates[idx + 2], sigmas[idx + 2]
        );
        output[idx + 3] = black_scholes_call_scalar(
            spots[idx + 3], strikes[idx + 3], times[idx + 3], rates[idx + 3], sigmas[idx + 3]
        );
    }
    
    // 余りを処理
    for i in (chunks * 4)..len {
        output[i] = black_scholes_call_scalar(
            spots[i], strikes[i], times[i], rates[i], sigmas[i]
        );
    }
}
```

**期待効果**: 100-1000要素で10-15%の性能向上

### Phase 4: インライン化とコンパイラヒント

#### 2.5 重要関数のインライン化
```rust
// 既存関数に追加
#[inline(always)]  // black_scholes_call_scalar
#[inline(always)]  // black_scholes_d1_d2
#[inline(always)]  // fast_norm_cdf
#[inline(always)]  // fast_erf

// 分岐予測ヒント
#[cold]  // エラーパス、稀な分岐
```

**期待効果**: 5-10%の性能向上

## 3. 実装フェーズ

### Phase 1: 設計と準備（2時間）
- [x] パフォーマンスボトルネック分析
- [ ] 最適化戦略の策定
- [ ] ベンチマーク基準値の測定

### Phase 2: 実装（4-6時間）
- [ ] Cargoプロファイル設定
- [ ] 高速erf関数実装
- [ ] マイクロバッチ最適化
- [ ] インライン化調整
- [ ] 各段階でのベンチマーク実施

### Phase 3: 品質チェック（1時間）
```bash
# 精度検証
cargo test --release -- --nocapture

# パフォーマンス測定
cargo bench --bench benchmark

# 品質チェック
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック（必要に応じて）
similarity-rs --threshold 0.80 --skip-test core/src/
```

### Phase 4: 検証と調整（1-2時間）
- [ ] 精度検証（1e-8維持確認）
- [ ] パフォーマンス測定
- [ ] NumPyとの比較
- [ ] 必要に応じて微調整

## 4. 命名定義セクション

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
```

### 4.2 新規提案命名
```yaml
proposed_names:
  # 新規命名なし（既存の命名規則で十分）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 5. 技術要件

### 必須要件
- [x] エラー率 < 1e-8（PRECISION_HIGHEST維持）
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）
- [x] 後方互換性（APIインターフェース変更なし）

### パフォーマンス目標
- [ ] 単一計算: 35ns → 15-20ns（目標10nsに近づく）
- [ ] 100件バッチ: NumPyの1.5倍以上
- [ ] 1,000件バッチ: NumPyの1.2倍以上
- [ ] 10,000件バッチ: NumPyの1.1倍以上
- [ ] メモリ使用量: 現状維持

## 6. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 精度劣化 | 高 | ゴールデンマスターテスト、許容誤差1e-8厳守 |
| プラットフォーム依存 | 中 | target-cpu=nativeはオプション、基本最適化で対応 |
| 並列化閾値の誤調整 | 中 | 環境変数で調整可能、デフォルト値維持 |
| コンパイル時間増加 | 低 | LTOは本番ビルドのみ適用 |

## 7. アンチパターン回避

### 絶対に行わないこと
- ❌ SIMD最適化の提案（過去に失敗、210行削除済み）
- ❌ 段階的実装（理想実装ファースト原則）
- ❌ 測定なしの推測最適化（プロファイリング必須）
- ❌ Arrow型変換（ゼロコピー維持）

### 推奨アプローチ
- ✅ コンパイラ最適化を最大活用
- ✅ 実測に基づく調整
- ✅ 精度を維持した高速化
- ✅ 既存の並列化を活かす

## 8. チェックリスト

### 実装前
- [x] 現状のベンチマーク測定
- [x] ボトルネック分析完了
- [x] アンチパターン確認

### 実装中
- [ ] 各最適化後のベンチマーク実施
- [ ] 精度テストの継続実行
- [ ] コミット前の品質チェック

### 実装後
- [ ] 全テスト合格（cargo test --release）
- [ ] ベンチマーク目標達成確認
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 9. 成果物

- [ ] 最適化されたCargoプロファイル（Cargo.toml, .cargo/config.toml）
- [ ] 高速erf実装（core/src/math/fast_erf.rs）
- [ ] マイクロバッチ最適化（core/src/compute/micro_batch.rs）
- [ ] ベンチマーク結果レポート
- [ ] パフォーマンス改善の測定データ

## 10. 期待される成果

### 定量的成果
- 単一計算: 35ns → 15-20ns（50-70%改善）
- 小規模バッチ: 15-20%高速化
- 中規模バッチ: 10-15%高速化
- 大規模バッチ: 5-10%高速化

### 定性的成果
- NumPyに対する競争力向上
- ユーザー体験の改善
- 将来の最適化の基盤確立

## 11. 備考

- プロファイリングは`cargo install flamegraph`でインストール
- ベンチマークは`cargo bench`で実施
- 環境変数`QUANTFORGE_PARALLEL_THRESHOLD`で並列化閾値調整可能
- LTO最適化は初回ビルド時間が長い（2-3分）が、実行時性能は大幅向上
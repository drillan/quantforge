# [Rust] パフォーマンス最適化実装計画

## メタデータ
- **作成日**: 2025-08-25
- **キャンセル日**: 2025-08-25
- **言語**: Rust
- **ステータス**: CANCELLED
- **推定規模**: 中
- **推定コード行数**: 300-400
- **対象モジュール**: src/math/distributions.rs, src/models/black_scholes.rs, benches/

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 300-400 行
- [x] 新規ファイル数: 2 個（高速近似関数モジュール、SIMDユーティリティ）
- [x] 影響範囲: 複数モジュール（math, models）
- [x] PyO3バインディング: 不要（既存APIを維持）
- [x] SIMD最適化: 必要
- [x] 並列化: 既存のバッチ処理を改善

### 規模判定結果
**中規模タスク**

## ⚠️ キャンセル理由

**この計画はerfベース実装により無効化されました。**

- norm_cdf実装がAbramowitz-Stegun（精度~1e-5）からerf（精度<1e-15）に変更
- 高速近似（3次多項式）が不要に
- 新計画: `plans/2025-08-25-erf-based-optimization-strategy.md`

## 背景と動機（当初）

精度設定が階層化（PRACTICAL: 1e-3, THEORETICAL: 1e-5, NUMERICAL: 1e-7）されたことと、ZERO HARDCODE POLICYの導入により、以下の最適化戦略を実施：

1. **精度レベル別の最適化実装**
   - 現在: norm_cdfは約1e-5精度（実装限界）
   - 改善: 用途別に最適化レベルを選択可能にする
     - PRACTICAL用: 3次多項式近似（1e-3精度、30%高速化）
     - THEORETICAL用: 現行実装維持（1e-5精度）
     - NUMERICAL用: 高精度版を別途検討

2. **SIMD実装の本格導入**
   - 現在: プレースホルダーのみ（norm_cdf_simd未実装）
   - 改善: AVX2/AVX-512による8要素同時処理（4-8倍高速化）
   - 精度レベルごとにSIMD実装を用意

3. **マジックナンバーの完全排除**
   - すべての数値定数を適切に命名・文書化
   - 高速近似の係数もconst定義で管理
   - アルゴリズムパラメータの明確化

## 品質管理ツール（Rust）

### 適用ツール
| ツール | 中規模 | 実行コマンド |
|--------|--------|-------------|
| cargo test | ✅ | `cargo test --all` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| similarity-rs | 条件付き | `similarity-rs --threshold 0.80 src/` |
| cargo bench | ✅ | `cargo bench` |

## 実装フェーズ

### Phase 1: 設計と準備（1時間）
- [x] 現状のベンチマーク実行と基準値記録
- [ ] 高速近似アルゴリズムの選定
- [ ] SIMD実装方針の決定
- [ ] テスト精度基準の確認

### Phase 2: 高速近似関数実装（2-3時間）

#### 2.1 norm_cdf最適化（ZERO HARDCODE準拠）
```rust
// src/math/distributions.rs に追加
use crate::constants::{PRACTICAL_TOLERANCE, THEORETICAL_TOLERANCE};

// 定数定義（マジックナンバー排除）
const NORM_CDF_PRACTICAL_UPPER_BOUND: f64 = 5.0;  // 実務精度での実質的な上限
const NORM_CDF_THEORETICAL_UPPER_BOUND: f64 = 8.0;  // 理論精度での実質的な上限

/// 実務精度（PRACTICAL_TOLERANCE）向け高速版
/// 3次多項式近似を使用し、約30%の高速化を実現
pub fn norm_cdf_practical(x: f64) -> f64 {
    if x > NORM_CDF_PRACTICAL_UPPER_BOUND { return 1.0; }
    if x < -NORM_CDF_PRACTICAL_UPPER_BOUND { return 0.0; }
    
    // 3次多項式係数（Hart, 1968）
    const A1_PRACTICAL: f64 = 0.4361836;
    const A2_PRACTICAL: f64 = -0.1201676;
    const A3_PRACTICAL: f64 = 0.9372980;
    const P_PRACTICAL: f64 = 0.33267;
    
    // 実装...
}

/// 理論精度（THEORETICAL_TOLERANCE）版 - 現行実装
pub fn norm_cdf_theoretical(x: f64) -> f64 {
    // 既存のnorm_cdf実装を使用
    norm_cdf(x)
}
```

#### 2.2 高速数学関数モジュール（定数管理徹底）
```rust
// src/math/fast_math.rs (新規)
use crate::constants::PRACTICAL_TOLERANCE;

/// 高速近似関数用の定数定義
mod constants {
    /// exp近似の最大入力値
    pub const EXP_APPROX_MAX_INPUT: f64 = 88.0;  // exp(88) ≈ 1.6e38
    
    /// log近似の最小入力値
    pub const LOG_APPROX_MIN_INPUT: f64 = 1e-308;  // 浮動小数点の最小正規化数に近い
    
    /// Newton-Raphson法の最大反復回数
    pub const NEWTON_MAX_ITERATIONS: usize = 5;  // 実務精度には十分
}

pub mod fast {
    use super::constants::*;
    
    /// 高速exp近似（精度: PRACTICAL_TOLERANCE）
    pub fn exp_approx(x: f64) -> f64 { 
        if x > EXP_APPROX_MAX_INPUT { return f64::INFINITY; }
        // Schraudolph近似実装...
    }
    
    /// 高速log近似（精度: PRACTICAL_TOLERANCE）
    pub fn log_approx(x: f64) -> f64 { 
        if x < LOG_APPROX_MIN_INPUT { return f64::NEG_INFINITY; }
        // ビット操作による高速近似...
    }
}
```

### Phase 3: SIMD実装（3-4時間）

#### 3.1 SIMD基盤整備
```rust
// src/simd/mod.rs (新規)
#[cfg(target_arch = "x86_64")]
use std::arch::x86_64::*;

pub struct SimdOps;

impl SimdOps {
    #[target_feature(enable = "avx2")]
    unsafe fn norm_cdf_avx2(values: &[f64]) -> Vec<f64> { ... }
}
```

#### 3.2 動的ディスパッチ（精度レベル対応）
```rust
use crate::constants::{PRACTICAL_TOLERANCE, THEORETICAL_TOLERANCE};

// バッチサイズ定数（ZERO HARDCODE準拠）
const SIMD_OPTIMAL_BATCH_SIZE: usize = 8192;  // L1キャッシュに収まる最適サイズ
const SIMD_MIN_BATCH_SIZE: usize = 64;  // SIMD化する最小要素数

/// 精度レベルを指定可能なバッチ処理
pub fn norm_cdf_batch_with_tolerance(values: &[f64], tolerance: f64) -> Vec<f64> {
    // 小さなバッチはスカラー処理
    if values.len() < SIMD_MIN_BATCH_SIZE {
        return norm_cdf_scalar_with_tolerance(values, tolerance);
    }
    
    // CPU機能と精度レベルに応じた実装選択
    if is_x86_feature_detected!("avx2") {
        unsafe { 
            match tolerance {
                t if t >= PRACTICAL_TOLERANCE => norm_cdf_avx2_practical(values),
                t if t >= THEORETICAL_TOLERANCE => norm_cdf_avx2_theoretical(values),
                _ => norm_cdf_scalar(values),  // 高精度要求時はスカラー実装
            }
        }
    } else {
        norm_cdf_scalar_with_tolerance(values, tolerance)
    }
}
```

### Phase 4: 統合とベンチマーク（2時間）

#### 4.1 Black-Scholesへの適用
- [ ] bs_call_price_batchでSIMD版norm_cdf使用
- [ ] 共通項の事前計算最適化
- [ ] メモリアクセスパターン最適化

#### 4.2 ベンチマーク実施
```bash
# ベースライン記録
cargo bench -- --save-baseline before

# 最適化後
cargo bench -- --baseline before
```

### Phase 5: 品質チェックと調整（1時間）
```bash
# テスト実行（精度確認）
cargo test --all

# パフォーマンステスト
cargo bench

# コード品質
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック
similarity-rs --threshold 0.80 --skip-test src/
```

## 技術要件

### 必須要件
- [x] 階層化された精度要件の遵守
  - PRACTICAL_TOLERANCE (1e-3): 実務計算用
  - THEORETICAL_TOLERANCE (1e-5): 理論検証用
  - NUMERICAL_TOLERANCE (1e-7): 数値検証用
- [x] ZERO HARDCODE POLICY準拠（すべてのマジックナンバーを定数化）
- [x] 後方互換性維持（既存APIを変更しない）
- [x] スレッド安全性（Send + Sync）

### パフォーマンス目標
- [ ] norm_cdf_practical: 30%高速化（3次多項式近似）
- [ ] norm_cdf_theoretical: 現行性能維持（精度優先）
- [ ] バッチ処理（1M要素）: < 5ms（現在: ~20ms）
- [ ] Black-Scholes単一計算: < 8ns（現在: ~10ns）
- [ ] メモリ使用量: 入力データの1.5倍以内

### 実装方針
- 精度レベルに応じた関数バリアント提供
  - `norm_cdf`: 既存実装（約1e-5精度、後方互換）
  - `norm_cdf_practical`: 実務用高速版（1e-3精度）
  - `norm_cdf_theoretical`: 理論用標準版（1e-5精度）
  - `norm_cdf_numerical`: 高精度版（将来実装、1e-7精度）
- feature flagによる選択的有効化
  - `fast-math`: 高速近似有効化
  - `simd`: SIMD最適化有効化
- すべての定数を適切な場所で定義
  - 精度値: src/constants.rs
  - アルゴリズム係数: 使用箇所の近くでconst定義
  - 最適化パラメータ: モジュール内で定義

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| SIMD可搬性 | 中 | 動的ディスパッチとフォールバック実装 |
| 精度劣化による既存テスト失敗 | 高 | 精度レベル別の関数提供、段階的移行 |
| ARM/M1での動作 | 中 | NEON対応または自動ベクトル化依存 |
| 高速近似の精度不足 | 低 | 実測とチューニング、フォールバック |

## チェックリスト

### 実装前
- [x] 現在のベンチマーク基準値記録
- [x] 階層化された精度要件の理解（PRACTICAL/THEORETICAL/NUMERICAL）
- [ ] SIMD命令セットの利用可能性確認
- [ ] 既存定数の確認（`grep -r "const.*=" src/constants.rs`）

### 実装中
- [ ] すべての数値リテラルを定数化（ZERO HARDCODE POLICY）
- [ ] 各最適化後のベンチマーク実行
- [ ] 精度レベル別のテスト実行
- [ ] プロファイリングによるボトルネック確認
- [ ] ハードコード検出スクリプト実行（`./scripts/detect_hardcode.sh`）

### 実装後
- [ ] 全テスト通過（cargo test）
- [ ] ベンチマーク改善確認（目標達成）
- [ ] ドキュメント更新（最適化内容記載）
- [ ] 定数定義のドキュメント化（根拠と参考文献）
- [ ] 計画のarchive移動

## 成果物

- [ ] 最適化されたnorm_cdf実装（src/math/distributions.rs）
- [ ] 高速数学関数モジュール（src/math/fast_math.rs）
- [ ] SIMD実装（src/simd/）
- [ ] ベンチマーク結果レポート（benches/結果）
- [ ] パフォーマンス改善ドキュメント

## 期待される成果

### パフォーマンス改善
- 単一計算: 30-40%高速化
- バッチ処理: 4-8倍高速化（SIMD有効時）
- メモリ効率: 変更なし（ゼロコピー維持）

### 実務への影響
- リアルタイムプライシング対応可能
- 大規模ポートフォリオ計算の高速化
- クラウドコスト削減（計算時間短縮）

## 備考

### 精度管理の原則
- 階層化された精度管理（PRACTICAL/THEORETICAL/NUMERICAL）を厳守
- norm_cdfの実装限界（約1e-5）を考慮した現実的な最適化
- 用途に応じた精度レベルの選択を可能にする

### ZERO HARDCODE POLICY遵守
- すべての数値定数に意味のある名前を付ける
- 定数の根拠と参考文献をコメントで明記
- テストコードでも必ず定数を使用
- ハードコード検出スクリプトで定期的にチェック

### パフォーマンス最適化の方針
- 精度レベル別の最適化実装（トレードオフの明確化）
- SIMD実装は将来のAVX-512対応も視野に入れる
- CPU機能の動的検出によるポータブルな実装
- Criterionベンチマークの結果をGitHubActionsで自動追跡することを検討

### 参考文献
- Hart, J.F. (1968): "Computer Approximations" - 3次多項式近似
- Abramowitz & Stegun (1972): "Handbook of Mathematical Functions" - 現行5次多項式
- Schraudolph, N.N. (1999): "A Fast, Compact Approximation of the Exponential Function" - 高速exp近似
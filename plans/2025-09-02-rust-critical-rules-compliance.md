# [Rust] Critical Rules違反修正と品質向上 実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 中
- **推定コード行数**: 300-400行（主に既存コードの修正）
- **対象モジュール**: core/src/constants.rs, core/src/math/distributions.rs, core/src/compute/, bindings/python/src/models.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 300-400行
- [x] 新規ファイル数: 1個（core/src/compute/formulas.rs）
- [x] 影響範囲: 複数モジュール
- [x] PyO3バインディング: 必要（models.rsの修正）
- [x] SIMD最適化: 不要（アンチパターン）
- [x] 並列化: 不要（既存実装維持）

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | - | ✅ | - | `cargo test --all` |
| cargo clippy | - | ✅ | - | `cargo clippy -- -D warnings` |
| cargo fmt | - | ✅ | - | `cargo fmt --check` |
| similarity-rs | - | ✅ | - | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | - | 条件付き | - | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | - | 推奨 | - | `cargo bench` |

## 🚨 Critical Rules違反の修正内容

### [C011-3] ハードコード違反: 4件

#### 修正対象
1. **core/src/math/distributions.rs**
   - Lines 26, 28: `8.0` → `NORM_CDF_UPPER_BOUND`
   - Lines 66, 68: `-8.0` → `NORM_CDF_LOWER_BOUND`
   - Lines 51, 80: `40.0` → `NORM_PDF_ZERO_BOUND`

### [C012] コード重複: 3箇所

#### 修正対象
1. **Black-Scholesフォーミュラの重複（6箇所）**
   - core/src/compute/black_scholes.rs（並列/逐次）
   - core/src/compute/black76.rs（並列/逐次）
   - bindings/python/src/models.rs（スカラー版）

2. **norm_cdf/norm_pdf実装の重複**
   - 配列版とスカラー版で同じロジック

## フェーズ構成

### Phase 1: 定数定義追加（30分）

#### core/src/constants.rs への追加
```rust
// ============================================================================
// 数学関数用定数
// ============================================================================

/// 正規分布CDF実質的上限
/// 
/// x > 8.0 の場合、Φ(x) ≈ 1.0 として扱う。
/// 浮動小数点精度で区別不可能なレベル。
pub const NORM_CDF_UPPER_BOUND: f64 = 8.0;

/// 正規分布CDF実質的下限
/// 
/// x < -8.0 の場合、Φ(x) ≈ 0.0 として扱う。
/// 浮動小数点精度で区別不可能なレベル。
pub const NORM_CDF_LOWER_BOUND: f64 = -8.0;

/// 正規分布PDF実質的ゼロ境界
/// 
/// |x| > 40.0 の場合、φ(x) ≈ 0.0 として扱う。
/// exp(-800) は実質的にゼロ。
pub const NORM_PDF_ZERO_BOUND: f64 = 40.0;

/// Black-Scholesフォーミュラ内の定数
/// 
/// σ²/2 の係数（頻繁に使用）
pub const HALF: f64 = 0.5;

/// ボラティリティ項の係数
pub const VOL_SQUARED_HALF: f64 = 2.0;
```

### Phase 2: 共通計算ロジックの抽出（1時間）

#### 新規ファイル: core/src/compute/formulas.rs
```rust
//! 共通金融計算フォーミュラ

use crate::math::distributions::norm_cdf;

/// Black-Scholes d1, d2パラメータ計算（スポット価格版）
#[inline(always)]
pub fn black_scholes_d1_d2(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r + sigma * sigma / VOL_SQUARED_HALF) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Black76 d1, d2パラメータ計算（フォワード価格版）
#[inline(always)]
pub fn black76_d1_d2(f: f64, k: f64, t: f64, sigma: f64) -> (f64, f64) {
    let sqrt_t = t.sqrt();
    let d1 = ((f / k).ln() + (sigma * sigma / VOL_SQUARED_HALF) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    (d1, d2)
}

/// Black-Scholesコール価格計算（スカラー版）
#[inline(always)]
pub fn black_scholes_call_scalar(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    let (d1, d2) = black_scholes_d1_d2(s, k, t, r, sigma);
    s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
}

/// Black-Scholesプット価格計算（スカラー版）
#[inline(always)]
pub fn black_scholes_put_scalar(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
    let (d1, d2) = black_scholes_d1_d2(s, k, t, r, sigma);
    k * (-r * t).exp() * norm_cdf(-d2) - s * norm_cdf(-d1)
}
```

### Phase 3: 既存コードの修正（2時間）

#### 1. core/src/math/distributions.rs の修正
- マジックナンバーを定数に置換
- マクロを使用して重複ロジックを統一

#### 2. core/src/compute/black_scholes.rs の修正
- formulas::black_scholes_d1_d2 を使用
- 並列/逐次の重複を削減

#### 3. core/src/compute/black76.rs の修正
- formulas::black76_d1_d2 を使用
- 並列/逐次の重複を削減

#### 4. bindings/python/src/models.rs の修正
- formulas::black_scholes_call_scalar を使用
- to_vec() の削除（メモリコピー最適化）

### Phase 4: 品質チェック（1時間）
```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック
similarity-rs --threshold 0.80 --skip-test src/
# 重複が解消されていることを確認

# ベンチマーク（パフォーマンス劣化がないことを確認）
cargo bench
```

### Phase 5: 検証とドキュメント更新（30分）
- [ ] すべてのテストが通過
- [ ] パフォーマンス劣化なし
- [ ] ドキュメント更新

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#Black-Scholes系"
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
  - name: "f"
    meaning: "フォワード価格"
    source: "naming_conventions.md#Black-Scholes系"
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # 新規命名なし（既存の命名規則に完全準拠）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 技術要件

### 必須要件
- [x] エラー率 < `src/constants.rs::EPSILON`（実務精度）
- [x] メモリ安全性（Rust保証）
- [x] スレッド安全性（Send + Sync）
- [x] Critical Rules C001-C014完全遵守

### パフォーマンス目標
- [x] パフォーマンス劣化なし（ベンチマークで確認）
- [x] メモリ使用量削減（to_vec()削除による）
- [x] コンパイル時間への影響最小限

### PyO3連携
- [x] 既存のゼロコピー実装を維持
- [x] GIL解放での並列処理を維持
- [x] エラー変換の一貫性

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 定数変更による精度変化 | 低 | 定数値は変更せず名前のみ付与 |
| リファクタリングによるパフォーマンス劣化 | 中 | ベンチマークで確認、inline(always)使用 |
| 共通化による可読性低下 | 低 | 適切なモジュール分割とドキュメント |

## チェックリスト

### 実装前
- [x] 既存コードの重複パターン確認完了
- [x] 定数定義の適切な配置場所確認
- [x] 影響範囲の特定完了

### 実装中
- [ ] 各フェーズごとのテスト実行
- [ ] コミット前の`cargo fmt`
- [ ] 段階的な動作確認

### 実装後
- [ ] 全品質ゲート通過
  - [ ] cargo test --all
  - [ ] cargo clippy -- -D warnings
  - [ ] cargo fmt --check
  - [ ] similarity-rs確認（重複解消）
- [ ] ベンチマーク結果記録
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 定数定義追加（core/src/constants.rs）
- [ ] 共通フォーミュラモジュール（core/src/compute/formulas.rs）
- [ ] 修正されたdistributionsモジュール
- [ ] 修正されたBlack-Scholesモジュール
- [ ] 修正されたBlack76モジュール
- [ ] 修正されたPyO3バインディング
- [ ] 全テストの通過確認
- [ ] ベンチマーク結果

## 備考

### Critical Rules遵守の重要性
本実装は以下のCritical Rulesを特に重視：
- **C002**: エラー迂回禁止 - すべてのエラーを即座に修正
- **C004/C014**: 理想実装ファースト - 段階的改善ではなく一度に完全修正
- **C011-3**: ハードコード禁止 - すべてのマジックナンバーを定数化
- **C012**: DRY原則 - コード重複を完全排除
- **C013**: 破壊的リファクタリング推奨 - 既存コードを躊躇なく改善

### アンチパターン回避
- SIMD最適化は提案しない（過去に210行削除済み）
- 「後で改善」という考えを排除
- プロファイリングなしの推測最適化を避ける

### 参考資料
- .claude/critical-rules.xml
- .claude/development-principles.md
- .claude/antipatterns/README.md
- docs/ja/internal/naming_conventions.md
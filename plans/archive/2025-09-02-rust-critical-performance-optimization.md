# [Rust] Critical Rules遵守とパフォーマンス最適化 統合実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Rust
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 600-800行（既存コードの修正が主）
- **対象モジュール**: core/src/constants.rs, core/src/math/distributions.rs, core/src/compute/, bindings/python/src/models.rs

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 600-800行
- [x] 新規ファイル数: 1個（core/src/compute/formulas.rs）
- [x] 影響範囲: 複数モジュール（core全体 + bindings）
- [x] PyO3バインディング: 必要（models.rsの最適化）
- [x] SIMD最適化: 不要（アンチパターン）
- [x] 並列化: 不要（既存実装維持）

### 規模判定結果
**大規模タスク**

## 品質管理ツール（Rust）

### 適用ツール（規模に応じて自動選択）
| ツール | 小規模 | 中規模 | 大規模 | 実行コマンド |
|--------|--------|--------|--------|-------------|
| cargo test | - | - | ✅ | `cargo test --all` |
| cargo clippy | - | - | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | - | - | ✅ | `cargo fmt --check` |
| similarity-rs | - | - | ✅ | `similarity-rs --threshold 0.80 src/` |
| rust-refactor.md | - | - | ✅ | `.claude/commands/rust-refactor.md` 適用 |
| cargo bench | - | - | ✅ | `cargo bench` |

## 🚨 統合実装の理由（Critical Rules遵守）

### C004/C014: 理想実装ファースト原則
- **段階的実装禁止**: 「Critical Rules修正してから最適化」は違反
- **妥協実装禁止**: 「とりあえず動く状態にして後で改善」は違反
- **理想形で一括実装**: すべての改善を同時に適用

### C012: DRY原則
- 同じファイルを複数回修正することは重複作業
- 一度の修正で完全な形にする

### C013: 破壊的リファクタリング推奨
- 既存実装を躊躇なく改善
- 後方互換性の考慮不要（ユーザーゼロ）

## フェーズ構成

### Phase 1: 設計フェーズ（1時間）

#### 1.1 定数定義設計
```rust
// core/src/constants.rs に追加
pub const NORM_CDF_UPPER_BOUND: f64 = 8.0;
pub const NORM_CDF_LOWER_BOUND: f64 = -8.0;
pub const NORM_PDF_ZERO_BOUND: f64 = 40.0;
pub const HALF: f64 = 0.5;
pub const VOL_SQUARED_HALF: f64 = 2.0;
```

#### 1.2 共通フォーミュラモジュール設計
```rust
// core/src/compute/formulas.rs（新規）
pub fn black_scholes_d1_d2(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> (f64, f64)
pub fn black76_d1_d2(f: f64, k: f64, t: f64, sigma: f64) -> (f64, f64)
pub fn black_scholes_call_scalar(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64
pub fn black_scholes_put_scalar(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64
```

### Phase 2: 統合実装フェーズ（3時間）

#### マイルストーン1: Float64Builder最適化とコード統合（2時間）

##### core/src/compute/black_scholes.rs
```rust
// Before（メモリコピー + 重複）
let mut result = Vec::with_capacity(len);
for i in 0..len {
    // Black-Scholesフォーミュラ（重複コード）
    let sqrt_t = t.sqrt();
    let d1 = ((s / k).ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
    let d2 = d1 - sigma * sqrt_t;
    let call_price = s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2);
    result.push(call_price);
}
Ok(Arc::new(Float64Array::from(result)))

// After（Float64Builder + 共通化）
let mut builder = Float64Builder::with_capacity(len);
for i in 0..len {
    let s = get_scalar_or_array_value(spots, i);
    let k = get_scalar_or_array_value(strikes, i);
    let t = get_scalar_or_array_value(times, i);
    let r = get_scalar_or_array_value(rates, i);
    let sigma = get_scalar_or_array_value(sigmas, i);
    
    let call_price = formulas::black_scholes_call_scalar(s, k, t, r, sigma);
    builder.append_value(call_price);
}
Ok(Arc::new(builder.finish()))
```

並列処理版も同様に修正：
- `Vec<f64>` → `builder.append_slice(&results)`
- 共通フォーミュラ使用

##### core/src/compute/black76.rs
- 同様にFloat64Builder化
- `formulas::black76_d1_d2()` 使用

##### core/src/compute/merton.rs
- Float64Builder化のみ（配当付きBlack-Scholes）

#### マイルストーン2: ハードコード修正（30分）

##### core/src/math/distributions.rs
```rust
// Before（ハードコード）
if x > 8.0 { return 1.0; }
if x < -8.0 { return 0.0; }
if x.abs() > 40.0 { return 0.0; }

// After（定数使用）
use crate::constants::{NORM_CDF_UPPER_BOUND, NORM_CDF_LOWER_BOUND, NORM_PDF_ZERO_BOUND};

if x > NORM_CDF_UPPER_BOUND { return 1.0; }
if x < NORM_CDF_LOWER_BOUND { return 0.0; }
if x.abs() > NORM_PDF_ZERO_BOUND { return 0.0; }
```

#### マイルストーン3: models.rs最適化（30分）

##### bindings/python/src/models.rs
- **numpy_to_arrow_direct**: 保持（30箇所で使用中）
- **arrayref_to_numpy**: 保持（バッチAPIで使用中）
- **Black-Scholesフォーミュラ**: `formulas::black_scholes_call_scalar` 使用
- **メモリコピー削減**: 該当箇所があれば最適化

### Phase 3: 品質チェックフェーズ（1時間）

```bash
# 基本チェック
cargo test --all
cargo clippy -- -D warnings
cargo fmt --check

# 重複チェック（改善確認）
similarity-rs --threshold 0.80 --skip-test src/
# Before: 6箇所のBlack-Scholesフォーミュラ重複
# After: 重複解消を確認

# パフォーマンス確認
cargo bench
# 10-20%高速化を確認

# Python側のベンチマーク
pytest tests/performance/ -m benchmark
# v0.0.7との比較
```

### Phase 4: リファクタリングフェーズ（30分）

- [ ] rust-refactor.md 適用（必要な場合）
- [ ] 最終的なコード整理
- [ ] ドキュメント更新
- [ ] CHANGELOG.md更新

## 4. 命名定義セクション

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
- [x] パフォーマンス改善: 10-20%高速化
- [x] メモリ使用量: 30-50%削減
- [x] arro3-coreとの性能差: 5%以内
- [x] コンパイル時間への影響: 最小限

### PyO3連携
- [x] 既存のゼロコピー実装を維持（arrow_native.rs）
- [x] GIL解放での並列処理を維持
- [x] エラー変換の一貫性

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Float64Builder API変更 | 低 | Arrow v56.0で安定、ドキュメント確認済み |
| パフォーマンス劣化 | 中 | ベンチマークで確認、inline(always)使用 |
| 既存テスト失敗 | 低 | 段階的なテスト実行で早期発見 |
| 重複削減による可読性低下 | 低 | 適切なモジュール分割、明確な関数名 |

## チェックリスト

### 実装前
- [x] 既存コードの重複パターン確認完了（6箇所）
- [x] Float64Builder APIドキュメント確認
- [x] 影響範囲の特定完了
- [x] arro3-coreの実装分析完了

### 実装中
- [ ] 各マイルストーンごとのテスト実行
- [ ] コミット前の`cargo fmt`
- [ ] 段階的な動作確認
- [ ] パフォーマンス測定

### 実装後
- [ ] 全品質ゲート通過
  - [ ] cargo test --all
  - [ ] cargo clippy -- -D warnings
  - [ ] cargo fmt --check
  - [ ] similarity-rs確認（重複解消）
- [ ] ベンチマーク結果記録
  - [ ] 10-20%高速化達成
  - [ ] メモリ使用量30%以上削減
- [ ] ドキュメント更新
- [ ] バージョン更新（v0.0.8）
- [ ] 計画のarchive移動

## 成果物

- [ ] 定数定義追加（core/src/constants.rs）
- [ ] 共通フォーミュラモジュール（core/src/compute/formulas.rs）
- [ ] Float64Builder化されたBlack-Scholesモジュール
- [ ] Float64Builder化されたBlack76モジュール
- [ ] Float64Builder化されたMertonモジュール
- [ ] ハードコード修正されたdistributionsモジュール
- [ ] 最適化されたPyO3バインディング（models.rs）
- [ ] 全テストの通過確認
- [ ] ベンチマーク結果（10-20%改善）

## 期待される成果

### 即座の効果
- **パフォーマンス**: 10-20%高速化（Float64Builder使用）
- **メモリ効率**: 30-50%削減（メモリコピー削減）
- **コード品質**: Critical Rules完全遵守

### 長期的効果
- **保守性向上**: コード重複解消により変更箇所削減
- **拡張性向上**: 共通フォーミュラで新モデル追加容易
- **信頼性向上**: ハードコード排除で定数管理一元化

## 備考

### Critical Rules遵守の重要性
本実装は以下のCritical Rulesを特に重視：
- **C002**: エラー迂回禁止 - すべてのエラーを即座に修正
- **C004/C014**: 理想実装ファースト - 統合実装で完全修正
- **C011-3**: ハードコード禁止 - すべてのマジックナンバーを定数化
- **C012**: DRY原則 - コード重複を完全排除
- **C013**: 破壊的リファクタリング推奨 - 既存コードを躊躇なく改善

### アンチパターン回避
- SIMD最適化は提案しない（過去に210行削除済み）
- 「後で改善」という考えを排除（段階的実装禁止）
- プロファイリングなしの推測最適化を避ける
- Arrow型変換（to_numpy/to_pylist）を使用しない

### 参考資料
- .claude/critical-rules.xml
- .claude/development-principles.md
- .claude/antipatterns/README.md
- docs/ja/internal/naming_conventions.md
- plans/2025-09-02-rust-critical-rules-compliance.md（参考）
- plans/2025-09-02-rust-performance-optimization-builder.md（参考）
# American Option Pricing Accuracy Fix

## ステータス: COMPLETED
## 開始日: 2025-01-26
## 完了日: 2025-01-26
## 言語: Rust（コア実装）

## 1. 背景と問題

### 現在の状況
- American putオプションでBENCHOPと5.7%の誤差（6.604 vs 6.248）
- American callは正確（誤差 < 0.01%）
- 原因：BAW（1987）近似が早期行使プレミアムを過大評価

### 根本原因
1. **BS2002実装が無効化**
   - "numerical issues that need debugging"のコメント
   - より高精度な手法が利用できない
2. **BAW近似の限界**
   - 1987年の古い手法
   - 早期行使プレミアムを約50%過大評価
3. **二項木も不完全**
   - 10,000ステップで6.090（BENCHOP: 6.248）
   - 早期行使プレミアムを約25%過小評価

## 2. 目標

### 必達目標
- [ ] American put価格の誤差を1%以内に改善
- [ ] 既存テストの全パス維持
- [ ] パフォーマンス劣化なし（< 1μs/計算）

### 努力目標
- [ ] BENCHOP参照値との完全一致（誤差 < 0.1%）
- [ ] BS2002の完全復活

## 3. 実装方針

### Phase 1: BS2002のデバッグ（優先度：高）
**期間**: 1日
**ファイル**: `core/src/compute/american.rs`

1. 数値オーバーフロー箇所の特定
2. 数値安定性の改善
   - exp()計算の工夫
   - 対数スケールでの計算
3. 単体テストによる検証

### Phase 2: 二項木の改善（優先度：中）
**期間**: 2日
**ファイル**: `core/src/compute/american.rs::american_binomial`

1. パラメータの見直し
   - 確率測度の計算方法
   - 配当利回りの扱い
2. QuantLib実装との比較
3. 収束性の改善

### Phase 3: 代替手法の検討（優先度：低）
**期間**: 3日
**新規ファイル**: `core/src/compute/american_fd.rs`

有限差分法（Crank-Nicolson）の実装：
```rust
pub fn american_fd_put(
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64,
    n_space: usize, n_time: usize
) -> f64
```

## 4. 命名定義

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
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#Black-Scholes系"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "n_steps"
    meaning: "ステップ数"
    source: "naming_conventions.md#将来追加予定"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "n_space"
    meaning: "空間方向の分割数（有限差分法）"
    justification: "有限差分法で標準的な命名"
    references: "Wilmott (2006) Paul Wilmott on Quantitative Finance"
    status: "pending_approval"
  - name: "n_time"
    meaning: "時間方向の分割数（有限差分法）"
    justification: "有限差分法で標準的な命名"
    references: "Wilmott (2006) Paul Wilmott on Quantitative Finance"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 5. 実装詳細

### BS2002の修正箇所（推定）
```rust
// 問題のある箇所（予想）
fn calculate_phi(/*...*/) -> f64 {
    // exp()のオーバーフロー対策
    let exponent = /*...*/;
    if exponent > 700.0 { // exp(700)が限界
        return /* 適切な近似値 */;
    }
    exponent.exp()
}

// 改善案：対数スケールでの計算
fn calculate_phi_log_scale(/*...*/) -> f64 {
    // log-sum-exp技法を使用
    let log_phi = /*...*/;
    log_phi.exp()
}
```

### 二項木の改善
```rust
// 現在の問題：リスク中立確率の計算
let p = (((r - q) * dt).exp() - d) / (u - d);

// 改善案：Jarrow-Rudd法の検討
let drift = (r - q - 0.5 * sigma * sigma) * dt;
let u = (drift + sigma * dt.sqrt()).exp();
let d = (drift - sigma * dt.sqrt()).exp();
let p = 0.5; // 対称確率
```

## 6. テスト計画

### 単体テスト
1. BS2002の各補助関数のテスト
2. 境界条件のテスト（t→0、σ→0）
3. Put-Call関係のテスト

### 統合テスト
1. BENCHOP参照値との比較
2. 他の実装（QuantLib等）との比較
3. 早期行使境界の妥当性検証

### パフォーマンステスト
```rust
#[bench]
fn bench_american_put(b: &mut Bencher) {
    b.iter(|| american_put_scalar(100.0, 100.0, 1.0, 0.05, 0.0, 0.2));
}
```

## 7. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| BS2002が修正不可能 | 高 | 有限差分法に切り替え |
| パフォーマンス劣化 | 中 | キャッシュ最適化、並列化 |
| 後方互換性の破壊 | 低 | 既存APIは維持、内部実装のみ変更 |

## 8. 成功基準

### 必須
- [ ] American put誤差 < 1%
- [ ] 全テストパス
- [ ] 計算時間 < 1μs

### 推奨
- [ ] BENCHOP完全一致（誤差 < 0.1%）
- [ ] コード品質スコア維持
- [ ] ドキュメント更新完了

## 9. スケジュール

| フェーズ | 期間 | 開始日 | 完了予定 |
|----------|------|--------|----------|
| Phase 1: BS2002デバッグ | 1日 | 2025-01-26 | 2025-01-27 |
| Phase 2: 二項木改善 | 2日 | 2025-01-27 | 2025-01-29 |
| Phase 3: 有限差分（オプション） | 3日 | 2025-01-29 | 2025-02-01 |

## 10. 参考資料

### 論文
- Bjerksund & Stensland (2002) "Closed Form Valuation of American Options"
- Barone-Adesi & Whaley (1987) "Efficient Analytic Approximation"
- Cox, Ross & Rubinstein (1979) "Option Pricing: A Simplified Approach"

### 実装参考
- QuantLib: americanoption.cpp
- 過去の記録: plans/archive/2025-09-03-american-implementation-summary.md（参照注意）

## 11. 注意事項

**Critical Rules遵守**:
- C002: エラー迂回禁止 - 数値問題は根本から修正
- C004: 理想実装ファースト - BAW近似は一時的、BS2002復活が理想
- C011: ハードコード禁止 - 全ての閾値は定数定義
- C012: DRY原則 - 既存の数学関数を再利用

**アンチパターン回避**:
- ❌ SIMD最適化は提案しない
- ❌ 段階的実装は行わない（一度で完成させる）
- ❌ 推測での最適化は行わない（プロファイリング必須）

---
計画作成日: 2025-01-26
作成者: Claude
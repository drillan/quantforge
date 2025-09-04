# American Adaptive実装の統合計画

## ステータス: COMPLETED
## 開始日: 2025-01-26
## 完了日: 2025-01-26
## 言語: Rust + Python（統合実装）

## 1. 背景と問題

### 現在の状況
- american_adaptive.rs: 実装完了、テストPASS
- 統合状態: 未統合（メインから参照なし）
- Python binding: 未実装
- ユーザーアクセス: 不可

### 技術的評価
1. **実装品質**: 動的dampening factorによる適応的調整
2. **カバレッジ**: Moneyness 0.5-1.5、満期 0.01-5年、σ 0.05-0.7
3. **精度**: パラメータ領域に応じた改善の可能性

### 問題点
- 宙に浮いた実装（ユーザー価値ゼロ）
- 技術的負債化のリスク
- 実環境での検証不足

## 2. 目標

### 必達目標
- [ ] american.rsへの統合（オプション機能として）
- [ ] Python APIの追加（_adaptiveサフィックス）
- [ ] 既存APIの後方互換性維持
- [ ] パフォーマンスベンチマーク実装

### 努力目標
- [ ] 包括的なパラメータ検証
- [ ] ドキュメント整備
- [ ] 将来のデフォルト切り替えパス明確化

## 3. 実装方針

### Phase 1: Rust統合（1時間）
**ファイル**: `core/src/compute/american.rs`

1. adaptive実装のインポート追加
2. 内部切り替えロジック実装
3. 単体テストの拡充

```rust
// 新規追加関数（内部用）
pub fn american_put_scalar_with_method(
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64,
    method: PricingMethod
) -> f64 {
    match method {
        PricingMethod::BAW => american_put_simple(s, k, t, r, q, sigma),
        PricingMethod::Adaptive => american_put_adaptive(s, k, t, r, q, sigma),
    }
}
```

### Phase 2: Python Binding（1時間）
**ファイル**: `src/python_modules/american_option.rs`

1. adaptive版の関数追加
2. method引数を受け取るオプション版

```python
# Python API
american.call_price_adaptive(s, k, t, r, q, sigma)  # 明示的にadaptive
american.put_price_adaptive(s, k, t, r, q, sigma)   # 明示的にadaptive

# 将来的なAPI（method引数）
american.call_price(s, k, t, r, q, sigma, method='baw')  # デフォルト
american.call_price(s, k, t, r, q, sigma, method='adaptive')  # オプション
```

### Phase 3: ベンチマーク実装（30分）
**ファイル**: `benchmarks/american_methods_comparison.py`

1. BAW vs Adaptive精度比較
2. パフォーマンス測定
3. パラメータ領域別の評価

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
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "method"
    meaning: "価格計算手法"
    justification: "複数の実装を切り替えるための標準的な名称"
    references: "QuantLib等でも同様の命名"
    status: "pending_approval"
    values:
      - "baw": "Barone-Adesi-Whaley (1987)"
      - "adaptive": "Adaptive BAW with dynamic dampening"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 5. 実装詳細

### Rust側の変更

#### american.rs
```rust
use super::american_adaptive::{
    american_call_adaptive, american_put_adaptive
};

// 列挙型定義
pub enum PricingMethod {
    BAW,
    Adaptive,
}

// スカラー版（内部用）
pub(crate) fn american_call_scalar_internal(
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64,
    method: PricingMethod
) -> f64 {
    match method {
        PricingMethod::BAW => american_call_simple(s, k, t, r, q, sigma),
        PricingMethod::Adaptive => american_call_adaptive(s, k, t, r, q, sigma),
    }
}

// 既存のpublic APIは変更しない（BAWのまま）
pub fn american_call_scalar(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    american_call_simple(s, k, t, r, q, sigma)  // 後方互換性維持
}
```

### Python Binding
```rust
#[pyfunction]
#[pyo3(name = "call_price_adaptive")]
fn py_american_call_adaptive(
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64
) -> PyResult<f64> {
    validate_positive_parameters!(s, k, t, sigma);
    validate_non_negative_parameters!(r);
    Ok(american_call_adaptive(s, k, t, r, q, sigma))
}

#[pyfunction]
#[pyo3(name = "put_price_adaptive")]  
fn py_american_put_adaptive(
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64
) -> PyResult<f64> {
    validate_positive_parameters!(s, k, t, sigma);
    validate_non_negative_parameters!(r);
    Ok(american_put_adaptive(s, k, t, r, q, sigma))
}
```

## 6. テスト計画

### 単体テスト
1. Adaptive実装の基本動作
2. BAWとの比較（同一パラメータ）
3. 境界条件でのロバスト性

### 統合テスト
1. Python APIの動作確認
2. BENCHOP値との比較
3. パラメータスイープ結果の妥当性

### ベンチマークテスト
```python
# benchmarks/american_methods_comparison.py
def test_accuracy_by_moneyness():
    """モネーネス別の精度比較"""
    for moneyness in [0.5, 0.8, 1.0, 1.2, 1.5]:
        s = 100.0 * moneyness
        k = 100.0
        baw_price = american.put_price(s, k, 1.0, 0.05, 0.0, 0.2)
        adaptive_price = american.put_price_adaptive(s, k, 1.0, 0.05, 0.0, 0.2)
        # BENCHOPとの比較...

def test_performance():
    """計算速度の比較"""
    # 10,000回の計算時間を測定
```

## 7. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Adaptive精度が劣る領域 | 中 | デフォルトはBAW維持、警告文書 |
| パフォーマンス劣化 | 低 | ベンチマークで監視 |
| ユーザー混乱 | 低 | 明確なドキュメント、デフォルト不変 |
| 技術的複雑性増加 | 低 | テスト充実、切り替えロジック単純化 |

## 8. 成功基準

### 必須
- [ ] Python APIでadaptive版が呼び出し可能
- [ ] 既存APIの動作変更なし
- [ ] 全テストパス
- [ ] ドキュメント更新

### 推奨
- [ ] BENCHOP誤差改善（特定領域で）
- [ ] パフォーマンス劣化 < 10%
- [ ] ユーザーガイド作成

## 9. スケジュール

| フェーズ | 期間 | 開始 | 完了予定 |
|----------|------|------|----------|
| Phase 1: Rust統合 | 1時間 | 即時 | 同日 |
| Phase 2: Python Binding | 1時間 | Phase 1後 | 同日 |
| Phase 3: ベンチマーク | 30分 | Phase 2後 | 同日 |

## 10. ドキュメント更新

### README.md
```markdown
### American Options - Experimental Features

We offer an experimental adaptive pricing method:

```python
# Standard BAW (default)
price = american.put_price(s, k, t, r, q, sigma)

# Adaptive BAW (experimental)
price_adaptive = american.put_price_adaptive(s, k, t, r, q, sigma)
```

The adaptive method adjusts dampening factors based on:
- Moneyness (S/K ratio)
- Time to maturity
- Volatility level

**Note**: Adaptive method is experimental. Use standard method for production.
```

### API Documentation
- american.call_price_adaptive: 新規追加
- american.put_price_adaptive: 新規追加
- 「Experimental」タグを明示

## 11. 将来の拡張

### 短期（1-2週間）
- ユーザーフィードバック収集
- 実環境データでの検証

### 中期（1-3ヶ月）
- ML最適化の検討
- デフォルト切り替えの判断基準策定

### 長期（3-6ヶ月）
- 十分な検証後、デフォルトをadaptiveに切り替え
- method引数による統一API提供

## 12. 注意事項

**Critical Rules遵守**:
- C004: 理想実装を追求（adaptiveは改善の試み）
- C010: TDD - テスト先行で実装
- C012: DRY原則 - 共通ロジックは再利用

**アンチパターン回避**:
- ❌ いきなりデフォルト変更しない
- ❌ 既存APIを破壊しない
- ✅ オプション機能として追加
- ✅ 十分な検証後に昇格

## 13. コミットメッセージ

```
feat(american): Adaptive pricing methodの統合

- american_adaptiveをオプション機能として統合
- Python APIに_adaptive版を追加
- 既存APIは変更なし（後方互換性維持）
- ベンチマークテスト追加

統合内容：
- Rust: 切り替えロジック実装
- Python: call_price_adaptive, put_price_adaptive追加
- Test: 精度・パフォーマンス比較

Experimental機能として提供、将来のデフォルト化検討
```

---
計画作成日: 2025-01-26
作成者: Claude
# Mertonモデル（配当付き資産）実装計画

**ステータス**: ACTIVE  
**作成日**: 2025-08-26  
**最終更新**: 2025-08-26  
**優先度**: HIGH  
**依存関係**: 2025-08-26-multi-model-architecture.md（フェーズ1完了）

## 概要

Mertonモデルは、配当利回りを考慮したオプション価格モデルです。Black-Scholesモデルを拡張し、連続的な配当支払いがある資産のオプション価格を計算します。

## 背景

### モデルの特徴
- **用途**: 配当を支払う株式、株価指数、為替レートのオプション
- **拡張点**: Black-Scholesに配当利回り（q）パラメータを追加
- **数式**: スポット価格を`S*exp(-q*T)`に調整

### 数学的基礎

```
d1 = (ln(S/K) + (r - q + σ²/2) * T) / (σ * √T)
d2 = d1 - σ * √T

Call = S * exp(-q*T) * N(d1) - K * exp(-r*T) * N(d2)
Put = K * exp(-r*T) * N(-d2) - S * exp(-q*T) * N(-d1)
```

## 実装計画

### タスク1: モジュール構造の作成
- [ ] `src/models/merton/mod.rs` - モジュール定義
- [ ] `src/models/merton/pricing.rs` - 価格計算ロジック
- [ ] `src/models/merton/greeks.rs` - グリークス計算
- [ ] `src/models/merton/implied_volatility.rs` - IV計算

### タスク2: パラメータ構造体の定義
```rust
pub struct MertonParams {
    pub s: f64,      // スポット価格
    pub k: f64,      // 権利行使価格
    pub t: f64,      // 満期までの時間
    pub r: f64,      // リスクフリーレート
    pub q: f64,      // 配当利回り（新規パラメータ）
    pub sigma: f64,  // ボラティリティ
}
```

### タスク3: 価格計算の実装
- [ ] コール価格計算（配当調整済み）
- [ ] プット価格計算（配当調整済み）
- [ ] バッチ処理対応（SIMD最適化）
- [ ] 入力検証（qの範囲チェック追加）

### タスク4: グリークス計算の実装
配当利回りを考慮した調整が必要：
- [ ] Delta: 配当調整済み
- [ ] Gamma: 標準的な計算
- [ ] Theta: 配当による調整
- [ ] Vega: 標準的な計算
- [ ] Rho: 配当による調整
- [ ] Dividend Rho（新規）: 配当感応度

### タスク5: Python APIの実装
```python
# python/quantforge/models/merton.py
def call_price(s, k, t, r, q, sigma):
    """配当付き資産のコールオプション価格"""
    
def put_price(s, k, t, r, q, sigma):
    """配当付き資産のプットオプション価格"""
    
def greeks(s, k, t, r, q, sigma, is_call=True):
    """配当付き資産のグリークス"""
```

### タスク6: テストの実装
- [ ] 単体テスト（価格計算の精度検証）
- [ ] プロパティテスト（Put-Callパリティ）
- [ ] 境界値テスト（q=0でBlack-Scholesと一致）
- [ ] パフォーマンステスト
- [ ] ゴールデンマスターテスト（参考値との比較）

### タスク7: ドキュメント作成
- [ ] `docs/models/merton.md` - モデル説明
- [ ] `docs/api/python/merton.md` - API文書
- [ ] 使用例とチュートリアル
- [ ] 配当利回りの扱い方の説明

## 技術的詳細

### Black-Scholesとの共通コード
```rust
// 共通の計算ロジックを活用
use crate::models::common::{norm_cdf, norm_pdf};
use crate::models::black_scholes::core;

// 調整済みスポット価格
let adjusted_spot = s * (-q * t).exp();
```

### 配当利回りの影響
1. **Forward価格**: `F = S * exp((r-q)*T)`
2. **ドリフト項**: `μ = r - q`
3. **境界条件**: q=0でBlack-Scholesに収束

### 最適化の考慮点
- 配当調整の事前計算
- exp関数の呼び出し削減
- SIMD対応（配当項も含めて）

## 検証基準

### 精度要件
- 価格精度: 相対誤差 < 1e-6
- グリークス精度: 相対誤差 < 1e-5
- Put-Callパリティ: 誤差 < 1e-10

### パフォーマンス要件
- 単一計算: < 15ns（Black-Scholesの1.5倍以内）
- バッチ処理（100万件）: < 30ms

### 互換性検証
- q=0でBlack-Scholesと完全一致
- 既存のAPIと同様のインターフェース

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| 配当利回りの符号誤り | HIGH | 徹底的なテスト、参照実装との比較 |
| パフォーマンス劣化 | MEDIUM | 事前計算の活用、SIMD最適化 |
| 数値安定性（大きなq） | LOW | 入力範囲の制限、警告出力 |

## 参考資料

- Merton, R.C. (1973). "Theory of Rational Option Pricing"
- Hull, J.C. "Options, Futures, and Other Derivatives"
- draft/GBS_2025.py - Mertonモデルの参照実装

## 成功基準

1. **正確性**: 参照実装との誤差 < 1e-6
2. **性能**: Black-Scholesの1.5倍以内の実行時間
3. **テスト**: カバレッジ90%以上
4. **ドキュメント**: 全公開APIの文書化
5. **互換性**: q=0でBlack-Scholesと一致

## 次のステップ

1. モジュール構造の作成から開始
2. Black-Scholesの実装をベースに拡張
3. 配当調整ロジックの追加
4. 徹底的なテストによる検証

## 更新履歴

- 2025-08-26: 初版作成（2025-08-26-multi-model-architecture.mdから分離）
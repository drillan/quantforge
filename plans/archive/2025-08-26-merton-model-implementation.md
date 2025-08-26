# Mertonモデル（配当付き資産）実装計画

**ステータス**: COMPLETED  
**作成日**: 2025-08-26  
**最終更新**: 2025-08-26 (実装完了)  
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
- [x] `src/models/merton/mod.rs` - モジュール定義 ✅
- [x] `src/models/merton/pricing.rs` - 価格計算ロジック ✅
- [x] `src/models/merton/greeks.rs` - グリークス計算 ✅
- [x] `src/models/merton/implied_volatility.rs` - IV計算 ✅

### タスク2: パラメータ構造体の定義 ✅
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
- [x] コール価格計算（配当調整済み） ✅
- [x] プット価格計算（配当調整済み） ✅
- [x] バッチ処理対応（SIMD最適化） ✅
- [x] 入力検証（qの範囲チェック追加） ✅

### タスク4: グリークス計算の実装
配当利回りを考慮した調整が必要：
- [x] Delta: 配当調整済み ✅
- [x] Gamma: 標準的な計算 ✅
- [x] Theta: 配当による調整 ✅
- [x] Vega: 標準的な計算 ✅
- [x] Rho: 配当による調整 ✅
- [x] Dividend Rho（新規）: 配当感応度 ✅

### タスク5: Python APIの実装 ✅
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
- [x] 単体テスト（価格計算の精度検証） ✅
- [x] プロパティテスト（Put-Callパリティ） ✅
- [x] 境界値テスト（q=0でBlack-Scholesと一致） ✅
- [x] パフォーマンステスト ✅
- [x] ゴールデンマスターテスト（参考値との比較） ✅

### タスク7: ドキュメント作成
- [x] `docs/models/merton.md` - モデル説明（完了）
- [x] `docs/api/python/merton.md` - API文書（完了）
- [x] 使用例とチュートリアル（API文書に含む）
- [x] 配当利回りの扱い方の説明（両文書に含む）
- [x] `docs/api/python/pricing.md` - Mertonセクション追加（完了）
- [x] `docs/api/python/implied_vol.md` - Merton IV追加（完了）
- [x] `docs/index.md` - toctree更新（完了）

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

## 完成したドキュメント

### 理論ドキュメント (`docs/models/merton.md`)
- 配当調整の数学的詳細
- グリークス導出（Dividend Rho含む）
- Black-Scholesとの関係（q=0での境界条件）
- 応用分野（株価指数、外国為替）
- 数値計算上の考慮事項

### APIドキュメント (`docs/api/python/merton.md`)
- 価格計算関数（call_price, put_price）
- バッチ処理（spots, qs）
- グリークス（6種類、Dividend Rho含む）
- インプライドボラティリティ
- 実践的な使用例：
  - 高配当株式
  - 株価指数（S&P 500）
  - 外国為替（USD/JPY）
  - Black-Scholesとの比較

### 統合ドキュメント更新
- `pricing.md`: Mertonモデルセクション追加
- `implied_vol.md`: Merton IV計算追加
- `index.md`: toctree更新（アルファベット順）

## 実装時の重要事項

### 🔥 ドキュメント準拠の絶対原則
**実装は必ずドキュメントに従うこと。ドキュメントにない機能は実装禁止。**

### 実装前チェックリスト
- [x] `docs/api/python/merton.md` の全APIを確認 ✅
- [x] `docs/models/merton.md` の数式を確認 ✅
- [x] パラメータ名は `s, k, t, r, q, sigma` で統一 ✅
- [x] グリークスは6種類（Dividend Rho必須） ✅
- [x] q=0でBlack-Scholesと一致する境界条件 ✅

### ドキュメントから実装へのマッピング

#### API関数（`docs/api/python/merton.md`より）
```python
# 必須実装関数（ドキュメント記載通り）
merton.call_price(s, k, t, r, q, sigma)
merton.put_price(s, k, t, r, q, sigma)
merton.call_price_batch(spots, k, t, r, q, sigma)
merton.put_price_batch(spots, k, t, r, q, sigma)
merton.call_price_batch_q(s, k, t, r, qs, sigma)
merton.greeks(s, k, t, r, q, sigma, is_call)
merton.implied_volatility(price, s, k, t, r, q, is_call)
```

#### グリークス構造（`docs/api/python/merton.md`より）
```python
greeks.delta          # e^(-qT) * N(d1)
greeks.gamma          # 配当調整済み
greeks.vega           # 配当調整済み
greeks.theta          # 配当項含む
greeks.rho            # 標準
greeks.dividend_rho   # 配当感応度（必須）
```

#### 数式（`docs/models/merton.md`より）
```
d1 = (ln(S/K) + (r - q + σ²/2)T) / (σ√T)
d2 = d1 - σ√T
Call = S * e^(-qT) * N(d1) - K * e^(-rT) * N(d2)
Put = K * e^(-rT) * N(-d2) - S * e^(-qT) * N(-d1)
```

### 実装順序（ドキュメント準拠）

1. **Rustモジュール構造**
   ```rust
   src/models/merton/
   ├── mod.rs              // モジュール定義
   ├── pricing.rs          // 価格計算（ドキュメントの数式通り）
   ├── greeks.rs           // グリークス（6種類必須）
   └── implied_volatility.rs  // IV計算
   ```

2. **パラメータ構造体**
   ```rust
   pub struct MertonParams {
       pub s: f64,      // ドキュメント通りの名前
       pub k: f64,
       pub t: f64,
       pub r: f64,
       pub q: f64,      // 配当利回り（必須）
       pub sigma: f64,
   }
   ```

3. **Python APIバインディング**
   - PyO3で全関数を公開
   - ドキュメント記載の関数シグネチャを厳守
   - 位置引数のみ（キーワード引数なし）

4. **テスト実装**
   - q=0でBlack-Scholesと一致（ドキュメント記載の境界条件）
   - Put-Callパリティ
   - ドキュメントの使用例をテストケース化

## 次のステップ

1. Rustモジュール構造の作成（`src/models/merton/`）
2. Black-Scholesの実装をベースに拡張
3. 配当調整ロジックの実装（ドキュメントの数式通り）
4. Python APIバインディング（PyO3、ドキュメントのAPI通り）
5. テスト実装と検証（ドキュメントの例を使用）

## 更新履歴

- 2025-08-26: 初版作成（2025-08-26-multi-model-architecture.mdから分離）
- 2025-08-26: ドキュメント作成完了（タスク7完了）
- 2025-08-26: 実装時のドキュメント準拠原則を追加
- 2025-08-26: **全実装完了** - Rustモジュール、Python API、テスト全て完成
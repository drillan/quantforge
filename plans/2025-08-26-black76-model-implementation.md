# Black76モデル（商品オプション）実装計画

**ステータス**: ACTIVE  
**作成日**: 2025-08-26  
**最終更新**: 2025-08-26  
**優先度**: HIGH  
**依存関係**: docs/api/python/black76.md（作成必須）

## ⚠️ D-SSoTプロトコル適用

**重要**: この計画文書は設計検討用の一時的なメモです。  
実装開始前に以下を必須実施：
1. `docs/api/python/black76.md`を作成して仕様確定
2. ドキュメントから実装へコピペ（手打ち禁止）
3. 実装完了後、この文書を`archive/`へ移動（以降参照禁止）

## 概要

Black76モデルは、先物やフォワード契約のオプション価格を計算するためのモデルです。主に商品（コモディティ）、金利、エネルギー市場で使用されます。

## 背景

### モデルの特徴
- **用途**: 商品先物、金利先物、エネルギーデリバティブ
- **特徴**: スポット価格の代わりにフォワード価格を使用
- **利点**: 保管コストや便益利回りを暗黙的に含む

### 数学的基礎

```
d1 = (ln(F/K) + σ²/2 * T) / (σ * √T)
d2 = d1 - σ * √T

Call = exp(-r*T) * (F * N(d1) - K * N(d2))
Put = exp(-r*T) * (K * N(-d2) - F * N(-d1))
```

ここで、F = フォワード価格

## 実装計画

### タスク1: モジュール構造の作成
- [ ] `src/models/black76/mod.rs` - モジュール定義
- [ ] `src/models/black76/pricing.rs` - 価格計算ロジック
- [ ] `src/models/black76/greeks.rs` - グリークス計算
- [ ] `src/models/black76/implied_volatility.rs` - IV計算

### タスク2: パラメータ構造体の定義
```rust
pub struct Black76Params {
    pub forward: f64,  // フォワード価格（スポット価格の代わり）
    pub strike: f64,   // 権利行使価格
    pub time: f64,     // 満期までの時間
    pub rate: f64,     // リスクフリーレート（割引用）
    pub sigma: f64,    // ボラティリティ
}
```
**注意**: パラメータ名はBlack-Scholesとの一貫性を保つため完全名を使用

### タスク3: 価格計算の実装
- [ ] フォワード価格ベースのコール計算
- [ ] フォワード価格ベースのプット計算
- [ ] 割引係数の事前計算最適化
- [ ] バッチ処理対応（SIMD最適化）

### タスク4: グリークス計算の実装
Black76固有のグリークス：
- [ ] Delta: フォワード価格に対する感応度
- [ ] Gamma: フォワード価格ベース
- [ ] Theta: 時間価値減衰
- [ ] Vega: ボラティリティ感応度
- [ ] Rho: 割引率に対する感応度

### タスク5: 商品市場特有の機能（理想実装）
- [ ] 複数満期のストリップ価格計算（完全実装）
- [ ] カレンダースプレッド対応（完全実装）
- [ ] **注意**: アジア型は別モデルとして実装（Black76には含めない）

### タスク6: Python APIの実装
```python
# python/quantforge/models/black76.py
def call_price(forward, strike, time, rate, sigma):
    """商品先物のコールオプション価格"""
    
def put_price(forward, strike, time, rate, sigma):
    """商品先物のプットオプション価格"""
    
def greeks(forward, strike, time, rate, sigma, is_call=True):
    """商品先物のグリークス"""
    
def from_spot_to_forward(spot, rate, div_yield, time):
    """スポット価格からフォワード価格への変換
    F = S * exp((r - q) * T)
    """
```
**注意**: パラメータ名は既存APIとの一貫性を保持

### タスク7: テストの実装
- [ ] 単体テスト（価格計算の精度検証）
- [ ] Put-Callパリティのテスト
- [ ] 境界値テスト（T→0、F→0、F→∞）
- [ ] Black-Scholesとの一貫性テスト
- [ ] パフォーマンステスト

### タスク8: ドキュメント作成
- [ ] `docs/models/black76.md` - モデル説明
- [ ] `docs/api/python/black76.md` - API文書
- [ ] 商品市場での使用例
- [ ] フォワード価格の計算方法

## 技術的詳細

### フォワード価格の扱い
```rust
// フォワード価格は直接入力として受け取る
// スポット価格からの変換はユーザー側で行う
// F = S * exp((r - q) * T)  // 参考式
```

### Black-Scholesとの関係
- Black76は`S = F * exp(-r*T)`と置換したBlack-Scholes
- 数値計算の効率化（exp関数の削減）

### 最適化の考慮点
- 割引係数`exp(-r*T)`の事前計算
- d1, d2の計算最適化
- SIMD対応バッチ処理

## 検証基準

### 精度要件
- 価格精度: 相対誤差 < 1e-6
- グリークス精度: 相対誤差 < 1e-5
- Put-Callパリティ: 誤差 < 1e-10

### パフォーマンス要件
- 単一計算: < 12ns
- バッチ処理（100万件）: < 25ms

### 市場慣行との整合性
- 商品市場の標準的な価格表記
- 先物満期日の扱い
- 営業日カレンダー対応（将来）

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| フォワード価格の誤解釈 | HIGH | 明確なドキュメント、変換関数の提供 |
| 金利期間構造の扱い | MEDIUM | 完全な期間構造モデルを最初から実装 |
| 商品固有の慣行 | LOW | 各市場の慣行を完全実装 |

## 商品市場での応用例

### エネルギー市場
```python
# 原油先物オプション（実装時は定数を使用 - C011-3）
from quantforge.constants import WTI_VOLATILITY, RISK_FREE_RATE

oil_forward = get_current_wti_forward()  # 外部データソースから取得
strike = get_strike_price()
time = calculate_time_to_maturity()

call_price = black76.call_price(oil_forward, strike, time, RISK_FREE_RATE, WTI_VOLATILITY)
```
**注意**: ハードコード値は使用禁止（C011-3適用）

### 農産物市場
```python
# コーン先物オプション
from quantforge.constants import COMMODITY_DEFAULTS

corn_forward = get_corn_forward_price()  # 外部データソースから取得
strike = get_strike_from_market()
# 以下、定数使用を徹底
```

## 参考資料

- Black, F. (1976). "The pricing of commodity contracts"
- Davis Edwards "Energy Trading and Investing"
- draft/GBS_2025.py - Black76実装の参照

## 成功基準

1. **正確性**: 市場標準ツールとの誤差 < 1e-6
2. **性能**: Black-Scholesと同等の実行速度
3. **テスト**: カバレッジ90%以上
4. **ドキュメント**: 商品市場での使用例を含む
5. **拡張性**: 他の商品オプションモデルへの拡張準備

## 次のステップ

1. モジュール構造の作成
2. 基本的な価格計算の実装
3. グリークス計算の追加
4. 商品市場固有の拡張

## 関連モデル（別実装）

以下は独立したモデルとして実装（C004/C014適用）：
- Asian76モデル（アジアンオプション）- 別計画書作成
- Kirk's Approximation（スプレッドオプション）- 別計画書作成
- 季節性考慮モデル - 別計画書作成
- ストレージコストモデル - 別計画書作成

**重要**: 段階的拡張や後での改善は禁止（C004/C014）

## 更新履歴

- 2025-08-26: 初版作成（2025-08-26-multi-model-architecture.mdから分離）
- 2025-08-26: Critical Rules準拠に更新
  - D-SSoTプロトコル警告追加
  - C011-3: ハードコード値を削除
  - C004/C014: 段階的実装の記述を削除
  - パラメータ名を統一（forward, strike, time, rate, sigma）
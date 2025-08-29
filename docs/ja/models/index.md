(models-index)=
# 数理モデル

QuantForgeで実装されているオプション価格モデルの数学的背景と理論。

(models-index-overview)=
## モデル一覧

(models-index-implemented)=
### 実装済みモデル
- [Black-Scholesモデル](black_scholes.md) - ヨーロピアンオプションの標準モデル ✅
- [Black76モデル](black76.md) - 商品先物・金利先物オプション ✅
- [Mertonモデル](merton.md) - 配当付き資産のオプション ✅
- [アメリカンオプション](american_options.md) - Bjerksund-Stensland 2002近似 ✅

(models-index-in-development)=
### 開発中モデル
- [アジアンオプション](asian_options.md) - 平均価格オプション ⚠️

(models-index-future)=
### 将来実装予定
- Garman-Kohlhagenモデル - FXオプション
- スプレッドオプション - Kirk近似
- バリアオプション - ノックイン/ノックアウト
- ルックバックオプション - パス依存型

(models-index-assumptions)=
## 基本仮定

QuantForgeのモデルは以下の仮定に基づいています：

(models-index-market-assumptions)=
### 市場の仮定
1. **完全市場**: 取引コスト、税金、借入制限なし
2. **無裁定**: リスクなしで利益を得る機会が存在しない
3. **流動性**: いつでも買い手と売り手が存在

(models-index-asset-assumptions)=
### 原資産の仮定
1. **幾何ブラウン運動**: $dS_t = \mu S_t dt + \sigma S_t dW_t$
2. **ボラティリティ一定**: $\sigma$ は時間と価格に依存しない
3. **配当**: 連続配当率 $q$ または離散配当

(models-index-risk-neutral)=
## リスク中立評価

(models-index-risk-neutral-probability)=
### リスク中立確率

リスク中立世界での期待値：

```{math}
:name: models-index-eq-risk-neutral

V_0 = e^{-rT} \mathbb{E}^\mathbb{Q}[V_T]
```

where:
- $\mathbb{Q}$: リスク中立確率測度
- $r$: 無リスク金利
- $T$: 満期までの時間

(models-index-girsanov)=
### Girsanovの定理

現実の確率測度 $\mathbb{P}$ からリスク中立測度 $\mathbb{Q}$ への変換：

```{math}
:name: models-index-eq-girsanov

\frac{d\mathbb{Q}}{d\mathbb{P}} = \exp\left(-\frac{1}{2}\int_0^T \theta_s^2 ds - \int_0^T \theta_s dW_s\right)
```

(models-index-numerical-methods)=
## 数値計算手法

(models-index-analytical)=
### 解析解

以下のモデルは解析解を持ちます：
- Black-Scholes（ヨーロピアン）
- 幾何平均アジアン
- デジタルオプション

(models-index-approximation)=
### 近似手法

複雑なモデルの高速計算：
- **Bjerksund-Stensland**: アメリカンオプション
- **Kirk近似**: スプレッドオプション
- **ボラティリティ調整**: 算術平均アジアン

(models-index-numerical-integration)=
### 数値積分

累積正規分布関数の計算：

```{code-block} python
:name: models-index-code-cumulative-normal
:caption: 累積正規分布の計算

def cumulative_normal(x):
    """高精度累積正規分布"""
    # Hart68アルゴリズム
    # 精度: < 1e-15
```

(models-index-greeks)=
## グリークス

(models-index-first-order-greeks)=
### 一階微分

```{list-table} 一階グリークス
:name: models-index-table-first-order-greeks
:header-rows: 1
:widths: 20 20 30 30

* - グリーク
  - 記号
  - 定義
  - 解釈
* - Delta
  - $\Delta$
  - $\frac{\partial V}{\partial S}$
  - 原資産価格感応度
* - Vega
  - $\nu$
  - $\frac{\partial V}{\partial \sigma}$
  - ボラティリティ感応度
* - Theta
  - $\Theta$
  - $-\frac{\partial V}{\partial t}$
  - 時間価値減少
* - Rho
  - $\rho$
  - $\frac{\partial V}{\partial r}$
  - 金利感応度
```

(models-index-second-order-greeks)=
### 二階微分

```{list-table} 二階グリークス
:name: models-index-table-second-order-greeks
:header-rows: 1
:widths: 20 20 30 30

* - グリーク
  - 記号
  - 定義
  - 解釈
* - Gamma
  - $\Gamma$
  - $\frac{\partial^2 V}{\partial S^2}$
  - Deltaの変化率
* - Vanna
  - 
  - $\frac{\partial^2 V}{\partial S \partial \sigma}$
  - Deltaのボラ感応度
* - Volga
  - 
  - $\frac{\partial^2 V}{\partial \sigma^2}$
  - Vegaの変化率
```

(models-index-numerical-stability)=
## 数値安定性

(models-index-underflow-prevention)=
### アンダーフロー対策

極端なパラメータでの安定性：

```{code-block} rust
:name: models-index-code-stable-calculation
:caption: 数値安定性の確保
:linenos:

fn stable_calculation(spot: f64, strike: f64, vol: f64, time: f64) -> f64 {
    // 小さい時間での特別処理
    if time < 1e-7 {
        return intrinsic_value(spot, strike);
    }
    
    // 小さいボラティリティでの特別処理
    if vol < 1e-7 {
        return discounted_intrinsic(spot, strike, rate, time);
    }
    
    // 通常の計算
    black_scholes_call(spot, strike, rate, vol, time)
}
```

(models-index-accuracy-guarantee)=
### 精度保証

二重精度(f64)での最大誤差：
- Black-Scholes: < 1e-15
- アメリカン: < 1e-10
- アジアン: < 1e-12

(models-index-performance-optimization)=
## パフォーマンス最適化

(models-index-precomputation)=
### 事前計算

共通項の再利用：

```{code-block} rust
:name: models-index-code-precomputed
:caption: 事前計算値の構造体

struct PrecomputedValues {
    sqrt_time: f64,
    vol_sqrt_time: f64,
    discount_factor: f64,
    d1: f64,
    d2: f64,
    nd1: f64,
    nd2: f64,
}
```

(models-index-parallel-processing)=
### 並列処理

Rayonによるバッチ処理：

```{code-block} rust
:name: models-index-code-parallel
:caption: 並列処理の実装
:linenos:

use rayon::prelude::*;

fn black_scholes_parallel(
    spots: &[f64],
    strikes: &[f64],
    rate: f64,
    vol: f64,
    time: f64,
) -> __m512d {
    // 8個のオプションを同時計算
}
```

(models-index-validation-tests)=
## 検証テスト

(models-index-put-call-parity)=
### Put-Callパリティ

```{math}
:name: models-index-eq-put-call-parity

C - P = S_0 e^{-qT} - K e^{-rT}
```

(models-index-boundary-conditions)=
### 境界条件

- $C \geq \max(S - Ke^{-rT}, 0)$
- $P \geq \max(Ke^{-rT} - S, 0)$
- $C \leq S$
- $P \leq Ke^{-rT}$

(models-index-monotonicity)=
### モノトニシティ

- $\frac{\partial C}{\partial S} > 0$ (コールはSに増加)
- $\frac{\partial P}{\partial S} < 0$ (プットはSに減少)
- $\frac{\partial V}{\partial \sigma} > 0$ (ボラティリティに増加)

(models-index-references)=
## 参考文献

1. Black, F., & Scholes, M. (1973). The Pricing of Options and Corporate Liabilities.
2. Bjerksund, P., & Stensland, G. (2002). Closed Form Valuation of American Options.
3. Kirk, E. (1995). Correlation in the Energy Markets.
4. Hull, J. C. (2018). Options, Futures, and Other Derivatives.

(models-index-next-steps)=
## 次のステップ

- [Black-Scholesモデル](black_scholes.md) - 詳細な理論と実装
- [Black76モデル](black76.md) - 先物オプションの理論
- [Mertonモデル](merton.md) - 配当考慮の拡張
- [アメリカンオプション](american_options.md) - 早期行使の数学
- [アジアンオプション](asian_options.md) - パス依存型オプション
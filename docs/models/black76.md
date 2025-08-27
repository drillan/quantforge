# Black76モデル

商品先物、金利デリバティブ、為替オプションの価格理論の標準モデルです。

## 理論的背景

### 基本概念

Black76モデルは、Fischer Black（1976）により提案された先物オプションの価格モデルです。
Black-Scholesモデルをフォワード価格ベースに拡張したもので、以下の特徴があります：

1. **フォワード価格の使用**: スポット価格の代わりにフォワード価格を使用
2. **保管コストの暗黙的処理**: フォワード価格に保管コスト・便益利回りが反映
3. **金利の役割**: 割引のみに使用（ドリフト項には現れない）

### 基本仮定

1. **対数正規分布**: フォワード価格は幾何ブラウン運動に従う
   $$dF_t = \sigma F_t dW_t$$
   （ドリフト項がないことに注意）

2. **効率的市場**: 取引コスト、税金なし、無制限の借入・貸出

3. **一定パラメータ**: ボラティリティと金利は一定

4. **フォワード価格のマルチンゲール性**: リスク中立測度下でフォワード価格はマルチンゲール

## 価格式の導出

### Black76方程式

フォワード価格 $F$ に対するオプション価値 $V(F,t)$ は以下の偏微分方程式を満たす：

$$\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 F^2 \frac{\partial^2 V}{\partial F^2} - rV = 0$$

### 境界条件

コールオプション:
- $V(F, T) = \max(F - K, 0)$
- $V(0, t) = 0$
- $V(F, t) \to e^{-r(T-t)}(F - K)$ as $F \to \infty$

プットオプション:
- $V(F, T) = \max(K - F, 0)$
- $V(0, t) = Ke^{-r(T-t)}$
- $V(F, t) \to 0$ as $F \to \infty$

## 解析解

### ヨーロピアンコール

$$C = e^{-rT}[F N(d_1) - K N(d_2)]$$

where:
- $d_1 = \frac{\ln(F/K) + \sigma^2 T/2}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$
- $N(x)$: 標準正規分布の累積分布関数

### ヨーロピアンプット

$$P = e^{-rT}[K N(-d_2) - F N(-d_1)]$$

## グリークス

オプション価格の感応度指標：

| グリーク | 意味 | コール | プット |
|---------|------|--------|--------|
| Delta | フォワード価格感応度 $\partial V/\partial F$ | $e^{-rT} N(d_1)$ | $-e^{-rT} N(-d_1)$ |
| Gamma | デルタの変化率 $\partial^2 V/\partial F^2$ | $\frac{e^{-rT} \phi(d_1)}{F \sigma \sqrt{T}}$ | 同左 |
| Vega | ボラティリティ感応度 $\partial V/\partial \sigma$ | $e^{-rT} F \phi(d_1) \sqrt{T}$ | 同左 |
| Theta | 時間価値減衰 $-\partial V/\partial T$ | 下記参照 | 下記参照 |
| Rho | 金利感応度 $\partial V/\partial r$ | $-T \cdot C$ | $-T \cdot P$ |

where $\phi(x) = \frac{1}{\sqrt{2\pi}}e^{-x^2/2}$ は標準正規分布の確率密度関数

### シータの詳細

時間減衰（1日あたり）：

コール:
$$\Theta_C = -e^{-rT} \left[ \frac{F \phi(d_1) \sigma}{2\sqrt{T}} + rK N(d_2) - rF N(d_1) \right] / 365$$

プット:
$$\Theta_P = -e^{-rT} \left[ \frac{F \phi(d_1) \sigma}{2\sqrt{T}} - rK N(-d_2) + rF N(-d_1) \right] / 365$$

## Black-Scholesとの関係

### 数学的等価性

Black76モデルは、Black-Scholesモデルにおいて配当利回り $q = r$ とした場合と数学的に等価です：

$$F = S e^{(r-q)T}$$

$q = r$ のとき: $F = S$（フォワード価格 = スポット価格）

### 実務上の違い

| 特徴 | Black-Scholes | Black76 |
|------|--------------|---------|
| 入力価格 | スポット $S$ | フォワード $F$ |
| ドリフト | $(r - q)$ | 0（マルチンゲール） |
| 保管コスト | 明示的（$q$） | 暗黙的（$F$に含む） |
| 主な用途 | 株式 | 商品・金利 |

## 応用分野

### 商品市場
エネルギーオプション（原油WTI/Brent、天然ガス、電力）の価格計算に広く使用されます。
保管コスト率 $u$ と便益利回り $y$ を考慮したフォワード価格 $F = S e^{(r + u - y)T}$ を使用します。
農産物（穀物、ソフトコモディティ）では季節性の考慮が重要です。

### 金利デリバティブ
キャップ・フロアの個別キャップレット/フロアレットの価格計算に使用されます。
スワプションではフォワードスワップレートを原資産として扱い、アニュイティファクターで調整します。
LIBORマーケットモデルの基礎となる重要な価格理論です。

### 為替オプション
外国通貨を商品とみなし、金利差を保管コストとして扱うことで価格計算を行います。
フォワード為替レートを使用することで、カバー付き金利パリティと整合的な価格が得られます。
企業の為替ヘッジや通貨オプション取引の標準的な価格モデルです。

## 数値計算上の考慮事項

### 精度要件

| 領域 | 精度目標 | 実装上の注意 |
|------|----------|-------------|
| ATM付近 | 相対誤差 < 1e-8 | 標準的な実装で十分 |
| 深いITM/OTM | 絶対誤差 < 1e-10 | 対数スケール計算推奨 |
| 短期満期 | 相対誤差 < 1e-6 | $\sqrt{T}$ の精度に注意 |

### 数値的課題と対策

1. **$d_1, d_2$ の計算**
   - $T \to 0$ で発散を避けるため最小値制限
   - $\ln(F/K)$ の精度確保

2. **正規分布関数 $N(x)$**
   - $|x| > 8$ で近似使用（$N(8) \approx 1$）
   - Erfcx関数による高精度計算

3. **極小ボラティリティ**
   - $\sigma < 0.001$ で特殊処理
   - 内在価値への収束を保証

## モデルの限界と拡張

### 限界

1. **ボラティリティスマイル**: 一定ボラティリティ仮定の限界
2. **早期行使**: アメリカンオプション非対応
3. **ジャンプリスク**: 連続的な価格変動仮定

### 拡張モデル

1. **SABR モデル**: ボラティリティスマイルの考慮
2. **確率的ボラティリティモデル**: Heston、SVIモデル
3. **ジャンプ拡散モデル**: Merton、Kouモデル

## 実装例（概念）

```python
import numpy as np
from scipy.stats import norm

def black76_call(F, K, T, r, sigma):
    """Black76コールオプション価格"""
    d1 = (np.log(F/K) + 0.5*sigma**2*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    call_price = np.exp(-r*T) * (F*norm.cdf(d1) - K*norm.cdf(d2))
    return call_price

def black76_put(F, K, T, r, sigma):
    """Black76プットオプション価格"""
    d1 = (np.log(F/K) + 0.5*sigma**2*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    
    put_price = np.exp(-r*T) * (K*norm.cdf(-d2) - F*norm.cdf(-d1))
    return put_price
```

## 参考文献

1. Black, F. (1976). "The pricing of commodity contracts", *Journal of Financial Economics*, 3(1-2), 167-179.

2. Hull, J. C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

3. Haug, E. G. (2007). *The Complete Guide to Option Pricing Formulas* (2nd ed.). McGraw-Hill.

4. Shreve, S. E. (2004). *Stochastic Calculus for Finance II: Continuous-Time Models*. Springer.

5. Musiela, M., & Rutkowski, M. (2005). *Martingale Methods in Financial Modelling*. Springer.

## 関連ドキュメント

- [Black76モデル API](../api/python/black76.md) - Python API使用方法
- [Black-Scholesモデル](black_scholes.md) - 株式オプションモデル
- [価格計算API概要](../api/python/pricing.md) - 統合APIインターフェース
# Black-Scholesモデル

オプション価格理論の基礎となる最も重要なモデルです。

## 理論的背景

### 基本概念

Black-Scholesモデルは、Fischer BlackとMyron Scholesが1973年に発表したオプション価格モデルです。
Robert Mertonも同時期に独立して同様のモデルを開発し、1997年にScholesとMertonはノーベル経済学賞を受賞しました。

このモデルは、無裁定価格理論とリスク中立評価法を用いて、ヨーロピアンオプションの理論価格を解析的に導出します。

### 基本仮定

1. **対数正規分布**: 株価は幾何ブラウン運動に従う
   $$dS_t = \mu S_t dt + \sigma S_t dW_t$$

2. **効率的市場**: 取引コスト、税金なし、無制限の借入・貸出

3. **一定パラメータ**: ボラティリティと金利は一定

4. **無裁定**: 市場に裁定機会は存在しない

5. **ヨーロピアン型**: 満期時のみ行使可能

## 価格式の導出

### Black-Scholes方程式

リスク中立測度下での偏微分方程式：

$$\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} - rV = 0$$

### 境界条件

コールオプション:
- $V(S, T) = \max(S - K, 0)$
- $V(0, t) = 0$
- $V(S, t) \to S - Ke^{-r(T-t)}$ as $S \to \infty$

プットオプション:
- $V(S, T) = \max(K - S, 0)$
- $V(0, t) = Ke^{-r(T-t)}$
- $V(S, t) \to 0$ as $S \to \infty$

## 解析解

### ヨーロピアンコール

$$C = S_0 N(d_1) - Ke^{-rT} N(d_2)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$
- $N(x)$: 標準正規分布の累積分布関数

### ヨーロピアンプット

$$P = Ke^{-rT} N(-d_2) - S_0 N(-d_1)$$

Put-Callパリティ:
$$C - P = S_0 - Ke^{-rT}$$

## グリークス

オプション価格の感応度指標：

| グリーク | 意味 | コール | プット |
|---------|------|--------|--------|
| Delta | 株価感応度 $\partial V/\partial S$ | $N(d_1)$ | $-N(-d_1)$ |
| Gamma | デルタの変化率 $\partial^2 V/\partial S^2$ | $\frac{\phi(d_1)}{S_0 \sigma \sqrt{T}}$ | 同左 |
| Vega | ボラティリティ感応度 $\partial V/\partial \sigma$ | $S_0 \phi(d_1) \sqrt{T}$ | 同左 |
| Theta | 時間価値減衰 $-\partial V/\partial T$ | $-\frac{S_0 \phi(d_1) \sigma}{2\sqrt{T}} - rKe^{-rT}N(d_2)$ | $-\frac{S_0 \phi(d_1) \sigma}{2\sqrt{T}} + rKe^{-rT}N(-d_2)$ |
| Rho | 金利感応度 $\partial V/\partial r$ | $KTe^{-rT}N(d_2)$ | $-KTe^{-rT}N(-d_2)$ |

where $\phi(x) = \frac{1}{\sqrt{2\pi}}e^{-x^2/2}$ は標準正規分布の確率密度関数

## Mertonとの関係

### 連続配当への拡張

配当利回り $q$ を考慮したMertonモデル：

$$C = S_0 e^{-qT} N(d_1) - Ke^{-rT} N(d_2)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r - q + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $q = 0$ の場合、標準のBlack-Scholesモデルに帰着

### 離散配当の扱い

配当落ち日 $t_i$ での配当 $D_i$ を考慮：
$$S_{\text{ex-div}} = S_0 - \sum_{t_i < T} D_i e^{-rt_i}$$

## 応用分野

### 株式オプション
個別株オプションの価格計算とリスク管理の基礎となるモデルです。
従業員ストックオプション（ESO）の評価や、ワラントの価格計算にも使用されます。
配当落ち日での調整が必要な場合はMertonモデルへの拡張が必要です。

### 株価指数オプション
S&P 500、日経225、FTSE 100などの主要株価指数オプションの価格計算に使用されます。
ETFオプションの評価にも広く適用され、機関投資家のポートフォリオヘッジに活用されています。
指数の連続配当利回りを考慮する必要があるため、実務ではMerton拡張が一般的です。

### 為替オプション
Garman-Kohlhagen拡張により外国為替オプションの価格計算が可能になります。
国内金利と外国金利の2つを考慮し、外国金利を配当利回りとして扱います。
企業の為替リスクヘッジや、投機的なFX取引の価格評価に使用されます。

### デリバティブプライシング全般
より複雑なモデル（確率的ボラティリティ、ジャンプ拡散等）の基礎となる理論です。
ボラティリティサーフェスの較正やリスク中立評価の概念理解に不可欠です。
金融機関のリスク管理システムの中核として、VaRやストレステストの基準モデルとして機能します。

## 数値計算上の考慮事項

### 精度要件
- 価格精度: 相対誤差 < $10^{-8}$
- グリークス精度: 相対誤差 < $10^{-7}$
- Put-Callパリティ: 誤差 < $10^{-12}$

### 数値的課題と対策

1. **極限値での不安定性**
   - 満期直前（$T \to 0$）: 境界値を直接返す
   - ゼロボラティリティ（$\sigma \to 0$）: 確定的なペイオフ
   - Deep ITM/OTM: 漸近展開を使用

2. **累積正規分布の高精度計算**
   - Hart68アルゴリズムやAS241の使用
   - 誤差 < $10^{-15}$ を達成

3. **並列処理**
   - Rayonによる効率的な並列計算
   - バッチ処理での大幅な高速化

## モデルの限界と拡張

### 限界
- **ボラティリティスマイル**: 実市場では観測される現象を説明不可
- **早期行使**: アメリカンオプションには適用不可
- **ジャンプリスク**: 急激な価格変動を考慮しない
- **取引コスト**: 現実の市場摩擦を無視

### 拡張モデル
- **確率的ボラティリティ**: Heston、SABRモデル
- **ジャンプ拡散**: Merton Jump Diffusion
- **局所ボラティリティ**: Dupireモデル
- **アメリカンオプション**: 二項ツリー、有限差分法

## 実装例（概念）

```python
# 概念的な実装例（実際のAPIとは異なる）
import numpy as np
from scipy.stats import norm

def black_scholes_call_price(s, k, t, r, sigma):
    """
    Black-Scholesモデルによるコールオプション価格
    
    Parameters:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間
        r: 無リスク金利
        sigma: ボラティリティ
    
    Returns:
        コールオプション価格
    """
    # 数値安定性のチェック
    if t < 1e-10:
        return max(s - k, 0.0)
    
    if sigma < 1e-10:
        forward = s * np.exp(r * t)
        return max((forward - k) * np.exp(-r * t), 0.0)
    
    # d1, d2の計算
    d1 = (np.log(s / k) + (r + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    
    # Black-Scholes価格式
    call_price = s * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    
    return call_price
```

## 参考文献

1. Black, F. and Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities." *Journal of Political Economy*, 81(3), 637-654.

2. Merton, R.C. (1973). "Theory of Rational Option Pricing." *Bell Journal of Economics and Management Science*, 4(1), 141-183.

3. Hull, J.C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

4. Wilmott, P. (2006). *Paul Wilmott on Quantitative Finance* (2nd ed.). Wiley.

## 関連ドキュメント

- [Black-Scholes API](../api/python/black_scholes.md)
- [Mertonモデル](merton.md)
- [Black76モデル](black76.md)
- [インプライドボラティリティ](../api/python/implied_vol.md)
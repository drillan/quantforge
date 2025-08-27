# Mertonモデル

配当を考慮したオプション価格理論の標準モデルです。

## 理論的背景

### 基本概念

Mertonモデルは、Black-Scholesモデルを配当支払いのある資産に拡張したものです。
連続的な配当利回り（dividend yield）を考慮することで、配当を支払う株式、株価指数、外国為替などのオプション価格を正確に計算できます。

配当利回り `q` がある場合、配当支払い後の株価は元の株価より低くなるため、この効果を価格計算に織り込む必要があります。

### 基本仮定

1. **対数正規分布**: 配当調整後の株価が幾何ブラウン運動に従う
   $$dS_t = (\mu - q) S_t dt + \sigma S_t dW_t$$

2. **連続配当**: 配当利回り `q` は一定かつ連続的に支払われる

3. **効率的市場**: Black-Scholesと同様、取引コスト・税金なし、無制限の借入・貸出

4. **一定パラメータ**: ボラティリティ、金利、配当利回りは一定

## 価格式の導出

### Merton方程式

配当を考慮した偏微分方程式：

$$\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + (r - q)S\frac{\partial V}{\partial S} - rV = 0$$

配当利回り `q` がドリフト項に影響を与えることに注目してください。

### 境界条件

コールオプション:
- $V(S, T) = \max(S - K, 0)$
- $V(0, t) = 0$
- $V(S, t) \to S e^{-q(T-t)} - Ke^{-r(T-t)}$ as $S \to \infty$

プットオプション:
- $V(S, T) = \max(K - S, 0)$
- $V(0, t) = Ke^{-r(T-t)}$
- $V(S, t) \to 0$ as $S \to \infty$

## 解析解

### ヨーロピアンコール

$$C = S_0 e^{-qT} N(d_1) - Ke^{-rT} N(d_2)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r - q + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$
- $N(x)$: 標準正規分布の累積分布関数

### ヨーロピアンプット

$$P = Ke^{-rT} N(-d_2) - S_0 e^{-qT} N(-d_1)$$

## グリークス

配当利回りを考慮したオプション価格の感応度指標：

| グリーク | 意味 | コール | プット |
|---------|------|--------|--------|
| Delta | 株価感応度 $\partial V/\partial S$ | $e^{-qT} N(d_1)$ | $-e^{-qT} N(-d_1)$ |
| Gamma | デルタの変化率 $\partial^2 V/\partial S^2$ | $\frac{e^{-qT} \phi(d_1)}{S_0 \sigma \sqrt{T}}$ | 同左 |
| Vega | ボラティリティ感応度 $\partial V/\partial \sigma$ | $S_0 e^{-qT} \phi(d_1) \sqrt{T}$ | 同左 |
| Theta | 時間価値減衰 $-\partial V/\partial T$ | 下記参照 | 下記参照 |
| Rho | 金利感応度 $\partial V/\partial r$ | $KTe^{-rT}N(d_2)$ | $-KTe^{-rT}N(-d_2)$ |
| Dividend Rho | 配当利回り感応度 $\partial V/\partial q$ | $-TS_0 e^{-qT}N(d_1)$ | $TS_0 e^{-qT}N(-d_1)$ |

where $\phi(x) = \frac{1}{\sqrt{2\pi}}e^{-x^2/2}$ は標準正規分布の確率密度関数

### 特記事項

- **Delta**: 配当調整係数 $e^{-qT}$ により、配当なしのBlack-Scholesより小さくなります
- **Theta**: 配当項 $qS_0 e^{-qT}N(d_1)$ が追加されています
- **Dividend Rho**: Mertonモデル特有のグリークです

### シータの詳細

コール:
$$\Theta_{\text{call}} = -\frac{S_0 e^{-qT} \phi(d_1) \sigma}{2\sqrt{T}} + qS_0 e^{-qT}N(d_1) - rKe^{-rT}N(d_2)$$

プット:
$$\Theta_{\text{put}} = -\frac{S_0 e^{-qT} \phi(d_1) \sigma}{2\sqrt{T}} - qS_0 e^{-qT}N(-d_1) + rKe^{-rT}N(-d_2)$$

## Black-Scholesとの関係

### 数学的関係

配当利回り `q = 0` のとき、Mertonモデルは完全にBlack-Scholesモデルに一致します：

- $d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}$ （Black-Scholesと同一）
- $C = S_0 N(d_1) - Ke^{-rT} N(d_2)$ （Black-Scholes価格式）

### Forward価格による解釈

配当調整後のForward価格を $F = S_0 e^{(r-q)T}$ とすると：

$$d_1 = \frac{\ln(F/K) + \sigma^2T/2}{\sigma\sqrt{T}}$$

これはBlack76モデルの構造と類似しています。

## 応用分野

### 株価指数オプション

株価指数（S&P 500、日経225など）は構成銘柄からの配当を反映するため、Mertonモデルが適切です。
例：配当利回り2%の株価指数のオプション価格計算

### 外国為替オプション

外国通貨の金利を配当利回りとみなすことで、為替オプションの価格計算に応用できます。
- 国内金利: `r`
- 外国金利: `q`（配当利回りとして扱う）

### 商品先物オプション

保管コストや便益利回り（convenience yield）を配当利回りパラメータに組み込んで価格計算します。

## 数値計算上の考慮事項

### 精度要件

| 領域 | 精度目標 | 実装上の注意 |
|------|----------|-------------|
| 価格精度 | 相対誤差 < 1e-6 | 標準的な実装で十分 |
| グリークス | 相対誤差 < 1e-5 | 有限差分法での検証推奨 |
| Put-Callパリティ | 誤差 < 1e-10 | 理論的整合性の検証用 |

### 数値的課題と対策

1. **配当調整の事前計算**
   - 配当割引係数 $e^{-qT}$ を事前に計算して再利用
   - 調整後スポット価格での計算により数値誤差を最小化

2. **極限値での安定性**
   - $q \to 0$: Black-Scholesの計算に切り替え
   - $q \to r$: 特殊ケースとして処理
   - 大きな $q$: 数値オーバーフロー防止のための範囲チェック

3. **exp関数の最適化**
   - 共通項の事前計算: $e^{-rT}$, $e^{-qT}$
   - SIMD化での一括計算による高速化

## モデルの限界と拡張

### 限界

1. **連続配当の仮定**: 実際の配当は離散的
2. **一定配当利回り**: 現実には時間変動する
3. **ボラティリティ一定**: 配当落ち日周辺で変動
4. **早期行使**: アメリカンオプションには対応しない

### 拡張モデル

1. **離散配当モデル**: 配当落ち日を明示的にモデル化
2. **確率的配当モデル**: 配当利回りも確率過程として扱う
3. **アメリカンオプション対応**: 数値計算手法（二項木、有限差分法）との組み合わせ
4. **Jump-Diffusionモデル**: 配当落ちのジャンプを考慮

## 実装例（概念）

```python
# 概念的な実装例（実際のAPIとは異なる）
import numpy as np
from scipy.stats import norm

def merton_call(s, k, t, r, q, sigma):
    """
    Mertonモデルによるコールオプション価格
    
    Parameters:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間（年）
        r: 無リスク金利
        q: 配当利回り
        sigma: ボラティリティ
    """
    # 配当調整
    dividend_discount = np.exp(-q * t)
    rate_discount = np.exp(-r * t)
    
    # d1, d2の計算
    d1 = (np.log(s / k) + (r - q + 0.5 * sigma**2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    
    # 価格計算
    call_price = s * dividend_discount * norm.cdf(d1) - k * rate_discount * norm.cdf(d2)
    
    return call_price
```

## 参考文献

1. Merton, R.C. (1973). "Theory of Rational Option Pricing." *Bell Journal of Economics and Management Science*, 4(1), 141-183.

2. Black, F. and Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities." *Journal of Political Economy*, 81(3), 637-654.

3. Hull, J.C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

4. Haug, E.G. (2007). *The Complete Guide to Option Pricing Formulas* (2nd ed.). McGraw-Hill.

## 関連ドキュメント

- [Merton API](../api/python/merton.md) - Python APIの使用方法
- [Black-Scholesモデル](black_scholes.md) - 配当なしの基本モデル
- [Black76モデル](black76.md) - 先物・商品オプション向けモデル
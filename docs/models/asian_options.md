---
future_feature: true
---

# アジアンオプションモデル

:::{warning}
このページで説明されている機能は現在開発中です。
現在利用可能なモデルは[モデル一覧](index.md)をご確認ください。
実装予定時期についてはプロジェクトの開発計画をご確認ください。
:::

平均価格に基づくパス依存型オプションの価格評価モデルです。

## 理論的背景

### 基本概念

アジアンオプションは、満期までの期間中の原資産価格の平均値に基づいてペイオフが決定されるエキゾチックオプションです。
単一時点の価格ではなく平均価格を使用することで、価格操作のリスクを軽減し、ボラティリティを低下させます。

主に商品市場、為替市場、エネルギー市場で使用され、企業のヘッジニーズに適合した設計となっています。

### 基本仮定

1. **対数正規分布**: 原資産価格は幾何ブラウン運動に従う
   $$dS_t = \mu S_t dt + \sigma S_t dW_t$$

2. **効率的市場**: 取引コスト、税金なし、無制限の借入・貸出

3. **一定パラメータ**: ボラティリティと金利は一定

4. **観測頻度**: 離散的（日次、週次等）または連続的

5. **平均タイプ**: 算術平均または幾何平均

## 価格式の導出

### 算術平均アジアンオプション

算術平均価格：
$$A_T = \frac{1}{n}\sum_{i=1}^{n} S_{t_i}$$

偏微分方程式（2次元）：
$$\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} + \frac{S}{n}\frac{\partial V}{\partial A} - rV = 0$$

### 境界条件

コールオプション:
- $V(S, A, T) = \max(A - K, 0)$（平均価格型）
- $V(S, A, T) = \max(S - K, 0)$（平均ストライク型）

プットオプション:
- $V(S, A, T) = \max(K - A, 0)$（平均価格型）
- $V(S, A, T) = \max(K - S, 0)$（平均ストライク型）

## 解析解

### 幾何平均アジアンコール

幾何平均には閉形式解が存在：

$$C_{geo} = S_0 e^{(r-q-\sigma_A^2/2)T} N(d_1) - K e^{-rT} N(d_2)$$

where:
- $\sigma_A = \sigma / \sqrt{3}$ （連続観測の場合）
- $d_1 = \frac{\ln(S_0/K) + (r - q + \sigma_A^2/2)T}{\sigma_A\sqrt{T}}$
- $d_2 = d_1 - \sigma_A\sqrt{T}$

### 算術平均の近似（Turnbull-Wakeman）

算術平均の近似解：

$$C_{arith} \approx C_{BS}(S_0, K, T, r, \sigma_{adj})$$

調整ボラティリティ：
$$\sigma_{adj} = \sqrt{\frac{\ln(M_2) - 2\ln(M_1)}{T}}$$

where $M_1, M_2$ は1次、2次モーメント

## グリークス

アジアンオプションのグリークス：

| グリーク | 意味 | 特徴 |
|---------|------|------|
| Delta | 株価感応度 $\partial V/\partial S$ | バニラより小さい |
| Gamma | デルタの変化率 $\partial^2 V/\partial S^2$ | 満期近くで複雑 |
| Vega | ボラティリティ感応度 $\partial V/\partial \sigma$ | バニラの約1/√3 |
| Theta | 時間価値減衰 $-\partial V/\partial T$ | 観測期間で変化 |
| Rho | 金利感応度 $\partial V/\partial r$ | バニラと類似 |

## Black-Scholesとの関係

### ボラティリティ削減効果

平均化によりボラティリティが減少：
- 連続観測: $\sigma_{asian} = \sigma / \sqrt{3}$
- 離散観測: $\sigma_{asian} = \sigma \sqrt{\frac{n+1}{3n}}$

### 価格関係

アジアン価格 < バニラ価格（通常）：
$$C_{Asian} < C_{Black-Scholes}$$

### 極限での一致

観測回数1回の場合、バニラオプションと一致：
$$\lim_{n \to 1} C_{Asian}^{(n)} = C_{Black-Scholes}$$

## 応用分野

### 商品市場
原油価格の月次平均オプションや農産物の季節平均価格オプションに使用されます。
金属市場では四半期平均価格のヘッジに活用され、価格操作リスクを軽減します。
平均価格による決済は、単一時点の価格変動リスクを大幅に削減します。

### 為替市場
企業の継続的な為替エクスポージャーのヘッジに適しています。
月次平均レートオプションは、定期的な海外送金を行う企業に人気があります。
観光業界では季節的な為替変動リスクの管理に活用されています。

### エネルギー市場
電力価格の日次平均オプションは、電力会社のリスク管理に不可欠です。
天然ガスの月次平均スワップは、季節的な需要変動に対するヘッジとして機能します。
再生可能エネルギー事業者の長期的な収益安定化にも寄与しています。

### 株式市場
従業員持株会では平均取得価格の保証により、参加者のリスクを軽減します。
インデックスファンドの期間平均リターン保証や、年金基金の平均価格プロテクションに使用されます。
ドルコスト平均法と組み合わせた投資戦略の実装にも適用可能です。

## 数値計算上の考慮事項

### 精度要件
- 価格精度: 相対誤差 < $10^{-6}$
- グリークス精度: 相対誤差 < $10^{-5}$
- 幾何・算術近似誤差: < 1%

### 数値的課題と対策

1. **次元の呪い**
   - 対策: PDE次元削減技法
   - 変数変換による1次元化

2. **算術平均の複雑性**
   - 対策: モーメントマッチング法
   - Turnbull-Wakeman近似

3. **部分観測の処理**
   - 対策: 条件付き期待値の利用
   - 既観測平均の組み込み

## モデルの限界と拡張

### 限界
- **算術平均の解析解不在**: 近似手法に依存
- **パス依存性**: 計算負荷が高い
- **離散観測**: 連続近似の誤差
- **早期行使**: アメリカン型は非常に複雑

### 拡張モデル
- **確率的ボラティリティ**: アジアンHestonモデル
- **ジャンプ拡散**: アジアンMertonモデル
- **多資産**: バスケットアジアンオプション
- **ダブルアジアン**: 2つの平均価格を使用

## 実装例（概念）

```python
# 概念的な実装例（実際のAPIとは異なる）
# 将来実装予定のAPI

import numpy as np
from scipy.stats import norm

def geometric_asian_call_price(s, k, t, r, sigma, n_fixings):
    """
    幾何平均アジアンコールオプション価格（正確な解）
    
    Parameters:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間
        r: 無リスク金利
        sigma: ボラティリティ
        n_fixings: 観測回数
    
    Returns:
        幾何平均アジアンコール価格
    """
    # 調整パラメータ
    sigma_a = sigma * np.sqrt((n_fixings + 1) / (3 * n_fixings))
    mu_a = (r - 0.5 * sigma**2) * (n_fixings + 1) / (2 * n_fixings)
    
    # d1, d2の計算
    d1 = (np.log(s / k) + (mu_a + 0.5 * sigma_a**2) * t) / (sigma_a * np.sqrt(t))
    d2 = d1 - sigma_a * np.sqrt(t)
    
    # 幾何平均アジアン価格
    price = s * np.exp((mu_a - r) * t) * norm.cdf(d1) - k * np.exp(-r * t) * norm.cdf(d2)
    
    return price


def arithmetic_asian_call_approximation(s, k, t, r, sigma, n_fixings):
    """
    算術平均アジアンコールの近似価格（Turnbull-Wakeman）
    
    Parameters:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間
        r: 無リスク金利
        sigma: ボラティリティ
        n_fixings: 観測回数
    
    Returns:
        算術平均アジアンコール近似価格
    """
    # モーメント計算
    dt = t / n_fixings
    
    # 1次モーメント（期待値）
    m1 = s * np.exp(r * t) * (1 - np.exp(-r * t * n_fixings / n_fixings)) / (n_fixings * r * dt)
    
    # 2次モーメント
    sigma2_adj = sigma**2 * (2 * n_fixings + 1) / (6 * n_fixings)
    m2 = m1**2 * np.exp(sigma2_adj * t)
    
    # 調整ボラティリティ
    sigma_adj = np.sqrt(np.log(m2 / m1**2) / t)
    
    # Black-Scholes近似
    d1 = (np.log(m1 / k) + 0.5 * sigma_adj**2 * t) / (sigma_adj * np.sqrt(t))
    d2 = d1 - sigma_adj * np.sqrt(t)
    
    price = np.exp(-r * t) * (m1 * norm.cdf(d1) - k * norm.cdf(d2))
    
    return price
```

## 参考文献

1. Kemna, A.G.Z. and Vorst, A.C.F. (1990). "A Pricing Method for Options Based on Average Asset Values." *Journal of Banking and Finance*, 14(1), 113-129.

2. Turnbull, S.M. and Wakeman, L.M. (1991). "A Quick Algorithm for Pricing European Average Options." *Journal of Financial and Quantitative Analysis*, 26(3), 377-389.

3. Hull, J.C. and White, A. (1993). "Efficient Procedures for Valuing European and American Path-Dependent Options." *Journal of Derivatives*, 1(1), 21-31.

4. Vecer, J. (2001). "A New PDE Approach for Pricing Arithmetic Average Asian Options." *Journal of Computational Finance*, 4(4), 105-113.

## 関連ドキュメント

- アジアンオプション API（開発中）
- [Black-Scholesモデル](black_scholes.md)
- [Mertonモデル](merton.md)
- モンテカルロ法（開発中）
- エキゾチックオプション一覧（開発中）
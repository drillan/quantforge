(american-options)=
# アメリカンオプションモデル

早期行使権を持つオプションの価格評価モデルです。

(american-options-theory)=
## 理論的背景

(american-options-basic-concepts)=
### 基本概念

アメリカンオプションは、満期日以前の任意の時点で行使可能なオプションです。
早期行使権により、ヨーロピアンオプションよりも常に価値が高くなります（または同等）。

Bjerksund-Stensland（2002）モデルは、アメリカンオプションの解析的近似解を提供する高精度な手法で、
数値解法（二項ツリー、有限差分法）と比較して100倍以上高速でありながら、誤差0.1%未満を達成します。

(american-options-assumptions)=
### 基本仮定

1. **対数正規分布**: 株価は幾何ブラウン運動に従う
   
   ```{math}
   :name: american-options-eq-gbm
   
   dS_t = (\mu - q) S_t dt + \sigma S_t dW_t
   ```

2. **効率的市場**: 取引コスト、税金なし、無制限の借入・貸出

3. **一定パラメータ**: ボラティリティ、金利、配当利回りは一定

4. **早期行使可能**: 満期前の任意の時点で行使可能

5. **最適行使戦略**: 投資家は価値を最大化する戦略を選択

(american-options-derivation)=
## 価格式の導出

(american-options-pde)=
### アメリカンオプション評価の偏微分方程式

自由境界問題として定式化：

```{math}
:name: american-options-eq-pde

\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + (r-q)S\frac{\partial V}{\partial S} - rV = 0
```

早期行使条件：

```{math}
:name: american-options-eq-exercise-call

V(S,t) \geq \max(S-K, 0) \text{ for call}
```

```{math}
:name: american-options-eq-exercise-put

V(S,t) \geq \max(K-S, 0) \text{ for put}
```

(american-options-boundary-conditions)=
### 境界条件

コールオプション:
- $V(S, T) = \max(S - K, 0)$
- $V(0, t) = 0$
- $V(S^*, t) = S^* - K$ （早期行使境界）
- $\frac{\partial V}{\partial S}(S^*, t) = 1$ （スムースペースティング）

プットオプション:
- $V(S, T) = \max(K - S, 0)$
- $V(0, t) = K$
- $V(S^*, t) = K - S^*$ （早期行使境界）
- $\frac{\partial V}{\partial S}(S^*, t) = -1$ （スムースペースティング）

(american-options-analytical-solution)=
## 解析解

(american-options-european-call)=
### ヨーロピアンコール（Bjerksund-Stensland 2002）

アメリカンコールの近似解：

```{math}
:name: american-options-eq-call-formula

C_{Am} = \alpha S_0^{\beta} - \alpha \phi(S_0, T, \beta, I, I) + \phi(S_0, T, 1, I, I) - \phi(S_0, T, 1, K, I) - K\phi(S_0, T, 0, I, I) + K\phi(S_0, T, 0, K, I)
```

where:
- $I = B_0 + (B_\infty - B_0)(1 - e^{h(T)})$ は早期行使境界
- $\alpha, \beta$ は補助パラメータ
- $\phi$ は補助関数

(american-options-european-put)=
### ヨーロピアンプット

アメリカンプットの近似解は、コールオプションよりも複雑な構造を持ちます：

```{math}
:name: american-options-eq-put-formula

P_{Am} = K - S_0 + \text{European Put} + \text{Early Exercise Premium}
```

早期行使プレミアムは、最適停止理論を用いて計算されます。

(american-options-greeks)=
## グリークス

アメリカンオプションの価格感応度指標：

```{list-table} アメリカンオプションのグリークス
:name: american-options-table-greeks
:header-rows: 1
:widths: 20 30 25 25

* - グリーク
  - 意味
  - コール
  - プット
* - Delta
  - 株価感応度 $\partial V/\partial S$
  - 早期行使境界で不連続
  - 早期行使境界で不連続
* - Gamma
  - デルタの変化率 $\partial^2 V/\partial S^2$
  - 境界近傍で急増
  - 境界近傍で急増
* - Vega
  - ボラティリティ感応度 $\partial V/\partial \sigma$
  - ヨーロピアンより小さい
  - ヨーロピアンより小さい
* - Theta
  - 時間価値減衰 $-\partial V/\partial T$
  - 早期行使により複雑
  - 早期行使により複雑
* - Rho
  - 金利感応度 $\partial V/\partial r$
  - 正（通常）
  - 負（通常）
```

(american-options-specific-features)=
### アメリカンオプション特有の特徴

1. **早期行使境界の影響**
   - Delta: 境界での不連続性により、ヘッジが困難
   - Gamma: 境界付近でスパイクが発生、リスク管理に注意が必要

2. **ヨーロピアンとの差異**
   - Vega: 早期行使の可能性により、ボラティリティ感応度が低下
   - Theta: 早期行使プレミアムの時間減衰が追加される

3. **数値計算上の注意**
   - 解析的な式が存在しないため、有限差分法やモンテカルロ法で近似
   - Bjerksund-Stensland近似を使用した高速計算も可能

(american-options-black-scholes-relation)=
## Black-Scholesとの関係

(american-options-value-relation)=
### 価値の関係

アメリカンオプション価値 ≥ ヨーロピアンオプション価値：

```{math}
:name: american-options-eq-value-relation

C_{American} \geq C_{European}

P_{American} \geq P_{European}
```

(american-options-dividend-effect)=
### 配当の影響

- **配当なしコール**: アメリカン = ヨーロピアン（早期行使しない）
- **配当ありコール**: アメリカン > ヨーロピアン（配当直前に行使可能）
- **プット**: 配当に関わらずアメリカン > ヨーロピアン

(american-options-convergence)=
### 収束条件

満期が短い極限で、両者は一致：

```{math}
:name: american-options-eq-convergence

\lim_{T \to 0} (American - European) = 0
```

(american-options-applications)=
## 応用分野

(american-options-equity-options)=
### 株式オプション
- 個別株オプション（配当支払い時）
- 従業員ストックオプション
- 早期行使特約付きワラント

(american-options-commodity-derivatives)=
### 商品デリバティブ
- 商品先物オプション
- エネルギーオプション（原油、天然ガス）
- 農産物オプション

(american-options-interest-rate-derivatives)=
### 金利デリバティブ
- バミューダンスワップション
- モーゲージ担保証券（MBS）
- プリペイメントオプション

(american-options-numerical-considerations)=
## 数値計算上の考慮事項

(american-options-accuracy-requirements)=
### 精度要件
- 価格精度: 真値との誤差 < 0.1%
- グリークス精度: 相対誤差 < 1%
- 早期行使境界: 誤差 < 0.5%

(american-options-numerical-challenges)=
### 数値的課題と対策

1. **自由境界問題**
   - 対策: 反復法による境界の探索
   - 収束基準: $|S^*_{n+1} - S^*_n| < \epsilon$

2. **不連続性の処理**
   - 対策: 適応的メッシュ細分化
   - 早期行使境界近傍で高解像度

3. **高速計算**
   - 対策: Bjerksund-Stensland近似の使用
   - 計算時間: < 50ns/オプション

(american-options-limitations-extensions)=
## モデルの限界と拡張

(american-options-limitations)=
### 限界
- **離散配当**: 配当落ち日での不連続性
- **確率的パラメータ**: ボラティリティ・金利の変動を無視
- **取引制約**: 現実の市場制約を考慮しない
- **税制**: 税金の影響を無視

(american-options-extensions)=
### 拡張モデル
- **最小二乗モンテカルロ**: Longstaff-Schwartz法
- **確率的ボラティリティ**: アメリカンHestonモデル
- **ジャンプ拡散**: アメリカンMertonジャンプモデル
- **多資産**: バスケットアメリカンオプション

(american-options-implementation-example)=
## 実装例（概念）

```{code-block} python
:name: american-options-code-example
:caption: アメリカンコール価格の計算（概念）
:linenos:

# 概念的な実装例（実際のAPIとは異なる）
def american_call_price(s, k, t, r, sigma, q=0.0):
    """
    Bjerksund-Stensland 2002モデルによるアメリカンコール価格
    
    Parameters:
        s: スポット価格
        k: 権利行使価格
        t: 満期までの時間
        r: 無リスク金利
        sigma: ボラティリティ
        q: 配当利回り
    
    Returns:
        アメリカンコールオプション価格
    """
    # 配当なしの場合、ヨーロピアンと同じ
    if q == 0:
        return european_call_price(s, k, t, r, sigma)
    
    # Bjerksund-Stensland パラメータ計算
    beta = calculate_beta(r, q, sigma)
    b_infinity = calculate_b_infinity(k, r, q, sigma)
    b_zero = max(k, r * k / (r - q))
    
    # 早期行使境界の計算
    h_t = -(q * t + 2 * sigma * np.sqrt(t))
    i = b_zero + (b_infinity - b_zero) * (1 - np.exp(h_t))
    
    # 近似価格の計算
    if s >= i:
        return s - k  # 即座に行使
    else:
        # Bjerksund-Stensland式を適用
        alpha = calculate_alpha(i, k, r, q, beta)
        price = alpha * s**beta + phi_functions(s, t, beta, i, k, r, q, sigma)
        
    return price
```

(american-options-references)=
## 参考文献

1. Bjerksund, P. and Stensland, G. (2002). "Closed Form Valuation of American Options." *Working Paper, NHH Bergen*.

2. Longstaff, F.A. and Schwartz, E.S. (2001). "Valuing American Options by Simulation: A Simple Least-Squares Approach." *Review of Financial Studies*, 14(1), 113-147.

3. Hull, J.C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.

4. Barone-Adesi, G. and Whaley, R.E. (1987). "Efficient Analytic Approximation of American Option Values." *Journal of Finance*, 42(2), 301-320.

(american-options-related-docs)=
## 関連ドキュメント

- [アメリカンオプション API](../api/python/american.md)
- [Black-Scholesモデル](black_scholes.md)
- [Mertonモデル](merton.md)
- 二項ツリーモデル（開発中）
- 有限差分法（開発中）
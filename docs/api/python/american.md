# アメリカンオプションモデル API

早期行使権を持つオプションの価格計算のための高精度近似モデルです。

## 概要

Bjerksund-Stensland (2002) モデルによる解析的近似解を提供します。
二項ツリー法と比較して処理速度が100倍（測定条件：1000ステップ二項ツリー、Intel i9-12900K）、数値誤差は0.1%未満です。

## API使用方法

### 基本的な価格計算

```python
from quantforge.models import american

# コールオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
call_price = american.call_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)

# プットオプション価格
# パラメータ: s(spot), k(strike), t(time), r(rate), q(dividend), sigma
put_price = american.put_price(100.0, 105.0, 1.0, 0.05, 0.03, 0.2)
```

### バッチ処理

```python
import numpy as np

# 完全配列サポートとBroadcasting
spots = np.array([95, 100, 105, 110])
strikes = 100.0  # スカラーは自動拡張
times = np.array([0.5, 1.0, 1.5, 2.0])
rates = 0.05
dividend_yields = 0.03
sigmas = np.array([0.18, 0.20, 0.22, 0.24])

# パラメータ: spots, strikes, times, rates, dividend_yields, sigmas
call_prices = american.call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)
put_prices = american.put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas)

# Greeksバッチ計算（辞書形式）
greeks = american.greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls=False)
print(greeks['delta'])  # NumPy配列
print(greeks['gamma'])  # NumPy配列

# 早期行使境界のバッチ計算
boundaries = american.exercise_boundary_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls=False)
```

詳細は[Batch Processing API](batch_processing.md)を参照してください。

### グリークス計算

```python
# 全グリークスを一括計算
# パラメータ: s, k, t, r, q, sigma, is_call
greeks = american.greeks(100.0, 100.0, 1.0, 0.05, 0.03, 0.2, True)

# 個別のグリークスへアクセス
print(f"Delta: {greeks.delta:.4f}")  # スポット価格感応度
print(f"Gamma: {greeks.gamma:.4f}")  # デルタの変化率
print(f"Vega: {greeks.vega:.4f}")    # ボラティリティ感応度
print(f"Theta: {greeks.theta:.4f}")  # 時間価値減衰
print(f"Rho: {greeks.rho:.4f}")      # 金利感応度
```

### インプライドボラティリティ

```python
# パラメータ: price, s, k, t, r, q, is_call
iv = american.implied_volatility(15.50, 100.0, 100.0, 1.0, 0.05, 0.03, True)
print(f"Implied Volatility: {iv:.4f}")
```

### 早期行使境界

```python
# 早期行使境界の計算
# パラメータ: s, k, t, r, q, sigma, is_call
boundary = american.exercise_boundary(100.0, 100.0, 1.0, 0.05, 0.03, 0.2, True)
print(f"Exercise boundary: {boundary:.2f}")
```

## パラメータ説明

### 入力パラメータ

| パラメータ | 型 | 説明 | 有効範囲 |
|-----------|-----|------|----------|
| `s` | float | スポット価格 | > 0 |
| `k` | float | 権利行使価格 | > 0 |
| `t` | float | 満期までの時間（年） | > 0 |
| `r` | float | 無リスク金利 | ≥ 0 |
| `q` | float | 配当利回り | ≥ 0 |
| `sigma` | float | ボラティリティ（年率） | > 0 |
| `is_call` | bool | オプションタイプ | True: コール, False: プット |

### バッチ処理用パラメータ

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `spots` | np.ndarray | 複数のスポット価格 |
| `k` | float | 権利行使価格（共通） |
| `t` | float | 満期までの時間（共通） |
| `r` | float | 無リスク金利（共通） |
| `q` | float | 配当利回り（共通） |
| `sigma` | float | ボラティリティ（共通） |

## 価格式（参考）

コールオプション（Bjerksund-Stensland近似）:
$$C_{Am} = \alpha S_0^{\beta} - \alpha \phi(S_0, T, \beta, I, I) + \phi(S_0, T, 1, I, I) - K\phi(S_0, T, 0, K, I)$$

早期行使境界:
$$I = B_0 + (B_\infty - B_0)(1 - e^{h(T)})$$

where:
- $I$ は早期行使境界
- $\alpha, \beta$ は補助パラメータ
- $\phi$ は補助関数

詳細な理論的背景は[アメリカンオプションモデル理論](../../models/american_options.md)を参照してください。

## エラーハンドリング

すべての価格計算関数は以下の条件でエラーを返します：

- s ≤ 0（スポット価格が負または0）
- k ≤ 0（権利行使価格が負または0）
- t ≤ 0（満期までの時間が負または0）
- sigma ≤ 0（ボラティリティが負または0）
- q < 0（配当利回りが負）
- q > r（配当利回りが無リスク金利を超える - 配当裁定機会）
- 数値がNaNまたは無限大

```python
try:
    # パラメータ: s, k, t, r, q, sigma
    price = american.call_price(100.0, 100.0, 1.0, 0.05, 0.10, 0.2)  # q > r
except ValueError as e:
    print(f"入力エラー: {e}")
```

## パフォーマンス指標

| 操作 | 単一計算 | 100万件バッチ |
|------|----------|--------------:|
| コール/プット価格 | ~1 μs | ~500ms |
| 全グリークス | ~6 μs | ~6s |
| インプライドボラティリティ | ~10 μs | ~10s |
| 早期行使境界 | ~1 μs | ~1s |

## 使用例

### 配当付き株式オプションの評価

```python
from quantforge.models import american

# 配当利回り3%の株式のアメリカンプット
s = 100.0    # 現在の株価
k = 105.0    # 権利行使価格（ITM）
t = 0.5      # 6ヶ月満期
r = 0.05     # 無リスク金利5%
q = 0.03     # 配当利回り3%
sigma = 0.25 # ボラティリティ25%

# 価格計算
put_price = american.put_price(s, k, t, r, q, sigma)

print(f"Put Price: ${put_price:.2f}")

# グリークス計算
greeks = american.greeks(s, k, t, r, q, sigma, False)
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### 早期行使判定

```python
import numpy as np
from quantforge.models import american

# パラメータ設定
k = 100.0    # 権利行使価格
t = 1.0      # 1年満期
r = 0.05     # 無リスク金利
q = 0.03     # 配当利回り
sigma = 0.2  # ボラティリティ

# 早期行使境界の計算
boundary_call = american.exercise_boundary(100.0, k, t, r, q, sigma, True)
boundary_put = american.exercise_boundary(100.0, k, t, r, q, sigma, False)

print(f"Call exercise boundary: ${boundary_call:.2f}")
print(f"Put exercise boundary: ${boundary_put:.2f}")

# 現在の株価での行使判定
spots = np.array([80, 90, 100, 110, 120])
for s in spots:
    call_price = american.call_price(s, k, t, r, q, sigma)
    put_price = american.put_price(s, k, t, r, q, sigma)
    
    # 即座行使価値
    intrinsic_call = max(s - k, 0)
    intrinsic_put = max(k - s, 0)
    
    print(f"S=${s}: Call=${call_price:.2f} (intrinsic=${intrinsic_call:.2f}), "
          f"Put=${put_price:.2f} (intrinsic=${intrinsic_put:.2f})")
```

## 関連情報

- [Black-Scholesモデル](black_scholes.md) - ヨーロピアンオプション
- [Mertonモデル](merton.md) - 配当付きヨーロピアンオプション
- [インプライドボラティリティAPI](implied_vol.md) - IV計算の詳細
- [アメリカンオプション理論的背景](../../models/american_options.md) - 数学的詳細
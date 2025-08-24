# インプライドボラティリティAPI

市場価格からボラティリティを逆算する関数群です。

## 基本的なIV計算

### `implied_volatility()`

```python
quantforge.implied_volatility(
    price: Union[float, np.ndarray],
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    time: Union[float, np.ndarray],
    option_type: str = "call",
    initial_guess: Optional[Union[float, np.ndarray]] = None,
    max_iterations: int = 100,
    tolerance: float = 1e-8
) -> Union[float, np.ndarray]
```

市場価格からインプライドボラティリティを計算。

**パラメータ:**
- `price`: 市場で観測されたオプション価格
- `spot`: 現在価格
- `strike`: 行使価格
- `rate`: 無リスク金利
- `time`: 満期までの時間
- `option_type`: "call" または "put"
- `initial_guess`: 初期推定値（省略時は自動設定）
- `max_iterations`: 最大反復回数
- `tolerance`: 収束判定の許容誤差

**戻り値:**
- インプライドボラティリティ（年率）

**例:**
```python
# 単一のIV計算
market_price = 12.5
iv = qf.implied_volatility(
    price=market_price,
    spot=100,
    strike=110,
    rate=0.05,
    time=1.0,
    option_type="call"
)
print(f"Implied Volatility: {iv:.1%}")
```

## アメリカンオプションのIV

### `american_implied_vol()`

```python
quantforge.american_implied_vol(
    price: Union[float, np.ndarray],
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    time: Union[float, np.ndarray],
    option_type: str = "call",
    dividend: Union[float, np.ndarray] = 0.0
) -> Union[float, np.ndarray]
```

アメリカンオプション価格からのIV計算。

**特徴:**
- Bjerksund-Stensland逆算
- 早期行使プレミアムを考慮
- 配当付きオプション対応

## バッチIV計算

### `implied_volatility_batch()`

```python
quantforge.implied_volatility_batch(
    prices: np.ndarray,
    spots: Union[float, np.ndarray],
    strikes: Union[float, np.ndarray],
    rates: Union[float, np.ndarray],
    times: Union[float, np.ndarray],
    option_types: Optional[np.ndarray] = None,
    parallel: bool = True
) -> np.ndarray
```

大量のオプションのIVを並列計算。

**パラメータ:**
- `prices`: 市場価格の配列
- `option_types`: 各オプションのタイプ配列
- `parallel`: 並列処理を使用するか

**例:**
```python
# ボラティリティスマイルの計算
strikes = np.array([90, 95, 100, 105, 110])
market_prices = np.array([15.2, 11.8, 8.5, 5.7, 3.4])

ivs = qf.implied_volatility_batch(
    prices=market_prices,
    spots=100,
    strikes=strikes,
    rates=0.05,
    times=0.5
)
```

## 高度なIV計算

### `implied_vol_surface()`

```python
quantforge.implied_vol_surface(
    market_prices: np.ndarray,
    spot: float,
    strikes: np.ndarray,
    times: np.ndarray,
    rate: float = 0.05,
    smoothing: str = "none"
) -> np.ndarray
```

IVサーフェスの構築。

**パラメータ:**
- `market_prices`: 2次元配列 (strikes × times)
- `smoothing`: スムージング手法
  - `"none"`: スムージングなし
  - `"svi"`: SVIモデル
  - `"sabr"`: SABRモデル

**戻り値:**
- IVサーフェス（2次元配列）

## IVの検証

### `validate_iv()`

```python
quantforge.validate_iv(
    iv: Union[float, np.ndarray],
    moneyness: Union[float, np.ndarray],
    time: Union[float, np.ndarray]
) -> np.ndarray
```

計算されたIVの妥当性を検証。

**チェック項目:**
- 無裁定条件
- バタフライスプレッド条件
- カレンダースプレッド条件

**戻り値:**
- 検証結果のブール配列

## IVの補間

### `interpolate_iv()`

```python
quantforge.interpolate_iv(
    known_strikes: np.ndarray,
    known_ivs: np.ndarray,
    target_strikes: np.ndarray,
    method: str = "cubic"
) -> np.ndarray
```

既知のIVから未知の行使価格のIVを補間。

**method:**
- `"linear"`: 線形補間
- `"cubic"`: 3次スプライン
- `"sabr"`: SABRモデル補間

## 収束アルゴリズム

### Newton-Raphson法

デフォルトの高速アルゴリズム：

```python
# 内部実装の疑似コード
def newton_raphson_iv(price, spot, strike, rate, time):
    vol = 0.2  # 初期推定
    for _ in range(max_iterations):
        bs_price = black_scholes(spot, strike, rate, vol, time)
        vega = calculate_vega(spot, strike, rate, vol, time)
        
        if abs(bs_price - price) < tolerance:
            return vol
            
        vol = vol - (bs_price - price) / vega
    
    raise ConvergenceError("IV計算が収束しませんでした")
```

### Brent法（フォールバック）

Newton-Raphson法が失敗した場合の堅牢なアルゴリズム：

```python
# Brent法を明示的に使用
iv = qf.implied_volatility_brent(
    price=12.5,
    spot=100,
    strike=110,
    rate=0.05,
    time=1.0,
    lower_bound=0.001,
    upper_bound=5.0
)
```

## パフォーマンス

### 計算速度

| メソッド | 単一計算 | 精度 |
|---------|----------|------|
| Newton-Raphson | < 200ns | 1e-8 |
| Brent | < 500ns | 1e-10 |
| Batch (並列) | < 50ns/option | 1e-8 |

### 最適化テクニック

```python
# 初期推定値の最適化
def optimal_initial_guess(price, spot, strike, time):
    """ATMボラティリティからの初期推定"""
    moneyness = spot / strike
    if 0.9 < moneyness < 1.1:
        # ATM近辺
        return 0.2
    else:
        # OTM/ITM
        return 0.3 * abs(np.log(moneyness)) + 0.15

# カスタム初期推定値の使用
iv = qf.implied_volatility(
    price=12.5,
    spot=100,
    strike=110,
    rate=0.05,
    time=1.0,
    initial_guess=optimal_initial_guess(12.5, 100, 110, 1.0)
)
```

## エラー処理

### 一般的なエラー

```python
class IVConvergenceError(QuantForgeError):
    """IV計算の収束失敗"""
    
class IVBoundsError(QuantForgeError):
    """IVが有効範囲外"""
    
class NoArbitrageViolation(QuantForgeError):
    """無裁定条件違反"""
```

### エラー処理例

```python
def safe_iv_calculation(prices, spots, strikes, rates, times):
    """安全なIV計算"""
    ivs = []
    errors = []
    
    for i in range(len(prices)):
        try:
            iv = qf.implied_volatility(
                prices[i], spots[i], strikes[i], 
                rates[i], times[i]
            )
            ivs.append(iv)
            errors.append(None)
        except qf.IVConvergenceError as e:
            ivs.append(np.nan)
            errors.append(f"Convergence failed: {e}")
        except qf.IVBoundsError as e:
            ivs.append(np.nan)
            errors.append(f"IV out of bounds: {e}")
    
    return np.array(ivs), errors
```

## 実用例

### ボラティリティスマイルの構築

```python
import matplotlib.pyplot as plt

# データ準備
spot = 100
strikes = np.linspace(80, 120, 21)
time = 0.25
rate = 0.05

# 仮想的な市場価格（スマイル効果を含む）
market_prices = []
for k in strikes:
    base_vol = 0.2 + 0.002 * abs(k - spot)  # スマイル
    price = qf.black_scholes_call(spot, k, rate, base_vol, time)
    market_prices.append(price)

# IV計算
ivs = qf.implied_volatility_batch(
    prices=np.array(market_prices),
    spots=spot,
    strikes=strikes,
    rates=rate,
    times=time
)

# プロット
plt.figure(figsize=(10, 6))
plt.plot(strikes, ivs * 100, 'o-')
plt.xlabel('Strike Price')
plt.ylabel('Implied Volatility (%)')
plt.title('Volatility Smile')
plt.grid(True, alpha=0.3)
plt.show()
```

### IVサーフェスのフィッティング

```python
# 市場データから完全なIVサーフェス構築
def fit_iv_surface(market_data):
    """市場データからIVサーフェスをフィット"""
    
    # データ整形
    strikes = market_data['strike'].unique()
    expiries = market_data['expiry'].unique()
    
    # グリッド作成
    surface = np.zeros((len(strikes), len(expiries)))
    
    for i, k in enumerate(strikes):
        for j, t in enumerate(expiries):
            mask = (market_data['strike'] == k) & (market_data['expiry'] == t)
            if mask.any():
                price = market_data.loc[mask, 'price'].values[0]
                iv = qf.implied_volatility(
                    price=price,
                    spot=100,
                    strike=k,
                    rate=0.05,
                    time=t
                )
                surface[i, j] = iv
    
    return strikes, expiries, surface
```
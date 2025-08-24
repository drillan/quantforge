# 価格計算API

オプション価格計算のための主要な関数群です。

## 汎用計算関数

### `calculate()`

```python
quantforge.calculate(
    spots: Union[float, np.ndarray],
    strikes: Union[float, np.ndarray],
    rates: Union[float, np.ndarray],
    vols: Union[float, np.ndarray],
    times: Union[float, np.ndarray],
    option_type: str = "call",
    greeks: bool = False
) -> Union[float, np.ndarray, dict]
```

汎用的なオプション価格計算関数。

**パラメータ:**
- `spots`: 現在価格
- `strikes`: 行使価格
- `rates`: 無リスク金利（年率）
- `vols`: ボラティリティ（年率）
- `times`: 満期までの時間（年）
- `option_type`: "call" または "put"
- `greeks`: Trueの場合、グリークスも計算

**戻り値:**
- `greeks=False`: 価格（float または np.ndarray）
- `greeks=True`: 価格とグリークスを含む辞書

**例:**
```python
# 単一計算
price = qf.calculate(100, 105, 0.05, 0.2, 1.0)

# グリークス付き
result = qf.calculate(100, 105, 0.05, 0.2, 1.0, greeks=True)
print(result['price'], result['delta'])
```

## Black-Scholesモデル

### `black_scholes_call()`

```python
quantforge.black_scholes_call(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray]
) -> Union[float, np.ndarray]
```

ヨーロピアンコールオプションのBlack-Scholes価格。

**数式:**
$$C = S_0 \cdot N(d_1) - K \cdot e^{-rT} \cdot N(d_2)$$

where:
- $d_1 = \frac{\ln(S_0/K) + (r + \sigma^2/2)T}{\sigma\sqrt{T}}$
- $d_2 = d_1 - \sigma\sqrt{T}$

### `black_scholes_put()`

```python
quantforge.black_scholes_put(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray]
) -> Union[float, np.ndarray]
```

ヨーロピアンプットオプションのBlack-Scholes価格。

**数式:**
$$P = K \cdot e^{-rT} \cdot N(-d_2) - S_0 \cdot N(-d_1)$$

## 配当付きオプション

### `black_scholes_call_dividend()`

```python
quantforge.black_scholes_call_dividend(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    dividend: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray]
) -> Union[float, np.ndarray]
```

連続配当利回り付きコールオプション。

**パラメータ:**
- `dividend`: 連続配当利回り（年率）

## アメリカンオプション

### `american_call()`

```python
quantforge.american_call(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray],
    dividend: Union[float, np.ndarray] = 0.0
) -> Union[float, np.ndarray]
```

Bjerksund-Stensland 2002近似によるアメリカンコール。

**特徴:**
- 早期行使プレミアムを考慮
- 高精度近似（誤差 < 0.1%）
- 配当付きでも高速計算

### `american_put()`

```python
quantforge.american_put(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray],
    dividend: Union[float, np.ndarray] = 0.0
) -> Union[float, np.ndarray]
```

アメリカンプットオプション価格。

### `american_exercise_boundary()`

```python
quantforge.american_exercise_boundary(
    strike: float,
    rate: float,
    vol: float,
    time: float,
    option_type: str = "put"
) -> float
```

アメリカンオプションの早期行使境界価格。

## アジアンオプション

### `asian_arithmetic_call()`

```python
quantforge.asian_arithmetic_call(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray],
    averaging_start: Union[float, np.ndarray] = 0.0,
    n_fixings: int = 252
) -> Union[float, np.ndarray]
```

算術平均アジアンコールオプション。

**パラメータ:**
- `averaging_start`: 平均計算開始時点
- `n_fixings`: 価格観測回数

### `asian_geometric_call()`

```python
quantforge.asian_geometric_call(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray]
) -> Union[float, np.ndarray]
```

幾何平均アジアンコール（解析解）。

## スプレッドオプション

### `spread_option_kirk()`

```python
quantforge.spread_option_kirk(
    spot1: Union[float, np.ndarray],
    spot2: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol1: Union[float, np.ndarray],
    vol2: Union[float, np.ndarray],
    correlation: Union[float, np.ndarray],
    time: Union[float, np.ndarray]
) -> Union[float, np.ndarray]
```

Kirk近似による2資産スプレッドオプション。

**パラメータ:**
- `spot1`, `spot2`: 各資産の現在価格
- `vol1`, `vol2`: 各資産のボラティリティ
- `correlation`: 資産間の相関係数

## バリアオプション

### `barrier_call()`

```python
quantforge.barrier_call(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    barrier: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray],
    barrier_type: str,
    rebate: Union[float, np.ndarray] = 0.0
) -> Union[float, np.ndarray]
```

バリアコールオプション。

**barrier_type:**
- `"up_and_out"`: アップアンドアウト
- `"up_and_in"`: アップアンドイン
- `"down_and_out"`: ダウンアンドアウト
- `"down_and_in"`: ダウンアンドイン

## デジタルオプション

### `digital_call()`

```python
quantforge.digital_call(
    spot: Union[float, np.ndarray],
    strike: Union[float, np.ndarray],
    rate: Union[float, np.ndarray],
    vol: Union[float, np.ndarray],
    time: Union[float, np.ndarray],
    cash_amount: Union[float, np.ndarray] = 1.0
) -> Union[float, np.ndarray]
```

キャッシュオアナッシング・デジタルコール。

**パラメータ:**
- `cash_amount`: ITM時の支払額

## インプレース計算

### `calculate_inplace()`

```python
quantforge.calculate_inplace(
    spots: np.ndarray,
    strikes: Union[float, np.ndarray],
    rates: Union[float, np.ndarray],
    vols: Union[float, np.ndarray],
    times: Union[float, np.ndarray],
    out: np.ndarray,
    option_type: str = "call"
) -> None
```

結果を既存配列に直接書き込む（メモリ効率的）。

**パラメータ:**
- `out`: 結果を書き込む配列（事前確保必要）

**例:**
```python
n = 1_000_000
spots = np.random.uniform(90, 110, n)
results = np.empty(n)
qf.calculate_inplace(spots, 100, 0.05, 0.2, 1.0, out=results)
```

## パフォーマンス指標

| 関数 | 単一計算 | 100万件バッチ |
|------|----------|--------------|
| `black_scholes_call` | < 10ns | < 15ms |
| `american_call` | < 50ns | < 50ms |
| `asian_arithmetic_call` | < 100ns | < 100ms |
| `spread_option_kirk` | < 150ns | < 150ms |

## エラー処理

すべての価格計算関数は以下のエラーをスローする可能性があります：

- `InvalidInputError`: 無効な入力パラメータ
- `ConvergenceError`: 数値計算の収束失敗
- `MemoryError`: メモリ不足

```python
try:
    price = qf.black_scholes_call(-100, 100, 0.05, 0.2, 1.0)
except qf.InvalidInputError as e:
    print(f"Invalid input: {e}")
```
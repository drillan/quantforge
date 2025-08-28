# バッチ処理 API

## 概要

QuantForgeはすべてのオプション価格モデルに対して高性能なバッチ処理機能を提供します。バッチAPIはNumPyスタイルのブロードキャスティングを備えた完全な配列入力をサポートし、大規模なポートフォリオと市場データの効率的な処理を可能にします。

## 主要機能

- **完全な配列サポート**: すべてのパラメータが配列を受け入れ、単一パラメータの変化だけでなく対応
- **ブロードキャスティング**: スカラー値と長さ1の配列の自動拡張
- **ゼロコピーパフォーマンス**: 中間変換なしの直接NumPy配列処理
- **並列実行**: Rayonを使用した大規模データセットの自動並列化
- **一貫したAPI**: すべてのモデルで統一されたインターフェース

## ブロードキャスティングルール

バッチAPIはNumPyスタイルのブロードキャスティングルールに従います：

1. **スカラー値**は出力サイズに合わせて自動的に拡張される
2. **長さ1の配列**は必要な長さに拡張される
3. **異なる長さの配列**（長さ1を除く）はエラーを発生させる
4. **出力サイズ**は最大入力配列長によって決定される

### 例

```python
import numpy as np
from quantforge.models import black_scholes

# スカラーと配列の混合入力
prices = black_scholes.call_price_batch(
    spots=np.array([95, 100, 105]),  # 3つのスポット価格の配列
    strikes=100.0,                    # スカラー、[100, 100, 100]に拡張
    times=1.0,                        # スカラー、[1.0, 1.0, 1.0]に拡張
    rates=0.05,                       # スカラー、[0.05, 0.05, 0.05]に拡張
    sigmas=np.array([0.2, 0.25, 0.3]) # 3つのボラティリティの配列
)
# 結果: 3つの価格の配列
```

## APIリファレンス

### Black-Scholesモデル

#### call_price_batch

複数の入力に対するコールオプション価格を計算。

```python
call_price_batch(spots, strikes, times, rates, sigmas) -> np.ndarray
```

**パラメータ:**
- `spots`: スポット価格（スカラーまたは配列）
- `strikes`: 権利行使価格（スカラーまたは配列）
- `times`: 満期までの時間（年）（スカラーまたは配列）
- `rates`: 無リスク金利（スカラーまたは配列）
- `sigmas`: ボラティリティ（スカラーまたは配列）

**戻り値:**
- コールオプション価格のNumPy配列

#### put_price_batch

複数の入力に対するプットオプション価格を計算。

```python
put_price_batch(spots, strikes, times, rates, sigmas) -> np.ndarray
```

**パラメータ:**
- `call_price_batch`と同じ

**戻り値:**
- プットオプション価格のNumPy配列

#### implied_volatility_batch

市場価格からインプライドボラティリティを計算。

```python
implied_volatility_batch(prices, spots, strikes, times, rates, is_calls) -> np.ndarray
```

**パラメータ:**
- `prices`: 市場価格（スカラーまたは配列）
- `spots`: スポット価格（スカラーまたは配列）
- `strikes`: 権利行使価格（スカラーまたは配列）
- `times`: 満期までの時間（年）（スカラーまたは配列）
- `rates`: 無リスク金利（スカラーまたは配列）
- `is_calls`: オプションタイプ - Trueでコール、Falseでプット（スカラーまたは配列）

**戻り値:**
- インプライドボラティリティのNumPy配列

#### greeks_batch

複数の入力に対するすべてのグリークスを計算。

```python
greeks_batch(spots, strikes, times, rates, sigmas, is_calls) -> Dict[str, np.ndarray]
```

**パラメータ:**
- `spots`: スポット価格（スカラーまたは配列）
- `strikes`: 権利行使価格（スカラーまたは配列）
- `times`: 満期までの時間（年）（スカラーまたは配列）
- `rates`: 無リスク金利（スカラーまたは配列）
- `sigmas`: ボラティリティ（スカラーまたは配列）
- `is_calls`: オプションタイプ（スカラーまたは配列）

**戻り値:**
- キー: 'delta', 'gamma', 'vega', 'theta', 'rho'を持つ辞書
- 各値は対応するグリークスのNumPy配列

### Black76モデル

#### call_price_batch

先物/フォワードに対するコールオプション価格を計算。

```python
call_price_batch(forwards, strikes, times, rates, sigmas) -> np.ndarray
```

**パラメータ:**
- `forwards`: フォワード/先物価格（スカラーまたは配列）
- `strikes`: 権利行使価格（スカラーまたは配列）
- `times`: 満期までの時間（年）（スカラーまたは配列）
- `rates`: 無リスク金利（スカラーまたは配列）
- `sigmas`: ボラティリティ（スカラーまたは配列）

**戻り値:**
- コールオプション価格のNumPy配列

#### put_price_batch

先物/フォワードに対するプットオプション価格を計算。

```python
put_price_batch(forwards, strikes, times, rates, sigmas) -> np.ndarray
```

#### implied_volatility_batch

```python
implied_volatility_batch(prices, forwards, strikes, times, rates, is_calls) -> np.ndarray
```

#### greeks_batch

```python
greeks_batch(forwards, strikes, times, rates, sigmas, is_calls) -> Dict[str, np.ndarray]
```

### Mertonモデル（配当調整）

#### call_price_batch

連続配当利回りを持つコールオプション価格を計算。

```python
call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

**パラメータ:**
- `spots`: スポット価格（スカラーまたは配列）
- `strikes`: 権利行使価格（スカラーまたは配列）
- `times`: 満期までの時間（年）（スカラーまたは配列）
- `rates`: 無リスク金利（スカラーまたは配列）
- `dividend_yields`: 連続配当利回り（スカラーまたは配列）
- `sigmas`: ボラティリティ（スカラーまたは配列）

**戻り値:**
- コールオプション価格のNumPy配列

#### put_price_batch

```python
put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

#### implied_volatility_batch

```python
implied_volatility_batch(prices, spots, strikes, times, rates, dividend_yields, is_calls) -> np.ndarray
```

#### greeks_batch

```python
greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls) -> Dict[str, np.ndarray]
```

**戻り値:**
- キー: 'delta', 'gamma', 'vega', 'theta', 'rho', 'dividend_rho'を持つ辞書

### アメリカンモデル

#### call_price_batch

Barone-Adesi-Whaley近似を使用したアメリカンコールオプション価格を計算。

```python
call_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

#### put_price_batch

```python
put_price_batch(spots, strikes, times, rates, dividend_yields, sigmas) -> np.ndarray
```

#### implied_volatility_batch

```python
implied_volatility_batch(prices, spots, strikes, times, rates, dividend_yields, is_calls) -> np.ndarray
```

#### greeks_batch

```python
greeks_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls) -> Dict[str, np.ndarray]
```

**戻り値:**
- キー: 'delta', 'gamma', 'vega', 'theta', 'rho', 'dividend_rho'を持つ辞書
- 各値は対応するグリークスのNumPy配列

#### exercise_boundary_batch

アメリカンオプションの最適行使境界を計算。

```python
exercise_boundary_batch(spots, strikes, times, rates, dividend_yields, sigmas, is_calls) -> np.ndarray
```

**戻り値:**
- 最適行使価格のNumPy配列

## 使用例

### ポートフォリオ評価

```python
import numpy as np
from quantforge.models import black_scholes

# 1000個の異なるオプションのポートフォリオ
n = 1000
spots = np.random.uniform(90, 110, n)
strikes = np.random.uniform(95, 105, n)
times = np.random.uniform(0.1, 2.0, n)
sigmas = np.random.uniform(0.15, 0.35, n)
rate = 0.05  # すべてに同じ金利

# すべての価格を一度に計算
prices = black_scholes.call_price_batch(spots, strikes, times, rate, sigmas)
```

### リスク管理のためのグリークス

```python
# ポートフォリオのすべてのグリークスを計算
greeks = black_scholes.greeks_batch(spots, strikes, times, rate, sigmas, is_calls=True)

# 個々のグリークスを配列として抽出
portfolio_delta = greeks['delta'].sum()
portfolio_vega = greeks['vega'].sum()
portfolio_gamma = greeks['gamma'].sum()
```

### インプライドボラティリティサーフェス

```python
# 市場価格からボラティリティサーフェスを作成
spots = 100.0  # 現在のスポット
strikes = np.linspace(80, 120, 41)
times = np.array([0.25, 0.5, 1.0, 2.0])

# グリッドを作成
K, T = np.meshgrid(strikes, times)
strikes_flat = K.flatten()
times_flat = T.flatten()

# 市場価格（例）
market_prices = np.random.uniform(5, 25, len(strikes_flat))

# インプライドボラティリティを計算
ivs = black_scholes.implied_volatility_batch(
    prices=market_prices,
    spots=spots,
    strikes=strikes_flat,
    times=times_flat,
    rates=0.05,
    is_calls=True
)

# サーフェスプロット用に再形成
iv_surface = ivs.reshape(K.shape)
```

### 感応度分析

```python
# スポット価格変化に対するオプション感応度を分析
base_spot = 100.0
spot_range = np.linspace(80, 120, 100)

prices = black_scholes.call_price_batch(
    spots=spot_range,
    strikes=100.0,      # 固定ストライク
    times=1.0,          # 固定満期
    rates=0.05,         # 固定金利
    sigmas=0.2          # 固定ボラティリティ
)

# 価格感応度曲線
import matplotlib.pyplot as plt
plt.plot(spot_range, prices)
plt.xlabel('スポット価格')
plt.ylabel('オプション価格')
plt.title('コールオプション価格感応度')
```

## パフォーマンスに関する考慮事項

### 自動最適化

バッチAPIは入力サイズに基づいて自動的に最適化します：

- **小規模バッチ (< 1,000)**: 直接逐次処理
- **中規模バッチ (1,000 - 10,000)**: ベクトル化演算
- **大規模バッチ (10,000 - 100,000)**: チャンク処理
- **超大規模バッチ (> 100,000)**: Rayonによる並列処理

### メモリ効率

- 入力配列はコピーなしで直接アクセスされる（ゼロコピー）
- 出力配列は効率のために事前割り当てされる
- ブロードキャスティングは中間配列を作成しない

### ベストプラクティス

1. **可能な限り配列を使用**: 均一なパラメータでも、配列はスカラーのブロードキャスティングより効率的な場合がある
2. **出力配列を事前割り当て**: 繰り返し計算では出力配列を再利用
3. **類似計算をバッチ化**: 似たパラメータを持つ計算をグループ化
4. **メモリ使用量を監視**: 非常に大きなバッチはメモリ制約システムではチャンキングが必要な場合がある

## エラーハンドリング

### ブロードキャスティングエラー

```python
# これはエラーを発生させる - 互換性のない配列長
try:
    prices = black_scholes.call_price_batch(
        spots=np.array([100, 101, 102]),  # 長さ3
        strikes=np.array([95, 100]),      # 長さ2 - エラー！
        times=1.0,
        rates=0.05,
        sigmas=0.2
    )
except ValueError as e:
    print(f"ブロードキャスティングエラー: {e}")
```

### 数値エラー

```python
# インプライドボラティリティは無効な入力に対してNaNを返す可能性がある
ivs = black_scholes.implied_volatility_batch(
    prices=np.array([0.01, 50.0, -1.0]),  # 無効な負の価格
    spots=100.0,
    strikes=100.0,
    times=1.0,
    rates=0.05,
    is_calls=True
)
# 負の価格のためivs[2]はNaNになる
```

## 移行ガイド

### 単一パラメータ変化から

旧API（単一パラメータ変化）:
```python
# 旧 - spotsのみが配列可能
prices = black_scholes.call_price_batch(
    spots=[95, 100, 105],  # 配列
    k=100.0,                # スカラーのみ
    t=1.0,                  # スカラーのみ
    r=0.05,                 # スカラーのみ
    sigma=0.2               # スカラーのみ
)
```

新API（完全配列サポート）:
```python
# 新 - すべてのパラメータが配列可能
prices = black_scholes.call_price_batch(
    spots=[95, 100, 105],   # 配列
    strikes=100.0,          # スカラーまたは配列
    times=1.0,              # スカラーまたは配列
    rates=0.05,             # スカラーまたは配列
    sigmas=0.2              # スカラーまたは配列
)
```

### List[PyGreeks]からDictへ

旧API:
```python
# 旧 - Greekオブジェクトのリストを返す
greeks_list = black_scholes.greeks_batch(...)
for greek in greeks_list:
    print(greek.delta, greek.gamma)
```

新API:
```python
# 新 - 配列の辞書を返す
greeks_dict = black_scholes.greeks_batch(...)
print(greeks_dict['delta'])  # すべてのデルタのNumPy配列
print(greeks_dict['gamma'])  # すべてのガンマのNumPy配列
```

## 関連情報

- [Black-Scholesモデル](black_scholes.md)
- [Black76モデル](black76.md)
- [Mertonモデル](merton.md)
- [アメリカンオプション](american.md)
- [パフォーマンス最適化](../../performance/optimization.md)
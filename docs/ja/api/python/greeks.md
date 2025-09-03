# グリークス API リファレンス

## 概要

グリークスはオプション価格が様々な要因に対してどのように変化するかを表す金融リスク指標です。QuantForgeはすべてのオプション価格モデルに対して統一された高性能なグリークス計算を提供します。

## 戻り値形式の仕様

QuantForgeのすべてのグリークス関数は、一貫性と使いやすさのために統一された戻り値形式に従います：

### 単一オプションのグリークス

単一オプション計算の場合、グリークスは以下の構造を持つ `dict` として返されます：

```python
{
    'delta': float,    # スポット価格に対するオプション価格の変化率
    'gamma': float,    # スポット価格に対するデルタの変化率
    'theta': float,    # 時間に対するオプション価格の変化率
    'vega': float,     # ボラティリティに対するオプション価格の変化率
    'rho': float       # 金利に対するオプション価格の変化率
}
```

### バッチグリークス計算

バッチ計算の場合、グリークスは `Dict[str, arro3.core.Array]` として返され、各グリークスはArrow配列になります：

```python
{
    'delta': arro3.core.Array,    # デルタ値の配列
    'gamma': arro3.core.Array,    # ガンマ値の配列
    'theta': arro3.core.Array,    # シータ値の配列
    'vega': arro3.core.Array,     # ベガ値の配列
    'rho': arro3.core.Array       # ロー値の配列
}
```

この形式はすべてのモデルで一貫しています：
- Black-Scholes (`quantforge.black_scholes_greeks_batch`)
- Black76 (`quantforge.black76_greeks_batch`)
- Merton Jump Diffusion (`quantforge.merton_greeks_batch`)
- アメリカンオプション (`quantforge.american_greeks_batch`)

## メモリ効率

バッチ形式は最適なメモリ効率のためにArrow配列を使用します：

```{code-block} python
:name: greeks-code-structure-of-arrays-soa
:caption: Structure of Arrays (SoA) - メモリ効率的

# Structure of Arrays (SoA) - メモリ効率的
greeks_dict = {
    'delta': pa.array([0.5, 0.6, 0.7]),    # 連続メモリ
    'gamma': pa.array([0.02, 0.03, 0.04]),
    # ... その他のグリークス
}

# これはArray of Structures (AoS)より効率的：
# greeks_list = [
#     {'delta': 0.5, 'gamma': 0.02, ...},  # 分散メモリ
#     {'delta': 0.6, 'gamma': 0.03, ...},
#     {'delta': 0.7, 'gamma': 0.04, ...},
# ]
```

## 使用例

### 単一オプションのグリークス

```{code-block} python
:name: greeks-code-single-option-example
:caption: 単一オプションのグリークス計算
:linenos:

import quantforge as qf

# Black-Scholesモデル
greeks = qf.black_scholes_greeks(
    s=100.0,      # スポット価格
    k=110.0,      # 権利行使価格
    t=0.25,       # 満期までの時間
    r=0.05,       # 無リスク金利
    sigma=0.2,    # ボラティリティ
    is_call=True  # コールオプション
)

print(f"Delta: {greeks['delta']:.4f}")
print(f"Gamma: {greeks['gamma']:.4f}")
print(f"Theta: {greeks['theta']:.4f}")
print(f"Vega: {greeks['vega']:.4f}")
print(f"Rho: {greeks['rho']:.4f}")
```

### バッチグリークス計算

```{code-block} python
:name: greeks-code-batch-calculation-example
:caption: バッチグリークス計算
:linenos:

import pyarrow as pa
import numpy as np  # 乱数生成用
import quantforge as qf

# バッチ入力の準備 - PyArrowを使用（推奨）
n = 1000
spots = pa.array(np.random.uniform(90, 110, n))
strikes = pa.array([100.0] * n)
times = pa.array(np.random.uniform(0.1, 2.0, n))
rates = pa.array([0.05] * n)
volatilities = pa.array(np.random.uniform(0.15, 0.35, n))
is_calls = pa.array([True] * n)

# すべてのオプションのグリークスを一度に計算
greeks_batch = qf.black_scholes_greeks_batch(
    s=spots,
    k=strikes,
    t=times,
    r=rates,
    sigma=volatilities,
    is_call=is_calls
)

# 個々のグリークス配列へのアクセス
deltas = greeks_batch['delta']  # 形状 (n,) のarro3.core.Array
gammas = greeks_batch['gamma']  # 形状 (n,) のarro3.core.Array

# 統計分析（必要に応じてNumPyに変換）
deltas_np = np.array(deltas)
gammas_np = np.array(gammas)
print(f"平均デルタ: {np.mean(deltas_np):.4f}")
print(f"最大ガンマ: {np.max(gammas_np):.4f}")
```

### アメリカンオプションのグリークス

アメリカンオプションも同じ統一形式に従います：

```{code-block} python
:name: greeks-code-american-option-example
:caption: アメリカンオプションのグリークス
:linenos:

import quantforge as qf
import numpy as np

# 単一アメリカンオプションのグリークス
greeks = qf.american_greeks(
    s=100.0,
    k=110.0,
    t=0.25,
    r=0.05,
    sigma=0.2,
    is_call=True,
    steps=100  # 二項ツリーのステップ数
)

# バッチアメリカングリークス（統一形式）
n = 100
greeks_batch = qf.american_greeks_batch(
    s=np.random.uniform(90, 110, n),
    k=np.full(n, 100.0),
    t=np.random.uniform(0.1, 1.0, n),
    r=np.full(n, 0.05),
    sigma=np.random.uniform(0.15, 0.35, n),
    is_call=np.ones(n, dtype=bool),
    steps=100
)

# Dict[str, arro3.core.Array]を返す - 他のモデルと同じ
print(f"デルタ範囲: [{greeks_batch['delta'].min():.4f}, {greeks_batch['delta'].max():.4f}]")
```

## モデル固有の注記

### Black-Scholesグリークス

Black-Scholes仮定下でのヨーロピアンオプションの標準的なグリークス。

### Black76グリークス

先物オプションのグリークス。スポット価格 `s` はフォワード/先物価格を表します。

### Merton Jump Diffusionグリークス

ジャンプリスクを考慮したグリークス：

```{code-block} python
:name: greeks-code-merton-greeks-example
:caption: Merton Jump Diffusionグリークス
:linenos:

greeks = qf.merton_greeks(
    s=100.0,
    k=110.0,
    t=0.25,
    r=0.05,
    sigma=0.2,
    lambda_=0.1,  # ジャンプ強度
    mu_j=-0.05,   # 平均ジャンプサイズ
    sigma_j=0.1,  # ジャンプボラティリティ
    is_call=True
)
```

### アメリカンオプショングリークス

二項ツリー法を使用して計算。`steps`パラメータが精度を制御します：
- ステップ数が多い = 高精度だが計算が遅い
- デフォルト: 100ステップ（バランスが良い）
- 高精度の場合: 200-500ステップ
- 概算の場合: 50ステップ

## パフォーマンスに関する考慮事項

1. **バッチ処理**: 複数のオプションを計算する場合は常にバッチ関数を優先
2. **メモリレイアウト**: Arrow配列を持つDict形式は最適なキャッシュ局所性を提供
3. **並列化**: バッチ関数は大規模入力に対して自動的に並列処理を使用
4. **型の一貫性**: すべてのバッチ関数は同じDict[str, arro3.core.Array]形式を返す

## エラーハンドリング

すべてのグリークス関数は入力を検証し、適切なエラーを発生させます：

```{code-block} python
:name: greeks-code-error-handling-example
:caption: エラーハンドリングの例
:linenos:

try:
    greeks = qf.black_scholes_greeks(
        s=-100.0,  # 無効: 負のスポット
        k=110.0,
        t=0.25,
        r=0.05,
        sigma=0.2,
        is_call=True
    )
except ValueError as e:
    print(f"エラー: {e}")  # "s must be positive"
```

## 関連情報

- [価格計算関数](pricing.md) - オプション価格計算
- [インプライドボラティリティ](implied_vol.md) - IV計算
- [バッチ処理](batch_processing.md) - 効率的な一括計算
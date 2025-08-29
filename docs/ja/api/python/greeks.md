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

バッチ計算の場合、グリークスは `Dict[str, np.ndarray]` として返され、各グリークスはNumPy配列になります：

```python
{
    'delta': np.ndarray,    # デルタ値の配列
    'gamma': np.ndarray,    # ガンマ値の配列
    'theta': np.ndarray,    # シータ値の配列
    'vega': np.ndarray,     # ベガ値の配列
    'rho': np.ndarray       # ロー値の配列
}
```

この形式はすべてのモデルで一貫しています：
- Black-Scholes (`quantforge.black_scholes_greeks_batch`)
- Black76 (`quantforge.black76_greeks_batch`)
- Merton Jump Diffusion (`quantforge.merton_greeks_batch`)
- アメリカンオプション (`quantforge.american_greeks_batch`)

## メモリ効率

バッチ形式は最適なメモリ効率のためにNumPy配列を使用します：

```{code-block} python
:name: greeks-code-structure-of-arrays-soa
:caption: Structure of Arrays (SoA) - メモリ効率的

# Structure of Arrays (SoA) - メモリ効率的
greeks_dict = {
    'delta': np.array([0.5, 0.6, 0.7]),    # 連続メモリ
    'gamma': np.array([0.02, 0.03, 0.04]),
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

```python
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

```python
import numpy as np
import quantforge as qf

# バッチ入力の準備
n = 1000
spots = np.random.uniform(90, 110, n)
strikes = np.full(n, 100.0)
times = np.random.uniform(0.1, 2.0, n)
rates = np.full(n, 0.05)
volatilities = np.random.uniform(0.15, 0.35, n)
is_calls = np.ones(n, dtype=bool)

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
deltas = greeks_batch['delta']  # 形状 (n,) のnp.ndarray
gammas = greeks_batch['gamma']  # 形状 (n,) のnp.ndarray

# 統計分析
print(f"平均デルタ: {np.mean(deltas):.4f}")
print(f"最大ガンマ: {np.max(gammas):.4f}")
```

### アメリカンオプションのグリークス

アメリカンオプションも同じ統一形式に従います：

```python
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

# Dict[str, np.ndarray]を返す - 他のモデルと同じ
print(f"デルタ範囲: [{greeks_batch['delta'].min():.4f}, {greeks_batch['delta'].max():.4f}]")
```

## モデル固有の注記

### Black-Scholesグリークス

Black-Scholes仮定下でのヨーロピアンオプションの標準的なグリークス。

### Black76グリークス

先物オプションのグリークス。スポット価格 `s` はフォワード/先物価格を表します。

### Merton Jump Diffusionグリークス

ジャンプリスクを考慮したグリークス：
```python
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
2. **メモリレイアウト**: NumPy配列を持つDict形式は最適なキャッシュ局所性を提供
3. **並列化**: バッチ関数は大規模入力に対して自動的に並列処理を使用
4. **型の一貫性**: すべてのバッチ関数は同じDict[str, np.ndarray]形式を返す

## エラーハンドリング

すべてのグリークス関数は入力を検証し、適切なエラーを発生させます：

```python
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
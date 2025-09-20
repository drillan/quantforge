(market-utils)=
# Market Utils API

市場データ処理ユーティリティ：ビッド・アスク価格からの中値計算、スプレッド分析、異常値処理

(market-utils-overview)=
## 概要

`quantforge.market_utils`モジュールは、市場データからの価格計算機能を提供します：

- **中値計算**: 単純中値とボリューム加重中値
- **スプレッド分析**: 絶対スプレッドとパーセンテージスプレッド
- **異常値処理**: オプション市場の極端なスプレッドの処理
- **バッチ処理**: 大規模データのArrow配列による高速処理

(market-utils-imports)=
## インポート

```{code-block} python
:name: market-utils-code-imports
:caption: モジュールインポート

from quantforge.market_utils import (
    # 単一値計算
    mid_price,
    mid_price_with_config,
    weighted_mid_price,
    weighted_mid_price_with_config,
    spread,
    spread_pct,

    # バッチ処理
    mid_price_batch,
    mid_price_batch_with_config,
    mid_price_batch_with_metrics,
    weighted_mid_price_batch,
    weighted_mid_price_batch_with_config,
    spread_batch,
    spread_pct_batch,

    # 設定
    PricingConfig
)
```

(market-utils-single-value)=
## 単一値計算

(market-utils-mid-price)=
### mid_price

ビッドとアスクから単純中値を計算します。

```{code-block} python
:name: market-utils-code-mid-price
:caption: mid_price関数シグネチャ

def mid_price(bid: float, ask: float) -> float:
    """
    単純中値の計算

    Parameters
    ----------
    bid : float
        ビッド価格
    ask : float
        アスク価格

    Returns
    -------
    float
        中値価格。異常な場合はNaN

    Notes
    -----
    - デフォルトで50%を超えるスプレッドはNaNを返す
    - クロススプレッド（bid > ask）はNaNを返す
    - 負の価格はNaNを返す
    """
```

**使用例**:

```{code-block} python
:name: market-utils-code-mid-price-example
:caption: mid_price使用例

import math
from quantforge.market_utils import mid_price

# 通常のスプレッド
price = mid_price(100.0, 100.2)
assert price == 100.1

# 極端なスプレッド（オプション市場でよくある）
price = mid_price(1.0, 1000.0)
assert math.isnan(price)  # デフォルトで50%超はNaN

# クロススプレッド
price = mid_price(105.0, 100.0)
assert math.isnan(price)
```

(market-utils-mid-price-with-config)=
### mid_price_with_config

カスタム設定で中値を計算します。

```{code-block} python
:name: market-utils-code-mid-price-with-config
:caption: mid_price_with_config関数シグネチャ

def mid_price_with_config(
    bid: float,
    ask: float,
    config: PricingConfig
) -> float:
    """
    設定可能な中値計算

    Parameters
    ----------
    bid : float
        ビッド価格
    ask : float
        アスク価格
    config : PricingConfig
        価格計算設定

    Returns
    -------
    float
        中値価格。異常な場合の処理は設定に依存
    """
```

**使用例**:

```{code-block} python
:name: market-utils-code-mid-price-with-config-example
:caption: mid_price_with_config使用例

from quantforge.market_utils import mid_price_with_config, PricingConfig

# 極端なスプレッドを許可
config = PricingConfig.with_config(max_spread_pct=None)
price = mid_price_with_config(1.0, 1000.0, config)
assert price == 500.5  # NaNではなく中値を返す

# 厳格なスプレッド制限
config = PricingConfig.with_config(max_spread_pct=0.01)  # 1%制限
price = mid_price_with_config(100.0, 102.0, config)
assert math.isnan(price)  # 2%スプレッドなのでNaN
```

(market-utils-weighted-mid-price)=
### weighted_mid_price

数量加重中値を計算します。

```{code-block} python
:name: market-utils-code-weighted-mid-price
:caption: weighted_mid_price関数シグネチャ

def weighted_mid_price(
    bid: float,
    ask: float,
    bid_qty: Optional[float] = None,
    ask_qty: Optional[float] = None
) -> float:
    """
    数量加重中値の計算

    Parameters
    ----------
    bid : float
        ビッド価格
    ask : float
        アスク価格
    bid_qty : float, optional
        ビッド数量。Noneの場合は単純中値
    ask_qty : float, optional
        アスク数量。Noneの場合は単純中値

    Returns
    -------
    float
        加重中値価格

    Notes
    -----
    - (bid * ask_qty + ask * bid_qty) / (bid_qty + ask_qty)
    - 数量が等しい場合は単純中値と同じ
    - 片方または両方の数量が0またはNoneの場合は単純中値
    """
```

**使用例**:

```{code-block} python
:name: market-utils-code-weighted-mid-price-example
:caption: weighted_mid_price使用例

from quantforge.market_utils import weighted_mid_price

# ビッド側が厚い市場
price = weighted_mid_price(100.0, 100.2, bid_qty=2000.0, ask_qty=1000.0)
# (100.0 * 1000.0 + 100.2 * 2000.0) / 3000.0 ≈ 100.133

# 数量なし（単純中値にフォールバック）
price = weighted_mid_price(100.0, 100.2)
assert price == 100.1
```

(market-utils-spread)=
### spread / spread_pct

スプレッドとスプレッドパーセンテージを計算します。

```{code-block} python
:name: market-utils-code-spread
:caption: spread/spread_pct関数シグネチャ

def spread(bid: float, ask: float) -> float:
    """絶対スプレッド（ask - bid）を計算"""

def spread_pct(bid: float, ask: float) -> float:
    """スプレッドパーセンテージを計算

    Returns
    -------
    float
        (ask - bid) / mid_price
        クロススプレッドの場合はNaN
    """
```

(market-utils-batch)=
## バッチ処理

(market-utils-mid-price-batch)=
### mid_price_batch

複数の価格ペアの中値を一括計算します。

```{code-block} python
:name: market-utils-code-mid-price-batch
:caption: mid_price_batch関数シグネチャ

def mid_price_batch(
    bids: np.ndarray,
    asks: np.ndarray
) -> np.ndarray:
    """
    バッチ中値計算（Arrow配列による高速処理）

    Parameters
    ----------
    bids : np.ndarray
        ビッド価格配列（スカラーも可能）
    asks : np.ndarray
        アスク価格配列（スカラーも可能）

    Returns
    -------
    np.ndarray
        中値価格配列

    Notes
    -----
    - 10,000要素以上で自動並列処理
    - ブロードキャスティング対応
    - Arrow配列によるゼロコピー処理
    """
```

**使用例**:

```{code-block} python
:name: market-utils-code-mid-price-batch-example
:caption: mid_price_batch使用例

import numpy as np
from quantforge.market_utils import mid_price_batch

# 複数価格の一括処理
bids = np.array([100.0, 101.0, 102.0])
asks = np.array([100.2, 101.3, 102.4])
mids = mid_price_batch(bids, asks)
# array([100.1, 101.15, 102.2])

# ブロードキャスティング（スカラー × 配列）
bid = np.array([100.0])  # スカラー
asks = np.array([100.2, 100.3, 100.4])
mids = mid_price_batch(bid, asks)
# array([100.1, 100.15, 100.2])
```

(market-utils-mid-price-batch-with-metrics)=
### mid_price_batch_with_metrics

中値計算と同時に統計情報を収集します。

```{code-block} python
:name: market-utils-code-mid-price-batch-with-metrics
:caption: mid_price_batch_with_metrics関数シグネチャ

def mid_price_batch_with_metrics(
    bids: np.ndarray,
    asks: np.ndarray,
    config: PricingConfig
) -> Tuple[np.ndarray, BatchMetrics]:
    """
    メトリクス付きバッチ処理

    Returns
    -------
    tuple
        (中値配列, BatchMetricsオブジェクト)

    BatchMetrics属性:
        - total_processed: 処理件数
        - nan_count: NaN結果の件数
        - crossed_spreads: クロススプレッド件数
        - abnormal_spreads: 異常スプレッド件数
        - mean_spread_pct: 平均スプレッド率
        - max_spread_pct: 最大スプレッド率
    """
```

**使用例**:

```{code-block} python
:name: market-utils-code-mid-price-batch-with-metrics-example
:caption: mid_price_batch_with_metrics使用例

from quantforge.market_utils import mid_price_batch_with_metrics, PricingConfig

# オプションチェーンの処理
bids = np.array([100.0, 1.0, 105.0, 100.0])
asks = np.array([100.2, 1000.0, 104.0, 100.5])
config = PricingConfig.with_config(max_spread_pct=0.1)  # 10%制限

mids, metrics = mid_price_batch_with_metrics(bids, asks, config)

print(f"処理件数: {metrics.total_processed}")
print(f"異常スプレッド: {metrics.abnormal_spreads}")
print(f"クロススプレッド: {metrics.crossed_spreads}")
print(f"平均スプレッド: {metrics.mean_spread_pct:.2%}")
```

(market-utils-weighted-mid-price-batch)=
### weighted_mid_price_batch

数量加重中値のバッチ計算を行います。

```{code-block} python
:name: market-utils-code-weighted-mid-price-batch
:caption: weighted_mid_price_batch関数シグネチャ

def weighted_mid_price_batch(
    bids: np.ndarray,
    asks: np.ndarray,
    bid_qtys: Optional[np.ndarray] = None,
    ask_qtys: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    数量加重中値のバッチ計算

    Parameters
    ----------
    bids : np.ndarray
        ビッド価格配列
    asks : np.ndarray
        アスク価格配列
    bid_qtys : np.ndarray, optional
        ビッド数量配列
    ask_qtys : np.ndarray, optional
        アスク数量配列

    Notes
    -----
    - 数量が0またはNoneの要素は単純中値を使用
    - ブロードキャスティング対応
    """
```

(market-utils-config)=
## 設定クラス

(market-utils-pricing-config)=
### PricingConfig

価格計算の動作を制御する設定クラスです。

```{code-block} python
:name: market-utils-code-pricing-config
:caption: PricingConfigクラス定義

class PricingConfig:
    """
    価格計算設定

    Attributes
    ----------
    max_spread_pct : float, optional
        最大許容スプレッド率（デフォルト: 0.5 = 50%）
        Noneの場合は制限なし
    abnormal_handling : str
        異常スプレッドの処理方法
        - "return_nan": NaNを返す（デフォルト）
        - "log_and_continue": ログして中値を返す
    crossed_handling : str
        クロススプレッドの処理方法
        - "return_nan": NaNを返す（デフォルト）
        - "swap_and_continue": bid/askを入れ替えて処理
    """

    @staticmethod
    def with_config(
        max_spread_pct: Optional[float] = None,
        abnormal_handling: str = "return_nan",
        crossed_handling: str = "return_nan"
    ) -> PricingConfig:
        """カスタム設定を作成"""
```

**使用例**:

```{code-block} python
:name: market-utils-code-pricing-config-example
:caption: PricingConfig使用例

from quantforge.market_utils import PricingConfig

# デフォルト設定（50%制限）
config = PricingConfig()

# 制限なし（深いOTMオプション用）
config = PricingConfig.with_config(max_spread_pct=None)

# 厳格な制限（流動性の高い市場）
config = PricingConfig.with_config(max_spread_pct=0.001)  # 0.1%

# クロススプレッドを自動修正
config = PricingConfig.with_config(
    crossed_handling="swap_and_continue"
)
```

(market-utils-use-cases)=
## 実世界のユースケース

(market-utils-option-chain-processing)=
### オプションチェーンの処理

```{code-block} python
:name: market-utils-code-option-chain-processing
:caption: オプションチェーンの処理例

import numpy as np
from quantforge.market_utils import (
    mid_price_batch_with_metrics,
    PricingConfig
)

# 日経225オプション（100銘柄）
n = 100
strikes = np.linspace(40000, 50000, n)
atm = 45000

# ATMからの距離でスプレッドが広がる
distance = np.abs(strikes - atm) / atm
spread_pct = 0.002 + distance * 2.0  # 0.2% ~ 200%+

bids = strikes * (1 - spread_pct / 2)
asks = strikes * (1 + spread_pct / 2)

# 10%を超えるスプレッドをフィルタ
config = PricingConfig.with_config(max_spread_pct=0.1)
mids, metrics = mid_price_batch_with_metrics(bids, asks, config)

# 有効な中値のみ抽出
valid_mids = mids[~np.isnan(mids)]
print(f"有効な銘柄: {len(valid_mids)}/{n}")
print(f"平均スプレッド: {metrics.mean_spread_pct:.2%}")
```

(market-utils-high-frequency-stream)=
### 高頻度データストリーム

```{code-block} python
:name: market-utils-code-high-frequency-stream
:caption: 高頻度データストリーム処理例

import numpy as np
from quantforge.market_utils import mid_price_batch

# 1秒間のティックデータ（100更新）
np.random.seed(42)
base_price = 100.0
n = 100

# ランダムウォーク
noise = np.random.randn(n) * 0.01
bids = base_price + np.cumsum(noise) - 0.1
asks = bids + np.random.uniform(0.05, 0.15, n)

# 高速バッチ処理（10,000件以上で並列化）
mids = mid_price_batch(bids, asks)

# 価格変動分析
returns = np.diff(mids) / mids[:-1]
volatility = np.std(returns) * np.sqrt(252 * 86400)  # 年率換算
print(f"ボラティリティ: {volatility:.2%}")
```

(market-utils-volume-analysis)=
### ボリューム分析付き中値計算

```{code-block} python
:name: market-utils-code-volume-analysis
:caption: ボリューム分析付き中値計算例

from quantforge.market_utils import weighted_mid_price_batch

# 板情報付きデータ
bids = np.array([100.0, 99.9, 99.8])
bid_qtys = np.array([100, 200, 500])  # 累積ボリューム
asks = np.array([100.1, 100.2, 100.3])
ask_qtys = np.array([150, 300, 400])

# 各レベルの加重中値
weighted_mids = weighted_mid_price_batch(
    bids, asks, bid_qtys, ask_qtys
)

# 板の偏り分析
imbalance = (bid_qtys - ask_qtys) / (bid_qtys + ask_qtys)
print(f"板の偏り: {imbalance}")
```

(market-utils-performance)=
## パフォーマンス特性

```{list-table} パフォーマンス特性
:name: market-utils-table-performance
:header-rows: 1
:widths: 25 25 25 25

* - データサイズ
  - 処理方式
  - 速度（vs NumPy）
  - メモリ使用
* - 1-1,000
  - シーケンシャル
  - 10倍高速
  - 最小
* - 1,000-10,000
  - マイクロバッチ
  - 2-5倍高速
  - 低
* - 10,000+
  - 並列処理（Rayon）
  - 1-2倍高速
  - 中
* - 100,000+
  - Arrow配列
  - 同等
  - 効率的
```

(market-utils-error-handling)=
## エラー処理

本モジュールはIEEE 754標準に従い、エラーではなくNaNを返します：

```{code-block} python
:name: market-utils-code-error-handling
:caption: エラー処理の例

import math
from quantforge.market_utils import mid_price

# エラーを発生させない
result = mid_price(-100.0, 100.0)  # 負の価格
assert math.isnan(result)  # エラーではなくNaN

result = mid_price(float('inf'), 100.0)  # 無限大
assert math.isnan(result)  # エラーではなくNaN

# 大規模処理でも継続
results = mid_price_batch(
    np.array([100.0, -50.0, 200.0]),  # 不正な値を含む
    np.array([101.0, 100.0, 201.0])
)
# [100.5, NaN, 200.5]  # 処理は継続
```

(market-utils-notes)=
## 注意事項

(market-utils-option-market-usage)=
### オプション市場での使用

深いOTMオプションでは極端なスプレッドが一般的です：

```{code-block} python
:name: market-utils-code-option-market-usage
:caption: オプション市場での使用例

# 悪い例：エラーで処理停止
if ask - bid > bid:
    raise ValueError("Spread too wide")

# 良い例：NaNで継続
config = PricingConfig.with_config(max_spread_pct=0.5)
price = mid_price_with_config(1.0, 1000.0, config)
if math.isnan(price):
    # 別の方法で価格を推定
    pass
```

(market-utils-memory-efficiency)=
### メモリ効率

大規模データではArrow配列のゼロコピー特性を活用：

```{code-block} python
:name: market-utils-code-memory-efficiency
:caption: メモリ効率的な使用例

# 効率的：ビューを使用
mids = mid_price_batch(bids[mask], asks[mask])

# 非効率：コピーを作成
mids = mid_price_batch(bids.copy(), asks.copy())
```

(market-utils-related-items)=
## 関連項目

- [Black-Scholesモデル](black_scholes.md) - オプション価格計算
- [インプライドボラティリティ](implied_vol.md) - 市場価格からのIV逆算
- [バッチ処理](batch_processing.md) - 効率的な大規模処理
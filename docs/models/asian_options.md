# アジアンオプション

平均価格に基づくパス依存型オプションです。

## 概要

アジアンオプションは、満期までの期間中の原資産価格の平均に基づいてペイオフが決定されます。

## 種類

### 算術平均アジアンオプション

最も一般的なタイプ：

$$A_T = \frac{1}{n}\sum_{i=1}^{n} S_{t_i}$$

### 幾何平均アジアンオプション

解析解が存在：

$$G_T = \left(\prod_{i=1}^{n} S_{t_i}\right)^{1/n}$$

## 価格計算

### ボラティリティ調整法

算術平均の近似：

```python
import quantforge as qf

# 算術平均アジアンコール
asian_call = qf.asian_arithmetic_call(
    spot=100,
    strike=100,
    rate=0.05,
    vol=0.2,
    time=1.0,
    n_fixings=252  # 日次観測
)
```

### 幾何平均の解析解

```python
# 幾何平均アジアンコール（正確な値）
geometric_asian = qf.asian_geometric_call(
    spot=100,
    strike=100,
    rate=0.05,
    vol=0.2,
    time=1.0
)
```

## 部分観測アジアン

既に一部の価格が観測されている場合：

```python
# 既観測価格を考慮
observed_prices = [98, 102, 101, 99, 103]
remaining_time = 0.5

adjusted_asian = qf.asian_call_partial(
    spot=103,
    strike=100,
    rate=0.05,
    vol=0.2,
    remaining_time=remaining_time,
    observed_average=np.mean(observed_prices),
    n_observed=len(observed_prices),
    n_total=252
)
```

## 特徴

### 利点
- ボラティリティが低い
- 価格操作に強い
- ヘッジが容易

### 用途
- 商品オプション
- 為替オプション
- エネルギーデリバティブ

## パフォーマンス

- 算術平均: < 100ns/計算
- 幾何平均: < 50ns/計算
- 精度: < 1e-12
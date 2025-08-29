# {ModelName}モデル API

{モデルの主な用途を1文で記述。例：「ヨーロピアンオプションの価格計算のための標準的なモデルです。」}

## 概要

{モデルの特徴を2-3文で簡潔に記述。数式や理論的背景は最小限に。}

## API使用方法

### 基本的な価格計算

```python
from quantforge.models import {module_name}

# コールオプション価格
# パラメータ: {param1}({param1_desc}), {param2}({param2_desc}), ...
call_price = {module_name}.call_price({example_values})

# プットオプション価格
# パラメータ: {同上}
put_price = {module_name}.put_price({example_values})
```

### バッチ処理

```python
import numpy as np

# 完全配列サポート（Broadcasting対応）
{array_name1} = np.array([{example_array_values1}])
{scalar_or_array1} = {scalar_value1}  # スカラーは自動拡張
{array_name2} = np.array([{example_array_values2}])

# パラメータ: {param1_plural}, {param2_plural}, {param3_plural}, {param4_plural}, {param5_plural}
call_prices = {module_name}.call_price_batch({batch_params_all})
put_prices = {module_name}.put_price_batch({batch_params_all})

# Greeksバッチ（辞書形式で返却）
greeks = {module_name}.greeks_batch({batch_params_all}, is_calls=True)
print(greeks['delta'])  # NumPy配列
```

### グリークス計算

```{code-block} python
:name: api-model-template-code-section
:caption: 全グリークスを一括計算

# 全グリークスを一括計算
# パラメータ: {params}, is_call
greeks = {module_name}.greeks({params}, True)

# 個別のグリークスへアクセス
print(f"Delta: {greeks.delta:.4f}")  # {delta_description}
print(f"Gamma: {greeks.gamma:.4f}")  # {gamma_description}
print(f"Vega: {greeks.vega:.4f}")    # ボラティリティ感応度
print(f"Theta: {greeks.theta:.4f}")  # 時間価値減衰
print(f"Rho: {greeks.rho:.4f}")      # 金利感応度
{additional_greeks_if_any}
```

### インプライドボラティリティ

```{code-block} python
:name: api-model-template-code-price-params-iscall
:caption: パラメータ: price, {params}, is_call

# パラメータ: price, {params}, is_call
iv = {module_name}.implied_volatility({iv_params})
print(f"Implied Volatility: {iv:.4f}")
```

## パラメータ説明

### 入力パラメータ

| パラメータ | 型 | 説明 | 有効範囲 |
|-----------|-----|------|----------|
| `{param1}` | float | {param1_full_description} | {param1_range} |
| `{param2}` | float | {param2_full_description} | {param2_range} |
| `{param3}` | float | {param3_full_description} | {param3_range} |
| `{param4}` | float | {param4_full_description} | {param4_range} |
| `{param5}` | float | {param5_full_description} | {param5_range} |
| `sigma` | float | ボラティリティ（年率） | > 0 |
| `is_call` | bool | オプションタイプ | True: コール, False: プット |

### バッチ処理用パラメータ（完全配列API）

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `{param1_plural}` | float \| np.ndarray | {param1_desc}（配列またはスカラー） |
| `{param2_plural}` | float \| np.ndarray | {param2_desc}（配列またはスカラー） |
| `{param3_plural}` | float \| np.ndarray | {param3_desc}（配列またはスカラー） |
| `{param4_plural}` | float \| np.ndarray | {param4_desc}（配列またはスカラー） |
| `{param5_plural}` | float \| np.ndarray | {param5_desc}（配列またはスカラー） |

Broadcasting規則：スカラーは自動的に配列サイズに拡張されます。

## 価格式（参考）

コールオプション:
$${call_formula}$$

プットオプション:
$${put_formula}$$

where:
- ${formula_variables_definitions}

詳細な理論的背景は[{ModelName}モデル理論](../../models/{model_file}.md)を参照してください。

## エラーハンドリング

すべての価格計算関数は以下の条件でエラーを返します：

- {error_condition_1}
- {error_condition_2}
- {error_condition_3}
- 数値がNaNまたは無限大

```python
try:
    # パラメータ: {error_example_params}
    price = {module_name}.call_price({invalid_params})  # {error_description}
except ValueError as e:
    print(f"入力エラー: {e}")
```

## パフォーマンス指標

| 操作 | 単一計算 | 100万件バッチ |
|------|----------|--------------|
| コール/プット価格 | < {single_price}ns | < {batch_price}ms |
| 全グリークス | < {single_greeks}ns | < {batch_greeks}ms |
| インプライドボラティリティ | < {single_iv}ns | < {batch_iv}ms |

## 使用例

### {UseCase1_Title}

```python
from quantforge.models import {module_name}

# {UseCase1_Description}
{usecase1_setup_code}

# 価格計算
call_price = {module_name}.call_price({usecase1_call_params})
put_price = {module_name}.put_price({usecase1_put_params})

print(f"Call Price: ${call_price:.2f}")
print(f"Put Price: ${put_price:.2f}")

# グリークス計算
greeks = {module_name}.greeks({usecase1_greeks_params})
print(f"Delta: {greeks.delta:.4f}")
print(f"Gamma: {greeks.gamma:.4f}")
print(f"Vega: {greeks.vega:.4f}")
```

### {UseCase2_Title}

```python
{usecase2_imports}

# {UseCase2_Description}
{usecase2_setup_code}

# {UseCase2_Main_Calculation}
{usecase2_calculation_code}

# {UseCase2_Output}
{usecase2_output_code}
```

## 関連情報

- [{RelatedModel1}]({related1_link}) - {related1_description}
- [{RelatedModel2}]({related2_link}) - {related2_description}
- [インプライドボラティリティAPI](implied_vol.md) - IV計算の詳細
- [{ModelName}理論的背景](../../models/{model_file}.md) - 数学的詳細
# Python Benchmarks Package Restructure and Remaining Issues

## 実施完了タスク (2025-08-30)

### 1. Python API構造の修正 ✅
- `python/quantforge/__init__.py`を更新
- `black_scholes`, `black76`, `merton`を直接エクスポート
- `from quantforge import black_scholes`が正常動作

### 2. implied_volatility_batch Broadcasting修正 ✅
**問題**: 配列入力時に最初の要素のみ処理していた
**修正内容**:
- `bindings/python/src/models/black_scholes.rs`
- `bindings/python/src/models/black76.rs`
- `bindings/python/src/models/merton.rs`

すべて以下のパターンに修正:
```rust
// 修正前: pricesだけPyReadonlyArray1、他はBroadcastIteratorで処理
prices: PyReadonlyArray1<'py, f64>,
let prices_slice = prices.as_slice()?;
// 最初の要素のみ使用していた

// 修正後: すべてArrayLikeでBroadcastIteratorに含める
prices: ArrayLike<'py>,
let inputs = vec![&prices, &spots, &strikes, &times, &rates, &is_calls];
// 全要素を正しく処理
```

**検証結果**:
```python
prices = np.array([10.45, 11.0, 9.5, 12.0, 8.0])
ivs = black_scholes.implied_volatility_batch(prices, spots, strikes, times, rates, is_calls)
# 結果: [0.19998445 0.21461606 0.17456731 0.24111689 0.13377583]
# すべて異なる値が正しく計算された
```

### 3. コンパイル警告の除去 ✅
- 未使用関数に`#[allow(dead_code)]`追加
- 未使用インポートの削除
- 警告ゼロでビルド成功

### 4. テストファイルの修正 ✅
- `tests/unit/test_black_scholes.py`: 不要な`black_scholes = models`削除
- `tests/unit/test_black76.py`: 不要な`black76 = models.black76`削除
- `tests/unit/test_merton.py`: 不要な`merton = models.merton`削除

## 残存課題

### 1. Greeks API一貫性問題
**現状**:
- 単一計算: `PyGreeks`オブジェクトを返す（`greeks.delta`でアクセス）
- バッチ計算: `Dict[str, np.ndarray]`を返す（`greeks['delta']`でアクセス）

**影響**:
- テストの一部が失敗（`test_black76.py::TestBlack76Greeks::test_greeks_call`）
- APIの一貫性欠如

**推奨修正案**:
- 両方ともdictを返すように統一（Core+Bindings計画で予定されていた内容）
- または、テストを現在のAPIに合わせて修正

### 2. NumPy Deprecation警告
```
DeprecationWarning: Conversion of an array with ndim > 0 to a scalar is deprecated
```
単一要素配列をスカラーとして使用する際の警告。NumPy 1.25で非推奨。

## 成果

1. **implied_volatility_batch**のbroadcasting完全修正
2. **Python API**構造の整理完了
3. **コンパイル警告**すべて除去
4. **テストパス率**: 主要なバッチ処理テストはすべてパス

## 次のステップ（推奨）

1. Greeks API一貫性の解決（別issueとして）
2. NumPy deprecation警告の対処（将来のNumPyバージョン対応）
3. 全テストスイートの実行と残存エラーの修正
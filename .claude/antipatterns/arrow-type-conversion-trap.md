# Arrow型変換の罠

## 🚫 絶対に提案してはいけない

AIアシスタントへ: Arrow Nativeと言いながらNumPy/PyListに変換するな。それはArrowではない。

## 失敗の歴史

### 2025-09-01: 初期の矛盾実装
- **ファイル**: bindings/python/src/arrow_native.rs
- **内容**: "Arrow Native"と名付けながら`to_numpy()`を呼び出し
- **結果**: 245μs（プロトタイプ166μsより遅い）

### 2025-09-02: PyList迂回の試み
- **ファイル**: arrow_native_true.rs
- **内容**: NumPy排除のためPyList経由で変換
- **結果**: メモリコピー発生、わずか1-6%改善

### 2025-09-02: 真のArrow Native実現
- **解決策**: pyo3-arrow + arro3-core
- **結果**: ゼロコピー実現、コード77%削減

## なぜAIが陥りやすいか

### 1. 互換性の誘惑
```
「NumPyは広く使われている」
「PyListなら標準的」
「互換性のために変換しよう」
```

### 2. Arrow = データ交換 という誤解
```
Arrow取得 → 使いやすい形式に変換 → 計算 → Arrowに戻す
（これは完全に間違い）
```

### 3. 部分的知識の危険
- Arrow配列を知っている: ✓
- NumPy配列を知っている: ✓
- でも真のArrow処理を理解していない: ✗

## 現実の問題

### パフォーマンス劣化の連鎖

```
Arrow → NumPy変換: メモリコピー1回
NumPy → 計算: OK
結果 → Arrow変換: メモリコピー2回
合計: 3倍のメモリ使用、2-3倍の処理時間
```

### 実測データ（10,000要素）
| 実装 | 処理時間 | メモリ使用 | 問題 |
|------|----------|------------|------|
| to_numpy()使用 | 245μs | 3倍 | 偽のArrow Native |
| PyList経由 | 240μs | 2.5倍 | まだメモリコピー |
| 真のArrow Native | 100-150μs | 1倍 | ゼロコピー実現 |

## 禁止すべきコードパターン

### ❌ 絶対禁止: to_numpy()
```rust
// "Arrow Native"と言いながらNumPy変換
let numpy_array = arrow_array.to_numpy()?;  // 禁止！
```

### ❌ 絶対禁止: PyList変換
```rust
// NumPy回避のためのPyList迂回
let py_list = py_array.call_method0("to_pylist")?;  // 禁止！
let values: Vec<f64> = py_list.extract()?;
```

### ❌ 絶対禁止: 手動のデータコピー
```rust
// slice.to_vec()によるコピー
let data = arrow_array.values().to_vec();  // 禁止！
```

## 正しいアプローチ

### ✅ 必須: 直接Arrow処理
```rust
use pyo3_arrow::PyArray;

// Arrow配列を直接受け取り、直接処理
pub fn arrow_call_price(
    py: Python,
    spots: PyArray,  // Arrow配列のまま
) -> PyArrowResult<PyObject> {
    let spots_array = spots.as_ref();  // ゼロコピー参照
    // 直接Arrow配列で計算
}
```

### ✅ 推奨: arro3-core使用
```rust
// 軽量で効率的
let result = py_array.to_arro3(py)?;  // Arrow標準準拠
```

## 判断フローチャート

```
Arrow配列を受け取った
    ↓
NumPy/PyListに変換したくなった？
    ↓ Yes → 絶対禁止！立ち止まれ
    ↓ No
直接Arrow配列として処理可能？
    ↓ No → pyo3-arrow/arro3-core検討
    ↓ Yes
ゼロコピーを維持しているか？
    ↓ No → 実装を見直せ
    ↓ Yes
実装継続
```

## 検出方法

```bash
# 禁止パターンの検出
rg "to_numpy|to_pylist|to_vec\(\)" --type rust bindings/

# 正しい実装の確認
rg "PyArray|pyo3_arrow|arro3" --type rust bindings/
```

## 実装停止条件

以下のいずれかが必要になったら即座に実装停止：
1. Arrow → NumPy変換
2. Arrow → PyList変換  
3. データの手動コピー（to_vec等）
4. 中間フォーマットへの変換

## 結論

**Arrow Nativeは「Arrow配列のまま処理」を意味する**

変換の誘惑に負けるな。ゼロコピーを死守せよ。

## 参考資料

- 失敗実装: bindings/python/src/arrow_native.rs (削除済み)
- 成功実装: 現在のpyo3-arrow実装
- 計画書: plans/2025-09-02-rust-arro3-core-complete-migration.md
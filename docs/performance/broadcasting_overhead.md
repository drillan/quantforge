# Broadcasting Performance Analysis

## Executive Summary

`call_price_batch`のbroadcasting機能は、スカラーと配列の混在を許可しますが、小さなオーバーヘッドが発生します。このオーバーヘッドはデータサイズが増えるにつれて急速に減少し、1000要素以上では無視できるレベル（<5%）になります。

## 測定結果

### オーバーヘッドのスケーリング特性

| データサイズ | 全て配列 | スカラー混在 | オーバーヘッド |
|------------|---------|-------------|--------------|
| 10要素     | 10.3μs  | 18.0μs      | **+74.0%**   |
| 100要素    | 13.9μs  | 19.3μs      | **+38.9%**   |
| 1000要素   | 44.3μs  | 46.4μs      | **+4.8%**    |
| 10000要素  | 222.5μs | 230.0μs     | **+3.4%**    |

### コンポーネント別コスト

| 処理内容 | 実行時間 | 説明 |
|---------|---------|------|
| PyArrow scalar→array | 66μs | Pythonでの変換（最も重い） |
| pyany_to_arrow (Rust) | ~3μs | Rust側での変換処理 |
| call_price (single) | 1.3μs | 単一スカラー計算のベースライン |
| call_price_batch (5 scalars) | 16.4μs | 5つのスカラー変換込み |

## 詳細分析

### 1. 固定オーバーヘッドの構成

```
スカラー1個あたりの変換コスト = ~3μs
- PyAny extraction: ~250ns
- Float64Array作成: ~2μs  
- PyArray wrapper: ~750ns
```

### 2. メモリオーバーヘッド

```
スカラー配列1個 = 96 bytes
- Arrow metadata: 64 bytes
- Data (1 float64): 8 bytes
- PyObject overhead: 24 bytes

4スカラーの合計 = 384 bytes (無視できる)
```

### 3. Broadcasting処理のコスト

Rust core内でのbroadcasting処理は非常に効率的：
- 長さチェック: O(1)
- インデックス計算: 各要素につき1-2命令
- 追加のメモリアロケーション: なし

## パフォーマンス特性

### 小規模データ（<100要素）
- **オーバーヘッド**: 大きい（40-70%）
- **絶対時間**: 小さい（<20μs）
- **推奨**: 頻繁に呼ぶ場合は`call_price`を検討

### 中規模データ（100-1000要素）  
- **オーバーヘッド**: 中程度（5-40%）
- **絶対時間**: 許容範囲（20-50μs）
- **推奨**: Broadcastingの利便性が優先

### 大規模データ（>1000要素）
- **オーバーヘッド**: 無視できる（<5%）
- **絶対時間**: 計算時間が支配的
- **推奨**: Broadcastingを積極活用

## ベストプラクティス

### 1. 一般的な使用パターン

```python
# ✅ 推奨: よくあるパターン（spots配列、他はスカラー）
result = call_price_batch(
    spots=pa.array([100, 105, 110]),  # 配列
    strikes=100.0,                      # スカラー（broadcast）
    times=1.0,                          # スカラー（broadcast）
    rates=0.05,                         # スカラー（broadcast）
    sigmas=0.2                          # スカラー（broadcast）
)
```

### 2. パフォーマンス重視の場合

```python
# 小規模・高頻度の場合
if len(data) < 100 and called_frequently:
    # スカラー関数を使用
    results = [call_price(s, k, t, r, sigma) for s in spots]
else:
    # Broadcasting活用
    results = call_price_batch(spots, k, t, r, sigma)
```

### 3. 型変換の最適化

```python
# ❌ 避けるべき: 整数配列（自動変換が発生）
spots = pa.array([100, 105, 110])  # int64 → float64変換

# ✅ 推奨: 最初からfloat配列
spots = pa.array([100.0, 105.0, 110.0])  # 直接float64
```

## 結論

### メリット
1. **柔軟性**: スカラーと配列を自由に混在可能
2. **利便性**: ユーザーコードがシンプル
3. **効率性**: 大規模データでは影響なし

### デメリット
1. **小規模オーバーヘッド**: 100要素未満では顕著
2. **固定コスト**: スカラー1個につき~3μs

### 総合評価
**Broadcasting機能は実用上問題なし**。特に：
- 100要素以上では積極的に使用推奨
- 小規模でも絶対時間は許容範囲（<20μs）
- コードの簡潔性と保守性が向上

## 技術的詳細

### pyany_to_arrow実装の効率性

```rust
pub fn pyany_to_arrow(_py: Python, value: &Bound<'_, PyAny>) -> PyResult<PyArray> {
    // Fast path: すでにArrow配列なら変換不要
    if let Ok(array) = value.extract::<PyArray>() {
        // 型チェックと必要に応じてキャスト
        // オーバーヘッド: ~250ns
    }
    
    // Scalar path: 長さ1配列を作成
    if let Ok(scalar) = value.extract::<f64>() {
        // Float64Array::from(vec![scalar])
        // オーバーヘッド: ~3μs
    }
}
```

### Core側のBroadcasting実装

```rust
// 効率的なインデックス計算
let idx = if array.len() == 1 { 0 } else { i };
// 分岐予測が効くため、実質的なコストなし
```

## 参考データ

- 測定環境: Linux x86_64, Rust 1.78, Python 3.12
- 測定方法: 1000回の繰り返し測定の中央値
- コンパイル: --release mode with optimizations
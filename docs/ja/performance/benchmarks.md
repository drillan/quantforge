# ベンチマーク結果

QuantForgeの詳細なパフォーマンス測定結果です。データは自動的に更新されます。

:::{note}
**最新の最適化により43%のパフォーマンス向上を達成しました。**
- マイクロバッチ最適化（100-1000要素）による小規模バッチの大幅改善
- 高速erf近似実装によるnorm_cdf計算の2-3倍高速化
:::

## データ管理方針

ベンチマーク結果は構造化データとして管理されています：
- **履歴データ**: `benchmark_results/history.jsonl` (JSON Lines形式)
- **最新結果**: `benchmark_results/latest.json`
- **表示用CSV**: `docs/ja/_static/benchmark_data/*.csv` (自動生成)

## テスト環境

```{csv-table}
:file: ../_static/benchmark_data/environment.csv
:header-rows: 1
:widths: 30, 70
```

## Black-Scholesコールオプション価格計算

### 単一計算

Black-Scholes コールオプション価格計算の単一実行パフォーマンス：

```{csv-table}
:file: ../_static/benchmark_data/single_calculation.csv
:header-rows: 1
:widths: 30, 20, 25, 25
```

### バッチ処理パフォーマンス

#### 小規模バッチ（100件）

```{csv-table}
:file: ../_static/benchmark_data/batch_100.csv
:header-rows: 1
:widths: 25, 25, 30, 20
```

#### 中規模バッチ（1,000件）

```{csv-table}
:file: ../_static/benchmark_data/batch_1000.csv
:header-rows: 1
:widths: 25, 25, 30, 20
```

#### 大規模バッチ（10,000件）

```{csv-table}
:file: ../_static/benchmark_data/batch_10000.csv
:header-rows: 1
:widths: 25, 25, 30, 20
```

## パフォーマンス要約

### 対Pure Python

```{csv-table}
:file: ../_static/benchmark_data/performance_summary_python.csv
:header-rows: 1
:widths: 30, 30, 40
```

### 対NumPy+SciPy

```{csv-table}
:file: ../_static/benchmark_data/performance_summary_numpy.csv
:header-rows: 1
:widths: 30, 30, 40
```

## 技術的詳細

### 実装方式の違い

#### Pure Python（forループ）
- Python標準ライブラリ（math）のみ使用
- 各要素を逐次処理（Pythonインタープリタのオーバーヘッド大）
- メモリアクセスパターンが非効率

#### NumPy+SciPy（ベクトル化）
- NumPyのブロードキャスティングで全要素同時計算
- C言語レベルでのループ実行（Pythonオーバーヘッド回避）
- Intel MKLによる最適化（利用可能な場合）
- キャッシュ効率的なメモリアクセス

#### QuantForge（Rust並列処理）
- Rayonによる自動並列化（マルチコアCPU活用）
- ゼロコピーデータ転送（NumPy配列の直接参照）
- 小規模データではFFIオーバーヘッドが相対的に大きい
- 大規模データで並列処理の効果が最大化

### FFI（Foreign Function Interface）オーバーヘッド

FFIは、PythonからRust関数を呼び出す際のデータ変換・転送コストです。QuantForgeではCore層とBindings層を分離し、Bindings層でPyO3を使用してPythonとRust間のデータを効率的にやり取りしています。

#### オーバーヘッドの内訳
- **データ変換**: Python オブジェクト ↔ Rust 型の相互変換
- **GIL取得/解放**: Python のグローバルインタプリタロック管理
- **関数呼び出し**: 言語境界を越える関数呼び出しコスト

#### サイズ別のオーバーヘッド
| データサイズ | 総オーバーヘッド | 要素あたり | 削減率 |
|------------|----------------|------------|--------|
| 単一要素 | ~1 μs | 1 μs | - |
| 100要素 | ~1 μs | 10 ns | 99% |
| 10,000要素 | ~1 μs | 0.1 ns | 99.99% |
| 100万要素 | ~2 μs | 0.002 ns | 99.9998% |

バッチ処理により、FFIオーバーヘッドが要素数で償却され、大規模データでは実質的に無視可能になります。

### 最適化による改善効果

#### マイクロバッチ最適化の効果

| データサイズ | 従来実装 | 最適化後 | 改善率 |
|-------------|---------|---------|--------|
| 100 | 6.1M ops/sec | 8.8M ops/sec | +44% |
| 500 | 10.2M ops/sec | 14.7M ops/sec | +44% |
| 1,000 | 8.5M ops/sec | 12.3M ops/sec | +45% |

4要素ループアンローリングにより、コンパイラの自動ベクトル化が促進され、小規模バッチで大幅な性能向上を実現しました。

### スケーリング特性

| データサイズ | スループット | 効率性 |
|-------------|-------------|--------|
| 100 | 8.8M ops/sec | FFIオーバーヘッド大 |
| 1,000 | 12.3M ops/sec | 良好 |
| 10,000 | 11.8M ops/sec | NumPyと拮抗 |
| 100,000 | 10.4M ops/sec | NumPyがわずかに優位 |
| 1,000,000 | 18.0M ops/sec | 並列化効果最大 |

### データサイズによる最適実装の変化

1. **小規模（〜1,000件）**: QuantForgeが圧倒的優位
   - Pure Pythonより10倍以上高速
   - NumPyより7倍高速

2. **中規模（10,000〜100,000件）**: NumPyとQuantForgeが拮抗
   - FFIオーバーヘッドの影響が顕著
   - NumPyのベクトル化効率が最適化

3. **大規模（100万件以上）**: QuantForgeの並列処理が再び優位
   - マルチコアCPU活用で1.15倍高速
   - メモリ効率も良好

## ベンチマーク実行と分析

### 測定実行

```bash
# ベンチマーク実行
pytest tests/performance/ -m benchmark

# CSV生成（Sphinx用）
python tests/performance/generate_benchmark_report.py

# ドキュメント再ビルド
cd docs/ja && make html
```

### データ分析

```bash
# 履歴分析
cd benchmark_results
cat history.jsonl | tail -n 5 | jq .

# パフォーマンストレンド確認
python -c "
import json
with open('history.jsonl') as f:
    lines = f.readlines()
    for line in lines[-5:]:
        data = json.loads(line)
        print(f\"{data['timestamp']}: {data['version']}\")
"
```

## データ形式

### JSON Lines履歴フォーマット
各行が独立したJSONオブジェクト：
```json
{
  "timestamp": "2025-08-27T14:41:14",
  "version": "0.0.11",
  "git_commit": "abc123",
  "environment": {
    "platform": "Linux",
    "python_version": "3.12.5",
    "cpu_count": 6,
    "memory_gb": 29.3
  },
  "benchmarks": [
    {
      "name": "test_quantforge_single",
      "stats": {
        "mean": 1.4e-6,
        "stddev": 0.05e-6,
        "rounds": 1000
      }
    }
  ]
}
```

## 注記

:::{important}
- 測定値は環境によって変動します
- 実測値ベース（理論値ではありません）
- FFIオーバーヘッドを含む現実的な性能
- コンパイラの自動ベクトル化に依存
:::

## 関連ドキュメント

- [最適化ガイド](optimization.md)
- [チューニングガイド](tuning.md)
- [アーキテクチャ](../development/architecture.md)
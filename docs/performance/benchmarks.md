# ベンチマーク結果

QuantForgeの詳細なパフォーマンス測定結果です。

## データ管理方針

ベンチマーク結果は構造化データとして管理されています：
- **履歴データ**: `benchmarks/results/history.jsonl` (JSON Lines形式)
- **最新結果**: `benchmarks/results/latest.json`
- **CSV出力**: `benchmarks/results/history.csv` (分析用)

## 最新測定結果（2025-08-27）

### テスト環境
- **CPU**: AMD Ryzen 5 5600G (6コア/12スレッド)
- **メモリ**: 29.3 GB
- **OS**: Linux 6.12 (Pop!_OS 22.04)
- **Python**: 3.12.5

### Black-Scholesベンチマーク（実測値）

#### 単一計算
| 実装 | 実測時間 | 相対速度 |
|------|----------|----------|
| QuantForge (Rust) | 1.40 μs | 1.0x (基準) |
| Pure Python (math only) | 3.74 μs | 0.37x |
| SciPy | 89.23 μs | 0.016x |

#### バッチ処理（100万オプション）
| 実装 | 実測時間 | スループット |
|------|----------|-------------|
| QuantForge | 54.88 ms | 18.2M ops/sec |
| NumPy Vectorized | 99.50 ms | 10.1M ops/sec |

## 性能特性

### FFIオーバーヘッド
- 単一呼び出し: 約1μsのオーバーヘッド
- バッチ処理: 要素あたりのオーバーヘッドは無視可能

### スケーリング特性
| データサイズ | スループット | 効率性 |
|-------------|-------------|--------|
| 100 | 11.7M ops/sec | FFIオーバーヘッド大 |
| 1,000 | 16.6M ops/sec | 良好 |
| 10,000 | 18.2M ops/sec | 最適 |
| 100,000+ | 18.3M ops/sec | 飽和 |

## ベンチマーク実行と分析

### 測定実行
```bash
# ベンチマーク実行
cd benchmarks
./run_benchmarks.sh
```

### データ分析
```bash
# 履歴分析
cd benchmarks
uv run python analyze.py

# CSV出力
uv run python save_results.py

# パフォーマンストレンド確認
uv run python -c "from analyze import analyze_performance_trends; print(analyze_performance_trends())"
```

### レポート生成
```bash
# Markdownレポート生成
cd benchmarks
uv run python format_results.py > ../docs/performance/latest_benchmark.md

# 履歴プロット生成（matplotlib必要）
uv run python analyze.py  # results/performance_history.png を生成
```

## データ形式

### JSON Lines履歴フォーマット
各行が独立したJSONオブジェクト：
```json
{"timestamp": "2025-08-27T14:41:14", "system_info": {}, "single": {}, "batch": []}
```

### CSVエクスポート
分析ツール（Excel、pandas等）での利用に適した形式：
- timestamp
- cpu, cpu_count, memory_gb
- single_quantforge_us, single_scipy_us, single_pure_python_us
- batch_1m_quantforge_ms, batch_1m_numpy_ms
- throughput_mops

## パフォーマンス要約

### 対Pure Python
- 単一計算: **2.7倍**高速
- バッチ処理（100件）: **20倍**高速
- バッチ処理（1000件）: **22倍**高速

### 対SciPy/NumPy
- 単一計算: **64倍**高速（SciPy比）
- バッチ処理（100件）: **16倍**高速（NumPy比）
- バッチ処理（100万件）: **1.8倍**高速（NumPy比）

## 注記

- 測定値は環境によって変動します
- 実測値ベース（理論値ではありません）
- FFIオーバーヘッドを含む現実的な性能
- SIMD最適化は現在無効化（安定性優先）

## 関連ドキュメント

- [最適化ガイド](optimization.md)
- [チューニングガイド](tuning.md)
- [アーキテクチャ](../development/architecture.md)
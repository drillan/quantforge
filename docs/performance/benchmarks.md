# ベンチマーク結果

QuantForgeの詳細なパフォーマンス測定結果です。

## 最新の測定結果

**重要**: 実際のユーザー環境での実測値に基づいています。理論値ではありません。

最新の測定結果は [benchmarks_20250827.md](benchmarks_20250827.md) を参照してください。

## テスト環境例

### AMD Ryzen 5 5600G (2025-08-27測定)
- **CPU**: AMD Ryzen 5 5600G (6コア/12スレッド)
- **メモリ**: 29.3 GB
- **OS**: Linux 6.12 (Pop!_OS 22.04)
- **Python**: 3.12.5
- **Rust**: 1.75+

## Black-Scholesベンチマーク（実測値）

### 単一計算

| 実装 | 実測時間 | 相対速度 |
|------|----------|----------|
| QuantForge (Rust) | 1.40 μs | 1.0x (基準) |
| Pure Python (math only) | 3.74 μs | 0.37x |
| SciPy | 89.23 μs | 0.016x |

### バッチ処理（100万オプション）

| 実装 | 実測時間 | スループット |
|------|----------|-------------|
| QuantForge | 54.88 ms | 18.2M ops/sec |
| NumPy Vectorized | 99.50 ms | 10.1M ops/sec |
| Pure Python Loop | N/A | < 1M ops/sec |

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

## ベンチマーク実行方法

```bash
# 自動ベンチマーク実行
cd benchmarks
./run_benchmarks.sh

# 個別実行
uv run python run_comparison.py
uv run python format_results.py
```

## パフォーマンス要約

### 対Pure Python
- 単一計算: **3倍**高速
- バッチ処理: **20倍以上**高速（推定）

### 対SciPy/NumPy
- 単一計算: **64倍**高速（SciPy比）
- バッチ処理: **1.8倍**高速（NumPy比）

## 注記

- 測定値は環境によって変動します
- AMD Ryzen 5 5600Gでの実測値を基準としています
- 高性能サーバーやIntel CPUでは異なる結果になる可能性があります
- SIMD最適化は現在無効化されています（安定性優先）

## グリークス計算

グリークス計算のベンチマークは今後追加予定です。

## 関連ドキュメント

- [最適化ガイド](optimization.md)
- [チューニングガイド](tuning.md)
- [アーキテクチャ](../development/architecture.md)
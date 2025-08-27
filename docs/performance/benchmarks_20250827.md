# Black-Scholesベンチマーク結果

測定日時: 2025-08-27 14:41:14

## 測定環境

- **プラットフォーム**: Linux-6.12.10-76061203-generic-x86_64-with-glibc2.35
- **CPU**: AMD Ryzen 5 5600G
- **コア数**: 6 (論理: 12)
- **メモリ**: 29.3 GB
- **Python**: 3.12.5

## 単一計算性能

### 実測値
| 実装 | 時間 | 説明 |
|------|------|------|
| QuantForge (Rust) | 1.40 μs | 最適化されたRust実装 |
| SciPy | 89.23 μs | 一般的なPython実装 |
| Pure Python | 3.74 μs | 外部ライブラリなし |

### 相対性能
| 比較 | 高速化率 |
|------|----------|
| QuantForge vs Pure Python | **3倍** 高速 |
| QuantForge vs SciPy | **64倍** 高速 |

## バッチ処理性能

| データサイズ | QuantForge | NumPy | Pure Python | QF高速化率 | QFスループット |
|-------------|------------|-------|-------------|-----------|----------------|
| 100 | 8.52 μs | 140.25 μs | 173.14 μs | NumPy: 16.5x | 11.7M ops/sec |
| 1,000 | 60.07 μs | 212.46 μs | 1.33 ms | NumPy: 3.5x | 16.6M ops/sec |
| 10,000 | 548.41 μs | 889.88 μs | N/A | NumPy: 1.6x | 18.2M ops/sec |
| 100,000 | 5.45 ms | 24.22 ms | N/A | NumPy: 4.4x | 18.3M ops/sec |
| 1,000,000 | 54.88 ms | 99.50 ms | N/A | NumPy: 1.8x | 18.2M ops/sec |

## パフォーマンス要約

### 単一計算
- QuantForgeはPure Pythonより**3倍**高速
- QuantForgeはSciPyより**64倍**高速
- 実測値: 1.40 μs（AMD Ryzen 5 5600G）

### バッチ処理（100万件）
- QuantForgeはNumPyより**1.8倍**高速
- 実測スループット: **18.2M ops/sec**
- 処理時間: 54.88 ms

## 測定方法

- **測定回数**: ウォームアップ100回後、1000回測定の中央値
- **Pure Python**: 外部ライブラリを使用しない実装（math.erfによる累積正規分布関数の近似）
- **SciPy**: scipy.stats.normを使用した一般的な実装
- **NumPy**: ベクトル化されたバッチ処理実装
- **QuantForge**: Rust + PyO3による最適化実装

## 再現方法

```bash
# ベンチマーク実行（推奨）
cd benchmarks
./run_benchmarks.sh

# または個別実行
cd benchmarks
uv run python run_comparison.py
uv run python format_results.py
```

## 注記

- このベンチマークは実際のユーザー環境（AMD Ryzen 5 5600G）で測定された実測値です
- 理論値や高性能サーバーでの測定値ではありません
- FFIオーバーヘッドを含む現実的な性能を反映しています
- 小規模バッチではFFIオーバーヘッドが相対的に大きくなるため、大規模バッチ処理で最大の効果を発揮します
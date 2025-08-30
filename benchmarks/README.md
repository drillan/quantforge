# QuantForge ベンチマークパッケージ

高性能オプション価格計算ライブラリQuantForgeのパフォーマンスを測定・管理するPythonパッケージ。

## 📦 パッケージ構成

```
benchmarks/                      # Pythonパッケージ
├── __init__.py                  # パッケージ初期化
├── __main__.py                  # エントリーポイント
├── common/                      # 共通ライブラリ（NEW）
│   ├── __init__.py
│   ├── base.py                  # BenchmarkBase基底クラス
│   ├── formatters.py            # 結果フォーマッター
│   ├── io.py                    # ファイルI/O管理
│   └── metrics.py               # パフォーマンスメトリクス計算
├── baseline/                    # ベースライン実装
│   ├── __init__.py
│   ├── python_baseline.py      # Pure Python実装
│   ├── iv_baseline.py           # SciPy実装
│   └── iv_vectorized.py         # ベクトル化実装
├── runners/                     # 実行スクリプト
│   ├── __init__.py
│   ├── comparison.py            # ベンチマーク実行（旧実装）
│   ├── comparison_refactored.py # ベンチマーク実行（新実装）
│   ├── practical.py             # 実践シナリオ
│   └── arraylike.py             # ArrayLikeテスト
├── analysis/                    # 分析ツール
│   ├── __init__.py
│   ├── save.py                  # データ保存・管理
│   ├── analyze.py               # 分析・トレンド検出
│   └── format.py                # Markdown生成
└── results/                     # 構造化データ（真実の源）
    ├── history.jsonl            # 履歴データ（追記型）
    ├── latest.json              # 最新結果
    └── history.csv              # 分析用エクスポート
```

## 🚀 クイックスタート

### パッケージとして実行（推奨）
```bash
# どのディレクトリからでも実行可能
python -m benchmarks                        # メインメニュー表示
python -m benchmarks.runners.comparison     # 比較ベンチマーク実行
python -m benchmarks.runners.practical      # 実践シナリオ実行
python -m benchmarks.analysis.analyze       # 結果分析
python -m benchmarks.analysis.format        # Markdownレポート生成
```

### 旧来のスクリプト実行（互換性維持）
```bash
cd benchmarks
./run_benchmarks.sh  # 統合実行スクリプト（まだ利用可能）
```

## 📊 測定内容

### 1. 単一計算ベンチマーク
- QuantForge (Rust + PyO3)
- Pure Python (mathモジュールのみ)
- SciPy (scipy.stats.norm使用)

### 2. バッチ処理ベンチマーク
- QuantForge バッチAPI
- NumPy ベクトル化
- Pure Python ループ（小規模のみ）

### 3. スケーリング特性
- 100, 1,000, 10,000, 100,000, 1,000,000 要素
- FFIオーバーヘッドの測定
- スループット飽和点の特定

## 🔧 共通ライブラリの使用

### BenchmarkBase クラス
ベンチマーク実装の基底クラスで、時間測定やシステム情報取得などの共通機能を提供：

```python
from benchmarks.common import BenchmarkBase
from typing import Any

class MyBenchmark(BenchmarkBase):
    def __init__(self):
        super().__init__(warmup_runs=100, measure_runs=1000)
    
    def run(self) -> dict[str, Any]:
        """ベンチマークを実行."""
        self.start_benchmark()
        
        # time_functionメソッドで自動測定
        timing = self.time_function(lambda: some_function())
        
        return {
            "system_info": self.get_system_info(),
            "result": timing.median  # TimingResultから中央値を取得
        }
```

### TimingResult データクラス
測定結果を格納する構造化データ：

```python
from benchmarks.common.base import TimingResult

# 自動的に統計情報を計算
timing = TimingResult.from_times([0.001, 0.002, 0.0015])
print(f"中央値: {timing.median}秒")
print(f"平均: {timing.mean}秒, 標準偏差: {timing.std}秒")
```

### BenchmarkFormatter
結果をMarkdown形式で整形：

```python
from benchmarks.common import BenchmarkFormatter

formatter = BenchmarkFormatter("My Benchmark Results")
markdown = formatter.format_markdown(results)
print(markdown)  # 美しくフォーマットされたMarkdown出力
```

### BenchmarkIO
結果の保存・読み込み・比較：

```python
from benchmarks.common import BenchmarkIO

io = BenchmarkIO()
io.save_result(results)  # 自動的にhistory.jsonlに追記
latest = io.load_latest()  # 最新結果を読み込み
comparison = io.compare_results()  # 前回との比較
```

## 📈 分析機能

### Pythonコードからの使用
```python
# ベースライン実装のインポート
from benchmarks.baseline.python_baseline import (
    black_scholes_pure_python,
    black_scholes_numpy_batch
)

# 分析ツールのインポート
from benchmarks.analysis.analyze import (
    detect_performance_trends,
    generate_summary_table
)
from benchmarks.analysis.save import save_benchmark_result

# 実行例（旧スタイル）
result = black_scholes_pure_python(s=100, k=105, t=1.0, r=0.05, sigma=0.2)
print(f"Pure Python Result: {result:.4f}")

# 分析の実行
trends = detect_performance_trends()
summary = generate_summary_table()

# 新スタイル（共通ライブラリ使用）
from benchmarks.common import BenchmarkBase, BenchmarkIO, BenchmarkFormatter

class QuickTest(BenchmarkBase):
    def run(self):
        timing = self.time_function(
            lambda: black_scholes_pure_python(100, 105, 1.0, 0.05, 0.2)
        )
        return {"pure_python": timing.median}

test = QuickTest()
results = test.run()
print(f"実行時間: {results['pure_python']*1e6:.2f} μs")
```

## 📝 データフォーマット

### JSON Lines (history.jsonl)
各行が独立したJSON：
```json
{"timestamp": "2025-08-27T14:41:14", "system_info": {...}, "single": {...}, "batch": [...]}
```

### Latest JSON (latest.json)
最新結果の完全なスナップショット（整形済み）

### CSV (history.csv)
| カラム | 説明 |
|--------|------|
| timestamp | ISO 8601形式 |
| cpu | プロセッサ名 |
| cpu_count | 物理コア数 |
| memory_gb | メモリ容量 |
| single_quantforge_us | 単一計算時間（μs） |
| batch_1m_quantforge_ms | 100万件処理時間（ms） |
| throughput_mops | スループット（M ops/sec） |

## ⚠️ 注意事項

### データ整合性
- `history.jsonl`は追記専用（編集しない）
- 手動でデータを変更しない
- パスは実行ディレクトリに依存しない設計（`Path(__file__).resolve()`使用）

### 測定の再現性
- 同一環境での測定を推奨
- システム負荷が低い状態で実行
- ウォームアップ実行後に測定（自動実施）

## 🔍 トラブルシューティング

### ImportError: psutil
```bash
uv add psutil
```

### ImportError: types-psutil
```bash
uv add --dev types-psutil
```

### 権限エラー（run_benchmarks.sh）
```bash
chmod +x run_benchmarks.sh
```

## 📚 詳細ドキュメント

包括的な管理方法については以下を参照：

→ **[ベンチマーク管理ガイド](../docs/ja/internal/benchmark_management_guide.md)**

その他の関連ドキュメント：
- [パフォーマンス結果](../docs/performance/benchmarks.md)
- [最適化ガイド](../docs/performance/optimization.md)
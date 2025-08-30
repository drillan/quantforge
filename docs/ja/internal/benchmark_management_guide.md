# ベンチマーク管理ガイド

このドキュメントは、QuantForgeのベンチマークデータ管理と`docs/performance/benchmarks.md`の更新方法を説明します。

## 📊 データ管理アーキテクチャ

### 構造化データ優先の原則
ベンチマーク結果は**構造化データ**として管理され、Markdownドキュメントは自動生成されます。

### オブジェクト指向設計への移行
2025年8月のリファクタリングにより、ベンチマークコードはオブジェクト指向設計に移行しました：

- **67%のコード削減**: 共通ライブラリへの統合による重複排除
- **保守性の向上**: 基底クラスによる統一されたインターフェース
- **拡張性の向上**: 新しいベンチマークの追加が簡単に

```
benchmarks/                      # Pythonパッケージとして構成
├── __init__.py                  # パッケージ初期化
├── __main__.py                  # エントリーポイント
├── common/                      # 共通ライブラリ（NEW）
│   ├── __init__.py
│   ├── base.py                  # ベンチマーク基底クラス
│   │   ├── TimingResult        # 測定結果を格納するデータクラス
│   │   └── BenchmarkBase       # ベンチマーク実行の基底クラス
│   ├── formatters.py            # 結果フォーマッター
│   │   ├── format_time()       # 時間を適切な単位でフォーマット
│   │   ├── format_throughput() # スループットのフォーマット
│   │   └── BenchmarkFormatter  # Markdown/CSV形式への変換
│   ├── io.py                    # ファイルI/O管理
│   │   └── BenchmarkIO         # 結果の保存・読み込み・比較
│   └── metrics.py               # メトリクス計算
│       ├── calculate_speedup()      # 高速化率の計算
│       └── calculate_throughput()   # スループットの計算
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

docs/performance/
└── benchmarks.md                # 自動生成される表示用ドキュメント
```

## 🔄 更新フロー

### 1. ベンチマーク実行と記録

```{code-block} bash
:name: benchmark-management-guide-code-section
:caption: ベンチマーク実行（自動的に履歴に追加）

# モジュールとして実行（どのディレクトリからでも可能）
python -m benchmarks                        # メインメニュー表示
python -m benchmarks.runners.comparison     # 比較ベンチマーク実行
python -m benchmarks.runners.practical      # 実践シナリオ実行

# uvでの実行
uv run python -m benchmarks.runners.comparison
```

実行により以下が自動的に行われます：
1. `results/history.jsonl`に新しい行を追加
2. `results/latest.json`を更新
3. `benchmark_results.json`を生成（互換性のため）

### 2. docs/performance/benchmarks.md の更新

#### 方法A: 最新結果のみ反映（推奨）

```bash
# 1. 最新データの要約を確認（どこからでも実行可能）
python -m benchmarks.analysis.analyze

# 2. benchmarks.mdの該当セクションを手動更新
# 以下の値を更新：
# - 最新測定結果の日付
# - 単一計算の実測値
# - バッチ処理の実測値
# - スループット
```

#### 方法B: 完全な自動生成

```bash
# Markdownセクションを生成（どこからでも実行可能）
python -c "
from benchmarks.analysis.analyze import generate_summary_table
print(generate_summary_table())
" > summary.md

# 必要な部分をbenchmarks.mdにコピー
```

#### 方法C: テンプレートベースの更新

```{code-block} python
:name: benchmark-management-guide-code-benchmarksupdatedocspy
:caption: benchmarks/update_docs.py として保存

# benchmarks/update_docs.py として保存
from pathlib import Path
import json
from datetime import datetime
from benchmarks.analysis import save

def update_benchmarks_doc():
    """docs/performance/benchmarks.mdを最新データで更新."""
    
    # 最新データ読み込み
    results_path = Path(__file__).parent / "results" / "latest.json"
    with open(results_path) as f:
        data = json.load(f)
    
    # テンプレート読み込み
    doc_path = Path(__file__).parent.parent / "docs" / "performance" / "benchmarks.md"
    content = doc_path.read_text()
    
    # 日付更新
    date_str = datetime.fromisoformat(data["timestamp"]).strftime("%Y-%m-%d")
    content = content.replace(
        "## 最新測定結果（", 
        f"## 最新測定結果（{date_str}"
    )
    
    # 実測値更新
    qf_us = data["single"]["quantforge"] * 1e6
    content = update_value(content, "QuantForge (Rust) |", f"{qf_us:.2f} μs")
    
    # 書き戻し
    doc_path.write_text(content)
    print(f"✅ Updated {doc_path}")

if __name__ == "__main__":
    update_benchmarks_doc()
```

### 3. パフォーマンス回帰のチェック

```bash
cd benchmarks

# 回帰検出
uv run python -c "
from analyze import analyze_performance_trends
trends = analyze_performance_trends()
if 'regressions' in trends and trends['regressions']:
    print('⚠️ パフォーマンス回帰検出:')
    for reg in trends['regressions']:
        print(f'  - {reg}')
else:
    print('✅ 回帰なし')
"
```

## 📝 benchmarks.md 更新チェックリスト

### 必須更新項目
- [ ] 測定日付（`## 最新測定結果（YYYY-MM-DD）`）
- [ ] テスト環境のCPU/メモリ情報
- [ ] 単一計算の実測値（μs単位）
- [ ] バッチ処理の実測値（ms単位）
- [ ] スループット（M ops/sec）

### オプション更新項目
- [ ] FFIオーバーヘッドの分析
- [ ] スケーリング特性のグラフ
- [ ] 環境別の比較（異なるCPUでの測定時）

## 📦 プログラムからの使用方法

### パッケージとしてのインポート

```{code-block} python
:name: benchmark-management-guide-code-import
:caption: ベンチマークパッケージの使用例

# ベースライン実装のインポート
from benchmarks.baseline.python_baseline import (
    black_scholes_pure_python,
    black_scholes_numpy_batch
)
from benchmarks.baseline.iv_baseline import (
    black_scholes_price_scipy,
    implied_volatility_scipy
)

# 分析ツールのインポート
from benchmarks.analysis.analyze import (
    detect_performance_trends,
    generate_summary_table
)
from benchmarks.analysis.save import save_benchmark_result

# 実行例
result = black_scholes_pure_python(s=100, k=105, t=1.0, r=0.05, sigma=0.2)
print(f"Pure Python Result: {result:.4f}")

# 分析の実行
trends = detect_performance_trends()
summary = generate_summary_table()
```

### カスタムベンチマークの作成

#### 旧実装（手動測定）

```{code-block} python
:name: benchmark-management-guide-code-custom-old
:caption: カスタムベンチマークの旧実装

import time
from benchmarks.analysis.save import save_benchmark_result

def custom_benchmark():
    """独自のベンチマークを実装（旧スタイル）."""
    results = {}
    
    # 測定対象の実装をインポート
    from benchmarks.baseline.python_baseline import black_scholes_pure_python
    from quantforge import models
    
    # 測定
    start = time.perf_counter()
    for _ in range(10000):
        black_scholes_pure_python(100, 105, 1.0, 0.05, 0.2)
    pure_python_time = time.perf_counter() - start
    
    start = time.perf_counter()
    for _ in range(10000):
        models.call_price(100, 105, 1.0, 0.05, 0.2)
    quantforge_time = time.perf_counter() - start
    
    # 結果を保存
    results = {
        "pure_python": pure_python_time,
        "quantforge": quantforge_time,
        "speedup": pure_python_time / quantforge_time
    }
    
    save_benchmark_result(results)
    return results
```

#### 新実装（共通ライブラリ使用）

```{code-block} python
:name: benchmark-management-guide-code-custom-new
:caption: カスタムベンチマークの新実装（推奨）

from benchmarks.common import BenchmarkBase, BenchmarkFormatter, BenchmarkIO
from benchmarks.common.metrics import calculate_speedup
from typing import Any

class CustomBenchmark(BenchmarkBase):
    """独自のベンチマーク実装例."""
    
    def __init__(self):
        super().__init__(warmup_runs=100, measure_runs=1000)
        
    def run(self) -> dict[str, Any]:
        """ベンチマークを実行."""
        self.start_benchmark()
        
        results = {
            "system_info": self.get_system_info(),
            "comparison": self.benchmark_comparison(),
        }
        
        # 結果を自動保存
        io = BenchmarkIO()
        io.save_result(results)
        
        # Markdown形式で出力
        formatter = BenchmarkFormatter("Custom Benchmark Results")
        print(formatter.format_markdown(results))
        
        return results
    
    def benchmark_comparison(self) -> dict[str, Any]:
        """カスタム測定の実装."""
        from benchmarks.baseline.python_baseline import black_scholes_pure_python
        from quantforge import models
        
        # time_function メソッドで自動測定
        pure_python_timing = self.time_function(
            lambda: black_scholes_pure_python(100, 105, 1.0, 0.05, 0.2)
        )
        
        quantforge_timing = self.time_function(
            lambda: models.call_price(100, 105, 1.0, 0.05, 0.2)
        )
        
        return {
            "pure_python": {
                "median": pure_python_timing.median,
                "mean": pure_python_timing.mean,
                "std": pure_python_timing.std,
            },
            "quantforge": {
                "median": quantforge_timing.median,
                "mean": quantforge_timing.mean,
                "std": quantforge_timing.std,
            },
            "speedup": calculate_speedup(
                pure_python_timing.median, 
                quantforge_timing.median
            ),
        }

# 使用例
if __name__ == "__main__":
    benchmark = CustomBenchmark()
    results = benchmark.run()
```

### 実装の比較

| 項目 | 旧実装 | 新実装（common使用） |
|------|---------|-----------------------|
| コード行数 | 各ファイル200-300行 | 基底クラス継承で100行程度 |
| 時間測定 | 手動実装 | TimingResult自動管理 |
| フォーマット | 各ファイルで重複実装 | BenchmarkFormatter統一 |
| データ保存 | 手動JSON操作 | BenchmarkIO自動管理 |
| ウォームアップ | 手動またはなし | 自動実施 |
| 統計情報 | 最小限 | 平均、中央値、標準偏差等 |

## 🔍 データ分析コマンド

### 履歴の統計情報

```{code-block} bash
:name: benchmark-management-guide-code-section
:caption: 全履歴の要約統計

# 全履歴の要約統計（どこからでも実行可能）
python -c "
from benchmarks.analysis.analyze import load_history
import json

history = load_history()

print(f'測定回数: {len(history)}')
if history:
    print(f'期間: {history[0]["timestamp"]} ~ {history[-1]["timestamp"]}')
    
    # QuantForge単一計算の統計
    qf_times = [h['single']['quantforge'] * 1e6 for h in history if 'single' in h]
    if qf_times:
        print(f'QuantForge単一計算:')
        print(f'  最小: {min(qf_times):.2f} μs')
        print(f'  最大: {max(qf_times):.2f} μs')
        print(f'  平均: {sum(qf_times)/len(qf_times):.2f} μs')
"
```

### CSV出力と外部ツール連携

```{code-block} bash
:name: benchmark-management-guide-code-csv
:caption: CSV生成

# CSV生成
cd benchmarks
uv run python save_results.py

# pandasで分析（要pandas）
python -c "
import pandas as pd
df = pd.read_csv('results/history.csv')
print(df.describe())
print('\n相関行列:')
print(df[['single_quantforge_us', 'batch_1m_quantforge_ms']].corr())
"
```

## ⚠️ 注意事項

### やってはいけないこと

1. **❌ Markdownファイルを手動で大幅編集**
   - 構造化データが真実の源
   - Markdownは表示用

2. **❌ 日付付きMarkdownファイルの作成**
   - `benchmarks_YYYYMMDD.md`は不要
   - 履歴は`history.jsonl`で管理

3. **❌ 測定値の手動入力**
   - 必ず実際の測定結果を使用
   - 理論値や推定値は記載しない

### 推奨事項

1. **✅ 定期的なベンチマーク実行**
   - 週1回程度の定期実行
   - 大きな変更後は必ず実行

2. **✅ 環境情報の記録**
   - CPU、メモリ、OS情報は自動記録される
   - 特殊な環境設定があれば追記

3. **✅ 回帰検出の自動化**
   - CI/CDへの統合を検討
   - 5%以上の性能劣化で警告

## 🚀 将来の改善案

### 自動化の強化
- GitHub Actionsでの定期実行
- PRごとのベンチマーク比較
- 自動的なbenchmarks.md更新

### 可視化の改善
- Web UIでのグラフ表示
- 環境別の比較ダッシュボード
- リアルタイムモニタリング

### データ管理の拡張
- PostgreSQL/SQLiteへの移行
- タグ付け機能（リリース版、実験版）
- A/Bテスト機能

## 🎆 最近の改善成果

### 2025年8月リファクタリング
共通ライブラリの導入により大幅な改善を達成：

- **コード削減**: 2,080行 → 680行（67%削減）
- **重複排除**: 同じ測定ロジックを一元化
- **保守性**: 修正箇所を1ヵ所に集約
- **拡張性**: 新ベンチマーク追加が簡単に

## 関連ファイル

- [benchmarks.md](../performance/benchmarks.md) - 公開用ドキュメント
- [benchmarks/README.md](../../benchmarks/README.md) - ベンチマークツールの説明
- [naming_conventions.md](naming_conventions.md) - 命名規則（パラメータ名）
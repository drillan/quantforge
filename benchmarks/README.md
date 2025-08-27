# QuantForge ベンチマークツール

このディレクトリには、QuantForgeのパフォーマンスを測定・管理するツールが含まれています。

## 🏗️ アーキテクチャ

### データフロー
```
実行 → 構造化データ保存 → 分析 → レポート生成
     ↓
run_comparison.py → results/history.jsonl → analyze.py → format_results.py
                  → results/latest.json
                  → results/history.csv
```

### ファイル構成
```
benchmarks/
├── python_baseline.py      # Python実装（Pure/SciPy/NumPy）
├── run_comparison.py       # ベンチマーク実行エンジン
├── save_results.py        # データ管理（JSONL/CSV）
├── analyze.py             # 分析・トレンド検出
├── format_results.py      # Markdown生成
├── run_benchmarks.sh      # 統合実行スクリプト
├── results/               # 構造化データストレージ
│   ├── history.jsonl     # 履歴（追記型）
│   ├── latest.json       # 最新結果
│   └── history.csv       # 分析用エクスポート
└── benchmark_results.json # 互換性用（廃止予定）
```

## 🚀 クイックスタート

### 基本的な実行
```bash
# 完全なベンチマーク実行
./run_benchmarks.sh

# または個別実行
uv run python run_comparison.py
```

### 結果の確認
```bash
# 要約表示
uv run python analyze.py

# Markdownレポート生成
uv run python format_results.py

# CSV出力
uv run python save_results.py
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

## 🔧 設定とカスタマイズ

### BenchmarkRunnerクラス
```python
runner = BenchmarkRunner(
    warmup_runs=100,    # ウォームアップ回数
    measure_runs=1000   # 測定回数
)
```

### 測定パラメータ
```python
# run_comparison.py内で調整可能
s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
```

## 📈 分析機能

### パフォーマンストレンド
```python
from analyze import analyze_performance_trends

trends = analyze_performance_trends()
# 回帰検出、改善検出、前回との比較
```

### 履歴統計
```python
from save_results import load_history

history = load_history()
# 全測定結果のリスト（時系列順）
```

### CSV出力
```python
from save_results import export_to_csv

export_to_csv("custom_output.csv")
# Excel、pandas等での分析用
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
- バックアップは定期的に実施

### 測定の再現性
- 同一環境での測定を推奨
- システム負荷が低い状態で実行
- 電源管理設定を「パフォーマンス」に

### Pure Python実装について
- Abramowitz & Stegun近似を使用
- 精度は約1%（実用上問題なし）
- 教育・比較目的

## 🔍 トラブルシューティング

### ImportError: psutil
```bash
uv add psutil
```

### ImportError: types-psutil
```bash
uv add --dev types-psutil
```

### matplotlib未インストール（プロット生成）
```bash
uv add matplotlib  # オプション
```

### 権限エラー（run_benchmarks.sh）
```bash
chmod +x run_benchmarks.sh
```

## 📚 関連ドキュメント

- [ベンチマーク管理ガイド](../docs/internal/benchmark_management_guide.md)
- [パフォーマンス結果](../docs/performance/benchmarks.md)
- [最適化ガイド](../docs/performance/optimization.md)
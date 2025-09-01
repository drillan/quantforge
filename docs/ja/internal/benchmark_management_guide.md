# ベンチマーク管理ガイド

## 概要

QuantForgeのベンチマーク管理システムは、Pure Python、NumPy+SciPy、QuantForge（Rust実装）の3つの実装を比較し、パフォーマンスの推移を追跡します。

## ディレクトリ構造

```
tests/performance/
├── conftest.py                    # pytest設定と自動記録
├── test_all_benchmarks.py         # 3実装の比較テスト
├── test_benchmark_system.py       # システム検証テスト
└── generate_benchmark_report.py   # レポート生成スクリプト

benchmark_results/
├── history.jsonl                  # 履歴（追記専用）
└── latest.json                    # 最新結果
```

## 主要コンポーネント

### 1. conftest.py
pytestのセッション終了時に自動的にベンチマーク結果を記録します。

- `BenchmarkRecorder`: シンプルな記録クラス
- `pytest_sessionfinish`: セッション終了フック
- `pytest_benchmark_compare_machine_info`: マシン情報追加

### 2. test_all_benchmarks.py
3つの実装を比較するベンチマークテスト：

- `black_scholes_pure_python`: math標準ライブラリのみ使用
- `black_scholes_numpy_scipy`: ベクトル化実装
- QuantForge: Rust実装（PyO3バインディング）

テストクラス：
- `TestSingleCalculation`: 単一計算のベンチマーク
- `TestBatchCalculation`: バッチ処理（100, 1000, 10000件）
- `TestModelComparison`: 精度検証とモデル比較

### 3. generate_benchmark_report.py
JSON形式の結果からMarkdownレポートを生成：

```python
generator = BenchmarkReportGenerator()
report = generator.generate_report()
generator.save_report("benchmark_report.md")
```

## 使用方法

### ベンチマーク実行

```bash
# 全ベンチマークを実行
pytest tests/performance/ -m benchmark

# 特定のテストのみ実行
pytest tests/performance/test_all_benchmarks.py::TestSingleCalculation -m benchmark

# 詳細出力付き
pytest tests/performance/ -m benchmark -v --benchmark-verbose
```

### レポート生成

```bash
# コンソールに出力
python tests/performance/generate_benchmark_report.py

# ファイルに保存
python tests/performance/generate_benchmark_report.py docs/ja/performance/latest_benchmark.md
```

### 履歴の確認

```bash
# 最新結果を表示
cat benchmark_results/latest.json | jq .

# 履歴から特定バージョンを検索
grep '"version": "0.2.0"' benchmark_results/history.jsonl | jq .
```

## データ形式

### history.jsonl
各行が独立したJSONオブジェクト（JSON Lines形式）：

```json
{
  "version": "0.2.0",
  "git_commit": "abc123",
  "timestamp": "2025-01-01T12:00:00Z",
  "environment": {
    "platform": "Linux",
    "python_version": "3.12.5",
    "cpu_count": 6,
    "memory_gb": 29.3
  },
  "benchmarks": [
    {
      "name": "test_all_benchmarks.py::TestSingleCalculation::test_quantforge_single",
      "stats": {
        "min": 1.4e-6,
        "max": 1.5e-6,
        "mean": 1.45e-6,
        "stddev": 0.05e-6,
        "rounds": 1000,
        "iterations": 1000
      }
    }
  ]
}
```

### latest.json
history.jsonlの最新エントリと同じ形式。

## 品質チェック

```bash
# Python品質チェック
uv run ruff format tests/performance/
uv run ruff check tests/performance/ --fix
uv run mypy tests/performance/

# テスト実行（ベンチマーク以外）
pytest tests/performance/ -m "not benchmark"
```

## トラブルシューティング

### ベンチマーク結果が記録されない
1. `benchmark_results/`ディレクトリの書き込み権限を確認
2. `pytest_sessionfinish`フックが呼ばれているか確認
3. `--benchmark-disable`オプションが設定されていないか確認

### レポート生成エラー
1. `benchmark_results/history.jsonl`または`latest.json`が存在するか確認
2. JSONフォーマットが正しいか確認
3. 必要なフィールドが含まれているか確認

### パフォーマンス測定のばらつき
1. システムの負荷を確認（他のプロセスを停止）
2. CPUガバナーをperformanceに設定
3. ベンチマーク実行回数を増やす

## 移行完了状況

✅ 完了した作業：
- `benchmarks/`ディレクトリを完全削除
- `benchmark_recorder.py`（v2.0.0タグ付き）を削除
- `tests/performance/`に新システムを構築
- pytest-benchmarkとの統合
- 自動記録機能の実装
- レポート生成スクリプトの作成

## 注意事項

- バージョン番号（v2.0.0など）は使用しない（混乱を避けるため）
- レガシーコードは残さない（技術的負債ゼロ原則）
- 毎回のpytest実行でベンチマークは実行されない（`-m benchmark`が必要）
- FFIオーバーヘッドを含む現実的な測定値を記録
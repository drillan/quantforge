# ベンチマーク管理ガイド

## 概要

QuantForgeのベンチマーク管理システムの詳細は、内部ツールディレクトリに移動しました。

## 📁 新しい場所

ベンチマーク自動化ツールとその詳細なドキュメントは以下にあります：

```
.internal/benchmark_automation/
├── README.md                      # 詳細なドキュメント（このファイルの後継）
├── generate_benchmark_report.py   # レポート生成スクリプト（tests/performance/から移動）
├── update_readme.py               # README更新スクリプト
└── update_all.sh                 # 統合実行スクリプト
```

## 🔗 参照先

以下の情報については **`.internal/benchmark_automation/README.md`** を参照してください：
- ディレクトリ構造の詳細
- 主要コンポーネントの説明
- データ形式（history.jsonl、latest.json）
- 詳細な使用方法
- トラブルシューティング

## クイックスタート

```bash
# 完全自動実行（プロジェクトルートから）
.internal/benchmark_automation/update_all.sh

# または個別実行
pytest tests/performance/ -m benchmark
python .internal/benchmark_automation/generate_benchmark_report.py
```

## 関連ファイル

### テストファイル（tests/performance/）
- `conftest.py`: pytest設定と自動記録
- `test_all_benchmarks.py`: 3実装の比較テスト
- `test_benchmark_system.py`: システム検証テスト

### データファイル
- `benchmark_results/history.jsonl`: 履歴（追記専用）
- `benchmark_results/latest.json`: 最新結果
- `docs/ja/_static/benchmark_data/`: CSV出力

---

*注意: このファイルは概要のみを提供します。詳細な技術情報とトラブルシューティングは `.internal/benchmark_automation/README.md` を参照してください。*
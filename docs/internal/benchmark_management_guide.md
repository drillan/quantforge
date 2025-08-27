# ベンチマーク管理ガイド

このドキュメントは、QuantForgeのベンチマークデータ管理と`docs/performance/benchmarks.md`の更新方法を説明します。

## 📊 データ管理アーキテクチャ

### 構造化データ優先の原則
ベンチマーク結果は**構造化データ**として管理され、Markdownドキュメントは自動生成されます。

```
benchmarks/
├── results/                      # 構造化データ（真実の源）
│   ├── history.jsonl            # 履歴データ（追記型）
│   ├── latest.json              # 最新結果
│   └── history.csv              # 分析用エクスポート
├── run_comparison.py            # ベンチマーク実行
├── save_results.py              # データ保存・管理
├── analyze.py                   # 分析・トレンド検出
└── format_results.py            # Markdown生成

docs/performance/
└── benchmarks.md                # 自動生成される表示用ドキュメント
```

## 🔄 更新フロー

### 1. ベンチマーク実行と記録

```bash
# ベンチマーク実行（自動的に履歴に追加）
cd benchmarks
./run_benchmarks.sh

# または手動実行
uv run python run_comparison.py
```

実行により以下が自動的に行われます：
1. `results/history.jsonl`に新しい行を追加
2. `results/latest.json`を更新
3. `benchmark_results.json`を生成（互換性のため）

### 2. docs/performance/benchmarks.md の更新

#### 方法A: 最新結果のみ反映（推奨）

```bash
cd benchmarks

# 1. 最新データの要約を確認
uv run python analyze.py

# 2. benchmarks.mdの該当セクションを手動更新
# 以下の値を更新：
# - 最新測定結果の日付
# - 単一計算の実測値
# - バッチ処理の実測値
# - スループット
```

#### 方法B: 完全な自動生成

```bash
cd benchmarks

# Markdownセクションを生成
uv run python -c "
from analyze import generate_summary_table
print(generate_summary_table())
" > summary.md

# 必要な部分をbenchmarks.mdにコピー
```

#### 方法C: テンプレートベースの更新

```python
# benchmarks/update_docs.py として保存
from pathlib import Path
import json
from datetime import datetime

def update_benchmarks_doc():
    """docs/performance/benchmarks.mdを最新データで更新."""
    
    # 最新データ読み込み
    with open("results/latest.json") as f:
        data = json.load(f)
    
    # テンプレート読み込み
    doc_path = Path("../docs/performance/benchmarks.md")
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

## 🔍 データ分析コマンド

### 履歴の統計情報

```bash
# 全履歴の要約統計
cd benchmarks
uv run python -c "
import json
from pathlib import Path

history = []
with open('results/history.jsonl') as f:
    for line in f:
        history.append(json.loads(line))

print(f'測定回数: {len(history)}')
print(f'期間: {history[0]["timestamp"]} ~ {history[-1]["timestamp"]}')

# QuantForge単一計算の統計
qf_times = [h['single']['quantforge'] * 1e6 for h in history]
print(f'QuantForge単一計算:')
print(f'  最小: {min(qf_times):.2f} μs')
print(f'  最大: {max(qf_times):.2f} μs')
print(f'  平均: {sum(qf_times)/len(qf_times):.2f} μs')
"
```

### CSV出力と外部ツール連携

```bash
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

## 関連ファイル

- [benchmarks.md](../performance/benchmarks.md) - 公開用ドキュメント
- [benchmarks/README.md](../../benchmarks/README.md) - ベンチマークツールの説明
- [naming_conventions.md](naming_conventions.md) - 命名規則（パラメータ名）
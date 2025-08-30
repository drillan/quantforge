# QuantForge ベンチマークパッケージ

高性能オプション価格計算ライブラリQuantForgeのパフォーマンスを測定・管理するPythonパッケージ。

## 📦 パッケージ構成

```
benchmarks/                      # Pythonパッケージ
├── __init__.py                  # パッケージ初期化
├── __main__.py                  # エントリーポイント
├── baseline/                    # ベースライン実装
│   ├── __init__.py
│   ├── python_baseline.py      # Pure Python実装
│   ├── iv_baseline.py           # SciPy実装
│   └── iv_vectorized.py         # ベクトル化実装
├── runners/                     # 実行スクリプト
│   ├── __init__.py
│   ├── comparison.py            # ベンチマーク実行
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

# 実行例
result = black_scholes_pure_python(s=100, k=105, t=1.0, r=0.05, sigma=0.2)
print(f"Pure Python Result: {result:.4f}")

# 分析の実行
trends = detect_performance_trends()
summary = generate_summary_table()
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
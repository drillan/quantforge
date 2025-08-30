# benchmarksパッケージ再構築計画

## 概要
相対パス依存のベンチマークスクリプトを、完全なPythonパッケージとして再構築

## ステータス
- Status: ACTIVE
- Created: 2025-08-30
- Language: Python

## 目的
- 相対インポート依存の完全排除
- 環境非依存の実行環境構築
- 技術的負債ゼロの理想実装

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "benchmarks"
    meaning: "ベンチマークパッケージ"
    source: "プロジェクト既存構造"
  - name: "python_baseline"
    meaning: "Pure Python実装"
    source: "既存モジュール名"
  - name: "iv_baseline"
    meaning: "SciPy実装"
    source: "既存モジュール名"
  - name: "iv_vectorized"
    meaning: "ベクトル化実装"
    source: "既存モジュール名"
```

### 4.2 新規提案命名（必要な場合）
```yaml
proposed_names:
  - name: "benchmarks.baseline"
    meaning: "ベースライン実装サブパッケージ"
    justification: "実装の種類を明確に分類"
    status: "approved"
  - name: "benchmarks.runners"
    meaning: "実行スクリプトサブパッケージ"
    justification: "実行可能スクリプトの分離"
    status: "approved"
  - name: "benchmarks.analysis"
    meaning: "分析ツールサブパッケージ"
    justification: "分析機能の明確な分離"
    status: "approved"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## 現状の問題点

### 1. 相対インポート依存
```python
# 現在の問題のあるコード
from iv_baseline import black_scholes_price_scipy
from python_baseline import black_scholes_pure_python
```

### 2. sys.path操作による強引な解決
```python
# tests/test_benchmark_implementations.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

### 3. 実行ディレクトリ依存
```bash
# benchmarksディレクトリに移動しないと動作しない
cd benchmarks
python run_comparison.py
```

## 理想形のディレクトリ構造

```
benchmarks/
├── __init__.py              # パッケージ初期化
├── __main__.py              # python -m benchmarks対応
├── baseline/                # ベースライン実装（明確な分類）
│   ├── __init__.py
│   ├── python_baseline.py  # Pure Python実装
│   ├── iv_baseline.py       # SciPy実装
│   └── iv_vectorized.py    # ベクトル化実装
├── runners/                 # 実行スクリプト（役割明確化）
│   ├── __init__.py
│   ├── comparison.py        # 比較ベンチマーク
│   ├── practical.py         # 実践シナリオ
│   └── arraylike.py         # ArrayLikeテスト
├── analysis/                # 分析ツール（機能分離）
│   ├── __init__.py
│   ├── analyze.py           # トレンド分析
│   ├── format.py            # 結果フォーマット
│   └── save.py              # データ保存
└── results/                 # データディレクトリ（変更なし）
    └── ...
```

## 実装計画

### Phase 1: ドキュメント更新
1. `docs/ja/internal/benchmark_management_guide.md`の更新
   - 実行方法を`python -m benchmarks.xxx`形式に変更
   - cdコマンドの削除
   - プログラムからのインポート例追加

### Phase 2: パッケージ設定
1. pyproject.tomlへの設定追加
   ```toml
   [tool.setuptools.packages.find]
   where = ["."]
   include = ["quantforge*", "benchmarks*"]
   namespaces = false
   
   [tool.setuptools.package-data]
   benchmarks = ["*.json", "*.md", "results/*.json", "results/*.jsonl"]
   ```

### Phase 3: ディレクトリ構造再編成
1. サブパッケージディレクトリの作成
2. ファイルの移動と整理

### Phase 4: インポート文の修正
1. 相対インポートから絶対インポートへの変更
2. すべてのファイルで統一

### Phase 5: エントリーポイント作成
1. `__main__.py`の作成
2. 各サブパッケージの`__init__.py`作成

### Phase 6: テストコード修正
1. sys.path操作の削除
2. try/except ImportErrorの削除

### Phase 7: クリーンアップ
1. `run_benchmarks.sh`の削除
2. 不要なコードの削除

### Phase 8: 品質チェック
1. pytestの実行
2. mypy, ruffチェック
3. 実行テスト

## 破壊的変更（後方互換性なし）

### 実行方法の完全変更
- **Before**: `cd benchmarks && python run_comparison.py`
- **After**: `python -m benchmarks.runners.comparison`

### インポート方法の完全変更
- **Before**: `from iv_baseline import xxx`
- **After**: `from benchmarks.baseline.iv_baseline import xxx`

### ファイル構造の完全変更
- フラット構造 → 階層構造
- 直接実行不可能に

## 期待される成果

1. **技術的負債ゼロ**
   - sys.path操作なし
   - try/except回避なし
   - 条件分岐なし

2. **環境非依存**
   - どのディレクトリからでも実行可能
   - PYTHONPATH設定不要
   - CI/CDで安定動作

3. **Pythonic**
   - 標準的なパッケージ構造
   - 明確なモジュール階層
   - `python -m`による標準的な実行

4. **保守性向上**
   - 役割ごとのディレクトリ分離
   - 明確な依存関係
   - 将来の拡張が容易

## 成功基準

- [ ] すべてのベンチマークが`python -m`で実行可能
- [ ] プロジェクトルートから全機能にアクセス可能
- [ ] sys.path操作が完全に削除
- [ ] pytest実行時にImportError発生なし
- [ ] mypy, ruffがエラーなし
- [ ] CI/CDパイプラインが正常動作

## 削除対象ファイル・コード

1. `benchmarks/run_benchmarks.sh`
2. すべての`sys.path.insert()`
3. すべての`try/except ImportError`
4. 相対インポート文

## リスクと対策

### リスク
- 既存のCIスクリプトが動作しなくなる
- 開発者の既存ワークフローへの影響

### 対策
- ドキュメントの詳細な更新
- 明確な実行例の提供
- エラーメッセージの改善
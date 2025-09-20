# ドキュメントコードテストガイド

QuantForgeプロジェクトのドキュメント内のPythonコードサンプルを自動的にテストし、APIとの整合性を確保するシステムです。

## 概要

### 目的
- ドキュメント内のすべてのPythonコードサンプルが実行可能であることを保証
- APIの変更時にドキュメントの不整合を自動検知
- ユーザーがコピー&ペーストで即座に使用できるコード例を提供

### システム構成
```
tests/doc_tests/
├── README.md                    # システム概要
├── code_extractor.py           # コードブロック抽出エンジン
├── conftest.py                 # pytest設定とフィクスチャ
├── test_documentation_code.py  # メインテストファイル
├── fix_documentation_codes.py  # 自動修正スクリプト
├── check_doc_codes.py          # 統計チェックツール
├── analyze_errors.py           # エラー分析ツール
└── FINAL_REPORT.md            # 実装完了報告書
```

## 使用方法

### 基本的なテスト実行

```bash
# デフォルトのドキュメントコードをテスト（TESTED_PATHSで定義）
pytest tests/doc_tests/ -v

# 特定のドキュメントのみテスト
pytest tests/doc_tests/ --doc-filter quickstart

# ワイルドカードパターンでテスト
pytest tests/doc_tests/ --doc-filter "docs/ja/api/python/*.md"
pytest tests/doc_tests/ --doc-filter "docs/*/quickstart.md"

# 詳細レポート付きでテスト
pytest tests/doc_tests/ --doc-report

# 時間のかかるテストをスキップ
pytest tests/doc_tests/ --skip-doc-slow
```

### デフォルトテスト対象の設定

`tests/doc_tests/test_documentation_code.py`の`TESTED_PATHS`を編集：

```python
# デフォルトでテストされるドキュメント（2025-09-21更新）
TESTED_PATHS = [
    "docs/ja/quickstart.md",
    "docs/en/quickstart.md",
    # 日本語APIドキュメント
    "docs/ja/api/python/american.md",
    "docs/ja/api/python/batch_processing.md",
    "docs/ja/api/python/black76.md",
    "docs/ja/api/python/black_scholes.md",
    "docs/ja/api/python/greeks.md",
    "docs/ja/api/python/implied_vol.md",
    "docs/ja/api/python/index.md",
    "docs/ja/api/python/market_utils.md",
    "docs/ja/api/python/merton.md",
    "docs/ja/api/python/pricing.md"
]
```

### 統計情報の確認

```bash
# 全体的な統計を表示
uv run python tests/doc_tests/check_doc_codes.py

# 特定ファイルのコードブロックを確認
uv run python tests/doc_tests/code_extractor.py docs/ja/quickstart.md

# エラーの詳細分析
uv run python tests/doc_tests/analyze_errors.py
```

### 自動修正の実行

```bash
# dry-runで修正内容を確認（推奨）
python tests/doc_tests/fix_documentation_codes.py docs/ --dry-run --verbose

# 特定のファイルのみ修正
python tests/doc_tests/fix_documentation_codes.py docs/ja/quickstart.md

# 全ドキュメントを修正
python tests/doc_tests/fix_documentation_codes.py docs/
```

## 対応するコードブロック形式

### 1. 単純なPythonコードブロック
```markdown
```python
from quantforge.models import black_scholes
price = black_scholes.call_price(100, 100, 1.0, 0.05, 0.2)
print(f"Price: {price}")
```
```

### 2. Sphinxコードブロック
```markdown
```{code-block} python
:name: example-name
:caption: サンプルコード
:no-test:  # このオプションでスキップ可能

from quantforge.models import black_scholes
price = black_scholes.call_price(100, 100, 1.0, 0.05, 0.2)
```
```

## 自動スキップ機能

以下のパターンを含むコードは自動的にスキップされます：

### 未定義関数の使用
```python
# 自動的にスキップされる例
market_price = get_market_price(strike)  # 未定義関数
```

### Matplotlib表示
```python
# 自動的にスキップされる例
plt.show()  # matplotlib表示
pyplot.show()
```

### プレースホルダーコード
```python
# 自動的にスキップされる例
# 実際の市場データ取得関数
...  # 省略記号
```

### 手動スキップ
```markdown
```{code-block} python
:no-test:

# このコードはテストされません
experimental_function()
```
```

## テスト環境

### 自動提供される環境
テスト実行時には以下の環境が自動的に提供されます：

```python
# QuantForgeモジュール
from quantforge.models import black_scholes, black76, merton, american
import quantforge

# 数値計算ライブラリ
import numpy as np
import pyarrow as pa

# モック関数
def get_market_price(strike):
    """市場価格を取得する仮の関数"""
    base_price = 10.0
    moneyness = abs(100.0 - strike) / 100.0
    return base_price * (1.0 - moneyness * 0.5)

# 標準ライブラリ
import time
import math
```

### matplotlib対応
- matplotlibがインストールされている場合、表示を自動的に無効化
- インストールされていない場合はエラーを回避

## 自動修正機能

### 修正可能な問題

#### 1. バッチAPIパラメータ名の不一致
```python
# 修正前（誤）
black_scholes.call_price_batch(spots=spots, strikes=100.0, times=1.0, rates=0.05, sigmas=0.2)

# 修正後（正）
black_scholes.call_price_batch(spots=spots, strikes=100.0, times=1.0, rates=0.05, sigmas=0.2)
```

#### 2. Greeks辞書アクセスの不一致
```python
# 修正前（誤）
delta = greeks['delta']

# 修正後（正）
delta = greeks['delta']
```

#### 3. コードブロックタイプの誤分類
```markdown
<!-- 修正前（誤） -->
```bash
pip install quantforge
```

<!-- 修正後（正） -->
```bash
pip install quantforge
```
```

### 手動修正が必要な問題

以下は自動修正できず、手動対応が必要です：

- **コンテキスト依存**: 前のコードブロックで定義された変数への参照
- **構文エラー**: 複雑な構文問題やインデントエラー
- **未定義変数**: importの不足、変数定義の欠如
- **不完全なコード**: 説明用の擬似コード

## 開発者向けガイド

### 新しいスキップパターンの追加

`tests/doc_tests/code_extractor.py`の`SKIP_PATTERNS`に正規表現を追加：

```python
SKIP_PATTERNS = [
    # 既存のパターン
    r'get_market_price\s*\(',
    r'plt\.show\s*\(',

    # 新しいパターンを追加
    r'your_custom_pattern\s*\(',
]
```

### 新しいモック関数の追加

`tests/doc_tests/conftest.py`の`mock_functions`フィクスチャに追加：

```python
@pytest.fixture
def mock_functions():
    def your_mock_function(param):
        """新しいモック関数"""
        return some_result

    return {
        'get_market_price': get_market_price,
        'your_mock_function': your_mock_function,  # 追加
    }
```

### 自動修正ルールの追加

`tests/doc_tests/fix_documentation_codes.py`に新しい修正ルールを追加：

```python
NEW_FIXES = [
    CodeFix(
        pattern=r'old_pattern',
        replacement='new_pattern',
        description='修正の説明',
        context='適用条件'  # オプション
    ),
]
```

## CI/CD統合

### GitHub Actions設定例

```yaml
name: Documentation Code Test

on:
  pull_request:
    paths:
      - 'docs/**/*.md'
  push:
    branches: [main]

jobs:
  doc-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --group dev

      - name: Test documentation code
        run: |
          uv run pytest tests/doc_tests/ --doc-report -v

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: doc-test-results
          path: |
            doc_test_reports/
            .pytest_cache/
```

## トラブルシューティング

### よくある問題と解決方法

#### ImportError: No module named 'matplotlib'
**症状**: matplotlibが見つからないエラー
**解決**: matplotlibは必須ではありません。自動的にスキップされます。

#### call_price_batch() got an unexpected keyword argument 'k'
**症状**: 古いパラメータ名でエラー
**解決**: 自動修正スクリプトを実行してください：
```bash
python tests/doc_tests/fix_documentation_codes.py docs/ --dry-run
```

#### 'dict' object has no attribute 'delta'
**症状**: greeksの属性アクセスエラー
**解決**: `greeks.delta` を `greeks['delta']` に修正してください。

#### 大量の構文エラー
**症状**: bashコマンドがPythonとして解釈される
**解決**: コードブロックタイプを適切に設定してください：
```markdown
```bash  # pythonではなくbash
pip install quantforge
```
```

### デバッグ方法

#### 特定のコードブロックのみテスト
```bash
# 特定のファイルの特定の行を確認
uv run python -c "
from tests.doc_tests.code_extractor import DocCodeExtractor
blocks = DocCodeExtractor().extract_from_file(Path('docs/ja/quickstart.md'))
for i, block in enumerate(blocks):
    if block.line_number == 70:  # 特定の行
        print(f'Block {i}: {block.code}')
"
```

#### 実行環境のテスト
```bash
# テスト環境を直接確認
uv run python -c "
from tests.doc_tests.conftest import CodeExecutor
from tests.doc_tests.check_doc_codes import SimpleCodeExecutor
executor = SimpleCodeExecutor()
success, output, error = executor.execute('print(\"Hello World\")')
print(f'Success: {success}, Output: {output}, Error: {error}')
"
```

## パフォーマンス指標

### 現在の統計（2025-09-20時点）

```
総コードブロック数: 279
テスト対象: 258 (92.5%)
成功: 124 (48.1%)
エラー: 134 (51.9%)
スキップ: 21 (7.5%)
```

### エラー分布
- 構文エラー: 46.3%（bashコマンドの誤分類など）
- 未定義変数: 23.9%（import不足、コンテキスト依存）
- その他: 29.8%（属性エラー、モジュール不在など）

## 関連リソース

- [システム実装報告書](../../../tests/doc_tests/FINAL_REPORT.md)
- [pytestドキュメント](https://docs.pytest.org/)
- [MyST Markdownガイド](https://myst-parser.readthedocs.io/)
- [Code-block指定方法](https://myst-parser.readthedocs.io/en/latest/syntax/code_and_apis.html)

## 更新履歴

| 日付 | 更新内容 | 担当者 |
|------|----------|--------|
| 2025-09-20 | 初版作成、システム実装完了 | AI Assistant |
| 2025-09-21 | TESTED_PATHS設定とワイルドカードサポートを追加 | AI Assistant |

---

> このガイドは `tests/doc_tests/README.md` と併せてご利用ください。技術的な詳細は実装ファイルのコメントも参照してください。
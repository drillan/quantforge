# ドキュメントコードテストシステム

ドキュメント内のPythonコードサンプルの実行可能性を自動的にテストするシステムです。

## 概要

このテストシステムは、QuantForgeプロジェクトのドキュメント（Markdown形式）からPythonコードブロックを抽出し、実際に実行して動作確認を行います。

## ファイル構成

```
tests/doc_tests/
├── README.md               # このファイル
├── code_extractor.py       # コードブロック抽出ユーティリティ
├── conftest.py            # pytest設定とフィクスチャ
├── test_documentation_code.py  # メインテストファイル
└── check_doc_codes.py     # スタンドアロン統計チェックスクリプト
```

## 使用方法

### 1. pytest経由でテスト実行

```bash
# すべてのドキュメントコードをテスト
pytest tests/doc_tests/ -v

# 特定のドキュメントのみテスト
pytest tests/doc_tests/test_documentation_code.py::TestSpecificDocuments::test_quickstart_examples

# 詳細レポートを生成
pytest tests/doc_tests/ --doc-report

# 特定のファイルのみテスト（フィルター）
pytest tests/doc_tests/ --doc-filter black_scholes
```

### 2. スタンドアロンチェックスクリプト

```bash
# 統計情報を表示（pytest不要）
uv run python tests/doc_tests/check_doc_codes.py

# 特定のファイルを直接チェック
uv run python tests/doc_tests/code_extractor.py docs/ja/quickstart.md
```

## コードブロックの抽出

### 対応フォーマット

1. 単純なコードブロック
```markdown
```python
code here
```
```

2. Sphinxコードブロック
```markdown
```{code-block} python
:name: example-name
:caption: Example Caption
:no-test:  # このオプションがあるとスキップ

code here
```
```

### 自動スキップ条件

以下のパターンを含むコードは自動的にスキップされます：

- `get_market_price()` のような未定義関数
- `plt.show()` や `pyplot.show()` （matplotlib表示）
- `...` （省略記号）
- 実際の市場データ取得関数のプレースホルダー

## テスト環境

テスト実行時には以下の環境が自動的に提供されます：

- QuantForgeモジュール（black_scholes, black76, merton, american）
- NumPy、PyArrow
- モック関数（get_market_price など）
- matplotlib表示の自動無効化

## 現在の統計（2025-09-20時点）

```
総コードブロック数: 279
テスト対象: 258
成功: 107 (41.5%)
失敗: 151
スキップ: 21
```

## 主なエラー原因

1. **APIの不一致**: `k` vs `strikes` パラメータ名
2. **戻り値の型**: greeksが辞書ではなくオブジェクト
3. **構文エラー**: bashコマンドをPythonとして実行
4. **未定義変数**: 前のコードブロックで定義された変数が使えない

## 今後の改善案

- [ ] エラーのあるドキュメントの自動修正
- [ ] CI/CDパイプラインへの統合
- [ ] 実行コンテキストの共有（連続するコードブロック間）
- [ ] 期待値検証の追加
- [ ] エラーレポートの可視化

## トラブルシューティング

### ImportError: No module named 'matplotlib'

matplotlibは必須ではありません。インストールされていない場合は自動的にスキップされます。

### call_price_batch() got an unexpected keyword argument

ドキュメントが古い可能性があります。APIドキュメントの更新が必要です。

## 開発者向け

新しいスキップパターンを追加する場合は、`code_extractor.py`の`SKIP_PATTERNS`リストに正規表現を追加してください。
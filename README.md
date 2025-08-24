# QuantForge

量的金融分析とオプション価格計算のためのライブラリ

## セットアップ

```bash
# 依存関係のインストール
uv sync

# ドキュメント生成用の依存関係をインストール
uv sync --extra docs
```

## ドキュメントのビルド

Sphinxを使用してドキュメントをビルドします：

```bash
uv run sphinx-build -M html docs docs/_build
```

ビルドされたドキュメントは `docs/_build/html/index.html` で確認できます。

## ライセンス

詳細は[LICENSE](LICENSE)ファイルを参照してください。
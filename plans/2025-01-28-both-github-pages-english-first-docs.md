# GitHub Pages 英語優先ドキュメント実装計画

## ステータス
- **作成日**: 2025-01-28
- **ステータス**: DRAFT
- **種別**: 両言語統合（both）
- **重要度**: CRITICAL

## 1. 背景と目的

### 背景
- QuantForgeをグローバルOSSとして成功させるため、英語を第一言語とする
- PyPI公開前に英語ドキュメントを完備する必要がある
- 現在は日本語でドキュメントが作成されているが、ユーザー視点では英語優先が必要

### 目的
- GitHub Pagesで英語をデフォルトパス（`/`）とする
- 日本語をサブディレクトリ（`/ja/`）として配置
- PLaMo-2による自動翻訳システムを活用

### Critical Rules適用
- **C004**: 理想実装ファースト - 最初から多言語対応で公開
- **C014**: 妥協実装禁止 - 段階的移行ではなく完全な形で実装

## 2. 現状分析

### 現在の構造
```
docs/           # 日本語マスター（現状）
docs_en_test/   # 英語テスト（翻訳済み）
translations/   # 翻訳システム
```

### 確認済み事項
- PLaMo-2による翻訳システムが正常動作
- `docs_en_test/user_guide/examples_en.md` の翻訳成功
- MD直接翻訳方式の有効性確認

## 3. 技術仕様

### 3.1 最終的なディレクトリ構造
```
quantforge/
├── README.md              # 英語（デフォルト）
├── README-ja.md          # 日本語
├── docs/                 # ドキュメント管理
│   ├── en/              # 英語版（デフォルトパス）
│   │   ├── conf.py      # language = 'en'
│   │   ├── index.md
│   │   ├── quickstart.md
│   │   ├── installation.md
│   │   ├── api/
│   │   │   └── python/
│   │   ├── user_guide/
│   │   ├── models/
│   │   ├── performance/
│   │   ├── development/
│   │   ├── _build/      # 英語版ビルド出力
│   │   │   └── html/
│   │   ├── _static/     # 英語版静的ファイル
│   │   └── _templates/  # 英語版テンプレート
│   └── ja/              # 日本語版（サブディレクトリ）
│       ├── conf.py      # language = 'ja'
│       ├── index.md
│       ├── quickstart.md
│       ├── installation.md
│       ├── api/
│       │   └── python/
│       ├── user_guide/
│       ├── models/
│       ├── performance/
│       ├── development/
│       ├── _build/      # 日本語版ビルド出力
│       │   └── html/
│       ├── _static/     # 日本語版静的ファイル
│       └── _templates/  # 日本語版テンプレート
├── .github/
│   └── workflows/
│       └── deploy-docs.yml
└── translations/        # プライベート作業領域（.gitignore）
    ├── translate.py     # PLaMo-2翻訳
    ├── glossary.py      # 金融用語辞書
    └── cache/          # 翻訳キャッシュ
```

### 3.2 GitHub Actions設定
```yaml
# .github/workflows/deploy-docs.yml
name: Deploy Documentation to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'docs/source/**'
      - 'translations/**'
      - '.github/workflows/deploy-docs.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: uv sync --extra docs
      
      - name: Build English docs (default)
        run: |
          cd docs/en
          sphinx-build -b html . _build/html
      
      - name: Build Japanese docs
        run: |
          cd docs/ja
          sphinx-build -b html . _build/html
      
      - name: Combine builds for deployment
        run: |
          # 英語版をルートに配置
          cp -r docs/en/_build/html/* docs/_site/
          # 日本語版をサブディレクトリに配置
          cp -r docs/ja/_build/html docs/_site/ja
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./docs/_site
  
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### 3.3 Sphinx設定

#### 英語版 (docs/en/conf.py)
```python
project = 'QuantForge'
copyright = '2025, QuantForge Team'
author = 'QuantForge Team'
release = '0.1.0'

language = 'en'
html_title = 'QuantForge Documentation'

# 言語切り替えナビゲーション
html_theme_options = {
    'navigation_with_keys': True,
    'sticky_navigation': True,
}

html_context = {
    'display_github': True,
    'github_user': 'drillan',
    'github_repo': 'quantforge',
    'github_version': 'main',
    'conf_py_path': '/docs/en/',
    'languages': [
        ('English', '/'),
        ('日本語', '/ja/'),
    ],
    'current_language': 'English',
}

# 静的ファイル
html_static_path = ['_static']
templates_path = ['_templates']
```

#### 日本語版 (docs/ja/conf.py)
```python
project = 'QuantForge'
copyright = '2025, QuantForge Team'
author = 'QuantForge Team'
release = '0.1.0'

language = 'ja'
html_title = 'QuantForge ドキュメント'

html_context = {
    'display_github': True,
    'github_user': 'drillan',
    'github_repo': 'quantforge',
    'github_version': 'main',
    'conf_py_path': '/docs/ja/',
    'languages': [
        ('English', '../'),
        ('日本語', '/ja/'),
    ],
    'current_language': '日本語',
}

# 静的ファイル
html_static_path = ['_static']
templates_path = ['_templates']
```

## 4. 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "docs"
    meaning: "ドキュメントルートディレクトリ"
    source: "プロジェクト標準構造"
  - name: "_build"
    meaning: "ビルド出力ディレクトリ"
    source: "Sphinx標準"
  - name: "_static"
    meaning: "静的ファイルディレクトリ"
    source: "Sphinx標準"
  - name: "_templates"
    meaning: "テンプレートディレクトリ"
    source: "Sphinx標準"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "_site"
    meaning: "GitHub Pages デプロイ用統合サイト"
    justification: "Jekyll/GitHub Pages標準の命名規則"
    status: "pending_approval"
  - name: "en"
    meaning: "英語版ドキュメントディレクトリ"
    justification: "ISO 639-1言語コード標準"
    status: "approved"
  - name: "ja"
    meaning: "日本語版ドキュメントディレクトリ"
    justification: "ISO 639-1言語コード標準"
    status: "approved"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存のディレクトリ構造との整合性確認
- [x] Sphinx標準構造との一致確認
- [x] GitHub Pages要件との適合確認
- [x] 言語コードはISO 639-1準拠（en, ja）

## 5. 実装手順

### Phase 1: ディレクトリ再構成（Day 1）
```bash
# 1. 日本語ディレクトリとして現在のdocsを移動
mv docs docs_ja_temp

# 2. 新しい構造を作成
mkdir -p docs/{en,ja}

# 3. 日本語ドキュメントを配置
mv docs_ja_temp/* docs/ja/
rmdir docs_ja_temp

# 4. 英語版ディレクトリ構造を作成
# ja/の構造をen/にコピー（ファイルは除く）
find docs/ja -type d | sed 's/\/ja/\/en/' | xargs mkdir -p

# 5. テストディレクトリ削除
rm -rf docs_en_test

# 6. 各言語のconf.pyを作成（後述の設定内容を使用）
```

### Phase 2: 翻訳システム更新（Day 2）
```bash
# 1. 翻訳スクリプト更新
# translate.pyのパス設定を更新

# 2. 構造同期スクリプト作成（簡略版）
cat > check_structure.sh << 'EOF'
#!/bin/bash
# 日英のディレクトリ構造を確認
echo "=== Structure Check ==="
echo "Japanese files:"
find docs/ja -name "*.md" | sort
echo ""
echo "English files to be created:"
find docs/ja -name "*.md" | sed 's/\/ja\//\/en\//' | sort
EOF

chmod +x check_structure.sh
```

### Phase 3: 重要ドキュメント翻訳（Day 3-5）
```bash
# 優先度順に翻訳
# 1. README.md（翻訳済み、確認のみ）
# 既に README.md（英語）と README-ja.md（日本語）が存在

# 2. 重要なトップレベルドキュメント
# タイムアウトを考慮してtimeoutコマンドを使用（各30分）
timeout 1800 uv run translations/translate.py \
  docs/ja/index.md \
  docs/en/index.md

timeout 1800 uv run translations/translate.py \
  docs/ja/quickstart.md \
  docs/en/quickstart.md

timeout 1800 uv run translations/translate.py \
  docs/ja/installation.md \
  docs/en/installation.md

# 3. ユーザーガイド（優先度高）
for file in docs/ja/user_guide/*.md; do
  basename=$(basename "$file")
  echo "Translating user_guide/$basename..."
  timeout 1800 uv run translations/translate.py \
    "$file" \
    "docs/en/user_guide/$basename"
done

# 4. API（バッチ処理、タイムアウト設定）
for file in docs/ja/api/python/*.md; do
  basename=$(basename "$file")
  echo "Translating api/python/$basename..."
  timeout 1800 uv run translations/translate.py \
    "$file" \
    "docs/en/api/python/$basename"
done

# 5. その他のドキュメント（優先度低）
# models/, performance/, development/ は後回し
```

### Phase 4: GitHub Pages設定（Day 6）
```bash
# 1. GitHub Actions有効化
cp .github/workflows/deploy-docs.yml .github/workflows/

# 2. GitHub Pages設定
# Repository Settings > Pages > Source: GitHub Actions

# 3. テストデプロイ
git add .
git commit -m "feat(docs): implement English-first GitHub Pages documentation"
git push

# 4. 確認
# https://[username].github.io/quantforge/
# https://[username].github.io/quantforge/ja/
```


## 6. テスト計画

### 6.1 ローカルテスト
```bash
# 英語版ビルド
cd docs/en
sphinx-build -b html . _build/html
python -m http.server -d _build/html 8000
# http://localhost:8000 で確認

# 日本語版ビルド
cd ../ja
sphinx-build -b html . _build/html
python -m http.server -d _build/html 8001
# http://localhost:8001 で確認

# 統合テスト（GitHub Pages形式）
mkdir -p /tmp/test_site
cp -r docs/en/_build/html/* /tmp/test_site/
cp -r docs/ja/_build/html /tmp/test_site/ja
python -m http.server -d /tmp/test_site 8002
# http://localhost:8002 (英語)
# http://localhost:8002/ja/ (日本語)
```

### 6.2 GitHub Pages動作確認
- [ ] 英語版トップページ表示
- [ ] 日本語版サブディレクトリアクセス
- [ ] 言語切り替えリンク動作
- [ ] 静的ファイル（画像、CSS）読み込み
- [ ] 404ページ動作

### 6.3 SEO確認
- [ ] hreflangタグ設定
- [ ] canonicalタグ設定
- [ ] sitemap.xml生成
- [ ] robots.txt配置

## 7. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 翻訳品質の問題 | 高 | 重要部分は人力レビュー |
| ビルド時間超過 | 中 | 並列ビルド、キャッシュ活用 |
| リンク切れ | 中 | リダイレクト設定、404ページ改善 |
| 検索順位低下 | 低 | 301リダイレクト、canonical設定 |

## 8. 成功指標

### 定量指標
- GitHub Pages デプロイ成功
- 両言語のドキュメント100%アクセス可能
- ビルド時間 < 5分
- Lighthouse スコア > 90

### 定性指標
- グローバルユーザーからのポジティブフィードバック
- PyPI公開時の英語圏での採用
- コントリビューター増加

## 9. タイムライン

| Day | タスク | 担当 |
|-----|--------|------|
| 1 | ディレクトリ再構成 | AI |
| 2 | 翻訳システム更新 | AI |
| 3-5 | 重要ドキュメント翻訳 | AI + PLaMo-2 |
| 6 | GitHub Pages設定 | AI |
| 7 | 最終確認・公開 | ユーザー |

## 10. チェックリスト

### 実装前
- [ ] 現在のドキュメントバックアップ
- [ ] GitHub Pages有効化確認
- [ ] 翻訳システム動作確認

### 実装中
- [ ] ディレクトリ構造変更
- [ ] conf.py設定更新
- [ ] GitHub Actions設定
- [ ] 重要ドキュメント翻訳

### 実装後
- [ ] 英語版アクセス確認
- [ ] 日本語版アクセス確認
- [ ] 言語切り替え動作確認
- [ ] PyPIドキュメントリンク更新

## 11. 参考資料

- [GitHub Pages Documentation](https://docs.github.com/pages)
- [Sphinx Internationalization](https://www.sphinx-doc.org/en/master/usage/advanced/intl.html)
- [draft/pypi-english-documentation-priority.md](../draft/pypi-english-documentation-priority.md)
- [plans/2025-01-28-both-md-based-documentation-i18n.md](./2025-01-28-both-md-based-documentation-i18n.md)

---

**次のアクション**: 
1. この計画のレビューとステータス更新（DRAFT → ACTIVE）
2. Phase 1のディレクトリ再構成開始
3. 翻訳システムのパス更新
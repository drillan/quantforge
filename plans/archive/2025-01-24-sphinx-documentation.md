# QuantForge Sphinx ドキュメント作成計画

## メタデータ

- **作成日**: 2025-01-24
- **ステータス**: DRAFT
- **タイプ**: ドキュメント作成計画
- **期間**: 7 日間
- **関連文書**:
  - [実装計画](./2025-01-24-implementation-plan.md)
  - [設計書](../draft/DRAFT-2025-01-24-002-rust-quant-options-engine.md)

## 📚 ドキュメント全体構成

### 1. **プロジェクト基盤ドキュメント**

#### docs/index.md (ランディングページ)

- プロジェクト概要とキーフィーチャー
- パフォーマンス指標（Python 比 500-1000 倍）
- 簡単な使用例
- ドキュメントナビゲーション

#### docs/quickstart.md

- 5 分で始めるガイド
- uv によるインストール
- 最初の Black-Scholes 計算
- 結果の確認

#### docs/installation.md

- システム要件（Python 3.12+、Rust 環境）
- インストール方法（uv 推奨）
- プラットフォーム別の注意事項
- トラブルシューティング

### 2. **ユーザー向けドキュメント**

#### docs/user_guide/index.md

- 基本的な使い方の概要

#### docs/user_guide/basic_usage.md

- Black-Scholes オプション価格計算
- グリークスの取得
- バッチ処理

#### docs/user_guide/advanced_models.md

- アメリカンオプション
- アジアンオプション
- スプレッドオプション

#### docs/user_guide/numpy_integration.md

- NumPy 配列での処理
- ゼロコピー最適化
- パフォーマンステクニック

#### docs/user_guide/examples.md

- 実践的なユースケース
- ポートフォリオ評価
- リスク管理計算

### 3. **API リファレンス**

#### docs/api/python/index.md

- Python API 概要
- 関数シグネチャ一覧

#### docs/api/python/pricing.md

```python
calculate(spots, strikes, rates, vols, times, option_type="call", greeks=False)
black_scholes_call(spot, strike, rate, vol, time)
black_scholes_put(spot, strike, rate, vol, time)
```

#### docs/api/python/implied_vol.md

```python
implied_volatility(price, spot, strike, rate, time, option_type="call")
american_implied_vol(price, spot, strike, rate, time, option_type="call")
```

#### docs/api/rust/index.md

- Rust API（開発者向け）
- SIMD 最適化関数
- 並列処理 API

### 4. **数理モデルドキュメント**

#### docs/models/index.md

- 実装モデル一覧
- 理論的背景

#### docs/models/black_scholes.md

- Black-Scholes モデル理論
- 数式（LaTeX）
- 実装の特徴

#### docs/models/american_options.md

- Bjerksund-Stensland 2002 近似
- 早期行使境界
- グリークス計算手法

#### docs/models/asian_options.md

- 平均価格オプション
- ボラティリティ調整
- 精度と制限事項

### 5. **パフォーマンスドキュメント**

#### docs/performance/benchmarks.md

- ベンチマーク結果
- Python vs Rust 比較
- 競合ライブラリとの比較

#### docs/performance/optimization.md

- SIMD 最適化の効果
- 並列処理戦略
- メモリ最適化

#### docs/performance/tuning.md

- 環境別チューニング
- CPU アーキテクチャ別設定
- バッチサイズ最適化

### 6. **開発者向けドキュメント**

#### docs/development/setup.md

- 開発環境構築
- Rust 環境設定
- PyO3/Maturin セットアップ

#### docs/development/architecture.md

- システムアーキテクチャ
- コンポーネント設計
- データフロー図（Mermaid）

#### docs/development/contributing.md

- コントリビューションガイド
- コーディング規約
- テスト方針

#### docs/development/testing.md

- テスト戦略
- 単体テスト実行
- ベンチマーク実行

### 7. **プロジェクト管理**

#### docs/roadmap.md

- plans/2025-01-24-implementation-plan.md からの自動生成
- 14 週間の実装計画
- 進捗状況

#### docs/changelog.md

- リリースノート
- 破壊的変更
- 新機能追加

#### docs/faq.md

- よくある質問
- トラブルシューティング
- パフォーマンス Q&A

## 🛠️ Sphinx 設定更新

### conf.py の拡張

```python
# 追加する拡張機能
extensions = [
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx.ext.autodoc",        # APIドキュメント自動生成
    "sphinx.ext.napoleon",       # Google/NumPyスタイルdocstring
    "sphinx.ext.viewcode",       # ソースコードリンク
    "sphinx.ext.mathjax",       # 数式表示
    "sphinx_copybutton",        # コードブロックコピーボタン
    "sphinx_tabs.tabs",         # タブ表示
]

# テーマ設定
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False
}

# 言語設定
language = 'ja'  # 日本語対応
```

## 📋 実装手順

### Phase 1: 基本構造（Day 1）

- [ ] docs/ディレクトリ構造作成
- [ ] index.md の充実
- [ ] quickstart.md と installation.md 作成
- [ ] conf.py 更新

### Phase 2: ユーザードキュメント（Day 2-3）

- [ ] user_guide/セクション作成
- [ ] 基本的な使用例作成
- [ ] NumPy 統合ガイド
- [ ] 実践例の追加

### Phase 3: 技術ドキュメント（Day 4-5）

- [ ] 数理モデル説明（LaTeX 数式）
- [ ] API リファレンス骨組み
- [ ] パフォーマンスベンチマーク
- [ ] アーキテクチャ図（Mermaid）

### Phase 4: 開発者ドキュメント（Day 6）

- [ ] 開発環境セットアップガイド
- [ ] コントリビューションガイド
- [ ] テスト戦略

### Phase 5: 自動化と公開（Day 7）

- [ ] GitHub Actions でのビルド自動化
- [ ] Read the Docs 連携
- [ ] バージョン管理設定
- [ ] 検索インデックス最適化

## 🎯 成功基準

- [ ] 全セクションが完成
- [ ] 数式が正しくレンダリング
- [ ] コード例が実行可能
- [ ] API ドキュメント自動生成
- [ ] モバイル対応
- [ ] 検索機能動作
- [ ] 多言語対応（日英）

## 📦 必要なパッケージ

### uv によるインストール

```bash
# uv のインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境作成とパッケージインストール
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Sphinxと拡張機能のインストール
uv pip install sphinx
uv pip install sphinx-rtd-theme
uv pip install myst-parser
uv pip install sphinxcontrib-mermaid
uv pip install sphinx-copybutton
uv pip install sphinx-tabs
```

## 🚀 次のアクション

1. docs/ディレクトリ構造の作成
2. 各 md ファイルのスケルトン作成
3. conf.py の更新
4. 実装計画からの内容移植
5. ローカルビルドとプレビュー

## 📊 進捗トラッキング

### Day 1 (Phase 1)

- [ ] 開始日:
- [ ] 完了日:
- [ ] 進捗: 0%
- [ ] ブロッカー: なし

### Day 2-3 (Phase 2)

- [ ] 開始日:
- [ ] 完了日:
- [ ] 進捗: 0%
- [ ] ブロッカー: なし

### Day 4-5 (Phase 3)

- [ ] 開始日:
- [ ] 完了日:
- [ ] 進捗: 0%
- [ ] ブロッカー: なし

### Day 6 (Phase 4)

- [ ] 開始日:
- [ ] 完了日:
- [ ] 進捗: 0%
- [ ] ブロッカー: なし

### Day 7 (Phase 5)

- [ ] 開始日:
- [ ] 完了日:
- [ ] 進捗: 0%
- [ ] ブロッカー: なし

---

**最終更新**: 2025-01-24
**次回レビュー**: 2025-01-31

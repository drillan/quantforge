# QuantForge ローカル翻訳システム実装計画

**作成日**: 2025-01-28  
**ステータス**: DRAFT  
**言語**: both（翻訳システムとドキュメント）  
**作成者**: AI Assistant

## 1. 目的と背景

### 目的
- PLaMo-2モデルを使用したローカル環境での日本語→英語翻訳システムの構築
- Sphinxドキュメントの構造を完全に保持した翻訳の実現
- GitHub Actions依存から脱却し、開発環境で完結する翻訳ワークフロー

### 背景
- GitHub ActionsでのPLaMo-2実行が不安定（モデルダウンロード問題）
- macOS限定の制約から解放（ローカルx86環境で実行可能）
- 翻訳品質は実証済み（PLaMo-2-translate-Q3_K_M.ggufで高品質な翻訳を確認）

## 2. 技術要件

### 必須要件
- MyST Markdown形式の完全な構造保持
- 数式（LaTeX）、表、Sphinxディレクティブの保護
- 日本語部分のみの選択的翻訳
- ビルド可能な出力の生成

### 性能要件
- 単一ファイル（index.md）: 5分以内
- 全ドキュメント: 1時間以内
- 差分翻訳サポート（変更部分のみ）

## 3. アーキテクチャ

### ディレクトリ構造
```
quantforge/
├── docs/                    # 本番ドキュメント（日本語）
├── docs_test/              # テスト環境（.gitignore）
│   ├── conf.py             # 簡略化された設定
│   ├── source/             # テスト用ドキュメント
│   │   ├── index.md        # 総合テスト
│   │   ├── math_heavy.md  # 数式テスト
│   │   ├── api_sample.md   # API形式テスト
│   │   └── complex_table.md # 表テスト
│   └── _build/             # ビルド結果
└── translations/           # 翻訳システム（.gitignore）
    ├── setup.sh            # 環境セットアップ
    ├── translate.py        # メイン翻訳スクリプト
    ├── glossary.py         # 金融用語集
    ├── config.json         # 設定ファイル
    ├── models/             # GGUFモデル置き場
    └── cache/              # 翻訳キャッシュ
```

## 4. 命名定義

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "spot"
    meaning: "現在価格"
    source: "naming_conventions.md#APIパラメータ"
  - name: "strike"
    meaning: "権利行使価格"
    source: "naming_conventions.md#APIパラメータ"
  - name: "volatility"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#金融用語"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "translation_unit"
    meaning: "翻訳の最小単位（段落、見出し等）"
    justification: "gettext/POファイルの業界標準"
    references: "GNU gettext documentation"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] 金融用語の統一（QuantForge固有用語集）
- [x] エラーメッセージでもAPI名を使用

## 5. 実装計画

### フェーズ1: テスト環境構築（1日）
1. docs_test/ディレクトリ作成
2. 最小限のSphinx設定（conf.py, Makefile）
3. テストドキュメント4ファイル作成
4. .gitignore更新

### フェーズ2: 翻訳システム移植（1日）
1. /home/driller/work/quantforge-translationから必要ファイルをコピー
2. 相対パス化とプロジェクト内動作の確認
3. 用語集（glossary.py）の作成
4. 設定ファイル（config.json）の実装

### フェーズ3: 構造保持アルゴリズム実装（2日）
1. MyST/Markdown構造のパース
2. 翻訳対象部分の抽出
3. 保護領域の識別（数式、コードブロック、ディレクティブ）
4. 翻訳後の再構築

### フェーズ4: テストと検証（1日）
1. docs_test/での翻訳実行
2. Sphinxビルドの成功確認
3. 数式レンダリング検証
4. 表構造の確認

### フェーズ5: 最適化（1日）
1. キャッシュシステム実装
2. 差分検出アルゴリズム
3. バッチ処理の並列化

## 6. テスト戦略

### 単体テスト
- 翻訳単位の抽出テスト
- 構造保持のテスト
- 用語集マッチングテスト

### 統合テスト
- docs_test/全ファイルの翻訳
- ビルド成功の確認
- HTML出力の視覚的検証

### 検証項目チェックリスト
- [ ] Sphinxビルドエラーなし
- [ ] 数式が正しくレンダリング
- [ ] 表構造が維持されている
- [ ] Sphinxディレクティブが機能
- [ ] 相互参照が有効
- [ ] コードブロック内の日本語コメントが保護

## 7. リスクと対策

### リスク1: 翻訳品質のばらつき
**対策**: 用語集による標準化、人間によるレビュー

### リスク2: 構造破壊によるビルドエラー
**対策**: docs_test/での事前検証、段階的適用

### リスク3: 処理時間の増大
**対策**: キャッシュシステム、差分翻訳、並列処理

## 8. 成功基準

- docs_test/の4ファイルすべてが翻訳後もビルド可能
- 翻訳時間が目標以内（index.md: 5分以内）
- 数式、表、ディレクティブの100%保護
- 用語の一貫性90%以上

## 9. 将来の拡張

- GitHub Actions統合（安定化後）
- 多言語対応（中国語、韓国語）
- 翻訳メモリの実装
- Web UIの提供

## 10. 参考資料

- [PLaMo-2 Documentation](https://github.com/pfnet/plamo-2)
- [llama.cpp PR #14560](https://github.com/ggerganov/llama.cpp/pull/14560)
- [Sphinx Internationalization](https://www.sphinx-doc.org/en/master/usage/advanced/intl.html)
- [MyST Parser Documentation](https://myst-parser.readthedocs.io/)
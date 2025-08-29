# MyST記法による日英ドキュメント構造比較システム実装計画

## ステータス: ACTIVE

## 概要
MyST記法のname属性を利用した言語横断的なドキュメント構造比較システムの実装（ローカル実行専用）

## 背景と目的
- **問題**: 日本語先行でドキュメントが作成され、英訳の同期管理が困難
- **解決策**: MyST記法のname属性による構造的な対応関係の管理
- **運用方針**: ローカルでの差分チェックと手動でのドキュメント修正

## 実装内容

### フェーズ1: MyST記法の導入（1週間）

1. **既存ドキュメントへのname属性追加**
   - `scripts/add_myst_names.py` の作成
   - 命名規則: `{file-basename}-{section-slug}`
   - 優先対象: models/, api/python/ ディレクトリ

2. **MyST記法ガイドライン作成**
   - `docs/internal/myst_naming_guidelines.md`
   - name属性の命名規則
   - caption属性の記述方法

### フェーズ2: 構造比較ツール実装（1週間）

1. **コア比較エンジン**
   ```
   translations/structure_compare/
   ├── __init__.py
   ├── parser.py          # MyST文書パーサー
   ├── comparator.py      # 構造比較ロジック
   └── reporter.py        # レポート生成
   ```

2. **主要機能**
   - docutilsによるAST解析
   - name属性ベースのマッチング
   - CSV/JSON形式での差分出力
   - HTMLレポート生成（視覚的な確認用）

3. **比較対象要素**
   - ヘッダー (sections)
   - コードブロック (code-block)
   - 数式 (math)
   - 表 (list-table)
   - 図 (figure)

### フェーズ3: ローカル実行環境（3日）

1. **CLIツール**
   ```bash
   # 単一ファイル比較
   python translations/structure_compare.py \
     --ja docs/ja/models/black_scholes.md \
     --en docs/en/models/black_scholes.md \
     --output reports/black_scholes_diff.csv
   ```

2. **バッチ処理スクリプト**
   ```bash
   # 全ドキュメント一括チェック
   ./scripts/check_all_doc_structures.sh
   
   # 出力例:
   # reports/
   # ├── structure_diff_summary.html
   # ├── models/
   # │   ├── black_scholes.csv
   # │   └── merton.csv
   # └── api/
   #     └── python/
   #         └── pricing.csv
   ```

3. **差分レポートの形式**
   ```csv
   type,name,ja_text,en_text,status
   header,black-scholes-intro,"Black-Scholesモデル","Black-Scholes Model",ok
   code-block,call_price_example,"コール価格の計算例",,missing
   table,greeks-table,"グリークスの定義","Greeks Definition",outdated
   ```

## 使用方法

1. **初回セットアップ**
   ```bash
   # MyST name属性の一括追加
   python scripts/add_myst_names.py --dir docs/ja
   python scripts/add_myst_names.py --dir docs/en
   ```

2. **日常的な差分チェック**
   ```bash
   # 全体チェック
   ./scripts/check_all_doc_structures.sh
   
   # レポート確認
   open reports/structure_diff_summary.html
   ```

3. **手動修正フロー**
   - CSVレポートで差分箇所を確認
   - 対応する英語ドキュメントを手動編集
   - 再度スクリプトを実行して確認

## 命名定義

### 使用する既存命名
```yaml
existing_names:
  - name: "myst_parser"
    meaning: "MyST Parser"
    source: "docs/ja/conf.py#extensions"
  - name: "docutils"
    meaning: "Document utilities"
    source: "Python標準ドキュメント処理"
```

### 新規提案命名
```yaml
proposed_names:
  - name: "structure_compare"
    meaning: "構造比較モジュール"
    justification: "機能を明確に表現"
    status: "pending_approval"
  
  - name: "myst_name"
    meaning: "MyST記法のname属性"
    justification: "MyST公式仕様に準拠"
    status: "pending_approval"
```

## 成功基準
- [ ] 全モデルドキュメントにname属性付与
- [ ] 構造差分の自動検出（手動確認用）
- [ ] CSV/HTML形式での差分レポート生成
- [ ] 翻訳更新箇所の明確な特定

## リスクと対策
- **リスク**: 既存ドキュメントの大規模変更
- **対策**: 段階的導入、通常Markdownとの共存、gitでの変更追跡

## 実装ファイル一覧

**新規作成**:
- `scripts/add_myst_names.py` - name属性自動付与スクリプト
- `translations/structure_compare/` - 構造比較モジュール
- `docs/internal/myst_naming_guidelines.md` - 命名ガイドライン
- `scripts/check_all_doc_structures.sh` - 一括チェックスクリプト
- `translations/reports/` - レポート出力ディレクトリ

**変更対象**:
- `docs/ja/**/*.md` - name属性追加
- `docs/en/**/*.md` - name属性追加（対応する日本語と同じname）

## 次のステップ
1. MyST記法の命名規則確定
2. add_myst_names.py スクリプトの実装
3. パイロット実装（black_scholes.md で試行）
4. 構造比較ツールの実装
5. 全ドキュメントへの展開

## 実装開始日
2025-01-29
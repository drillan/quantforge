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
   - `docs/ja/internal/myst_naming_guidelines.md`
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

**実装済み**:
- ✅ `translations/myst/add_names.py` - name属性自動付与スクリプト
- ✅ `translations/compare/structure_compare.py` - 構造比較モジュール（v1.1.0：メタデータ・階層情報実装済み）
- ✅ `translations/compare/check_all.sh` - 一括チェックスクリプト
- ✅ `translations/compare/reports/` - レポート出力ディレクトリ
- ✅ `translations/compare/PROMPT.md` - 構造確認用プロンプト集
- ✅ `translations/compare/README.md` - 構造比較ツール使用ガイド
- ✅ `translations/README.md` - 翻訳ツール統合ドキュメント
- ✅ `docs/ja/internal/myst_naming_guidelines.md` - 命名ガイドライン

**部分実装（要改善）**:
- ⚠️ `docs/ja/**/*.md` - name属性追加（models/の一部のみ完了）
- ⚠️ `docs/en/**/*.md` - name属性追加（models/の一部のみ完了）

**未実装**:
- `translations/compare/auto_fix.py` - 自動修正ツール

## 実装進捗と課題

### 完了項目
1. ✅ translations/配下への統合再編成完了
2. ✅ 構造比較ツール基本実装完了
3. ✅ models/配下の主要ファイルへのMyST記法追加
4. ✅ 構造比較レポート生成機能実装

### 発見された課題
1. **name属性の不一致**: 日英間で異なるname属性が使用されている
   - 例: `black-scholes-analytical-solution` vs `black-scholes-solutions`
2. **構造の相違**: セクション階層が日英で異なる箇所がある
3. **JSONレポートの改善必要性**:
   - ファイルパス情報の欠如
   - ヘッダー階層情報の欠如
   - 親子関係の表現不足

## 次のステップ
1. ✅ ~~MyST記法の命名規則確定~~
2. ✅ ~~add_myst_names.py スクリプトの実装~~
3. ✅ ~~パイロット実装（black_scholes.md で試行）~~
4. ✅ ~~構造比較ツールの基本実装~~
5. 🔄 構造比較ツールの改善（メタデータ追加、階層情報追加）
6. 📝 name属性の統一化作業
7. 🔧 auto_fix.py の実装
8. 📚 全ドキュメントへの展開

## structure_compare.py 改善計画

### 現在の課題
1. **メタデータ不足**
   - 比較対象ファイルのパスが記録されていない
   - 実行時刻が記録されていない
   - ツールバージョンが不明

2. **構造情報の不足**
   - ヘッダーレベル（#, ##, ###）が記録されていない
   - 要素の親子関係が表現されていない
   - 文書の階層構造が平坦化されている

3. **修正支援機能の不足**
   - どのように修正すべきかの提案がない
   - 優先度の指定がない

### 改善実装案

#### JSONレポート構造の拡張
```json
{
  "metadata": {
    "timestamp": "2025-01-29T10:00:00",
    "ja_file": "docs/ja/models/black_scholes.md",
    "en_file": "docs/en/models/black_scholes.md",
    "tool_version": "1.1.0",
    "comparison_mode": "name-based"
  },
  "summary": {
    "total_elements": {"ja": 37, "en": 39},
    "matched": 21,
    "issues": {
      "missing_in_en": 16,
      "missing_in_ja": 18,
      "type_mismatch": 0,
      "caption_diff": 0
    },
    "sync_rate": 56.7,
    "severity": "high"  // low, medium, high based on sync_rate
  },
  "structure": {
    "ja_tree": { /* 階層構造 */ },
    "en_tree": { /* 階層構造 */ }
  },
  "elements": {
    "matched": [
      {
        "name": "black-scholes",
        "type": "header",
        "level": 1,  // 新規追加
        "parent": null,  // 新規追加
        "children": ["black-scholes-theory", ...],  // 新規追加
        "ja_caption": "Black-Scholesモデル",
        "en_caption": "Black-Scholes Model",
        "ja_line": 1,
        "en_line": 1
      }
    ],
    "missing_in_en": [
      {
        "name": "black-scholes-analytical-solution",
        "type": "header",
        "level": 3,
        "parent": "black-scholes-derivation",
        "caption": "解析解",
        "line": 63,
        "suggestion": "Add section 'Analytical Solutions' under 'Derivation of Pricing Formula'"
      }
    ]
  },
  "recommendations": [
    {
      "priority": "high",
      "action": "add_missing_sections",
      "target": "en",
      "count": 16,
      "details": "Add missing sections to English documentation"
    }
  ]
}
```

#### 実装タスク
1. ヘッダーレベル検出機能の追加
2. 親子関係構築ロジックの実装
3. メタデータセクションの追加
4. 修正提案生成機能の追加
5. 階層構造ビューの生成

## 実装開始日
2025-01-29
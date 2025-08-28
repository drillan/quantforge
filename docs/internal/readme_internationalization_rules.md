# README国際化統一ルール

このドキュメントは、QuantForgeプロジェクトのREADMEファイル（README.mdとREADME-ja.md）の国際化における統一ルールを定義します。

## 1. 基本原則

### 1.1 構造的整合性
- 両言語版のセクション構造は完全に一致させる
- セクションの追加・削除は必ず両方同時に実施
- 順序も統一（文化的な読みやすさより構造的一貫性を優先）

### 1.2 内容の同等性
- 技術的情報は完全に同一
- パフォーマンス数値、バージョン情報、コマンドは必ず同期
- 言語固有の表現は許容するが、伝える情報は同じ

### 1.3 メンテナンス原則
- 片方のみの更新は禁止
- 更新時は両言語版の差分を必ず確認
- 同期チェックツールの活用を推奨

## 2. 構造的整合性ルール

### 2.1 必須セクション（両言語共通）

以下のセクションは両言語版に必須：

| セクション名（英語） | セクション名（日本語） | 内容 |
|---------------------|----------------------|------|
| Performance Metrics | パフォーマンス測定結果 | 最新のベンチマーク結果 |
| Features and Capabilities | 機能と実装 | 主要機能の説明 |
| Installation | インストール | インストール手順 |
| Quick Start | クイックスタート | 基本的な使用例 |
| Development | 開発環境セットアップ | 開発者向け情報 |
| Documentation | ドキュメント | ドキュメントへのリンク |
| Roadmap | ロードマップ | 開発計画 |
| Contributing | コントリビューション | 貢献方法 |
| License | ライセンス | ライセンス情報 |
| Acknowledgments | 謝辞 | 使用ツールへの謝辞 |

### 2.2 オプションセクション

以下は言語固有で存在可能：
- 文化的な説明や例示
- 言語固有のリソースへのリンク
- ローカルコミュニティ情報

ただし、主要な技術情報は必ず両方に記載。

## 3. 同期管理プロトコル

### 3.1 即時同期が必要な要素

以下の要素は変更時に即座に両言語版を更新：

```yaml
critical_sync_elements:
  - performance_metrics:
      - benchmark_results
      - measurement_date
      - test_environment
  - version_info:
      - library_version
      - dependency_versions
      - rust_version
      - python_version
  - code_samples:
      - api_examples
      - installation_commands
      - build_commands
  - technical_specs:
      - supported_models
      - feature_list
      - system_requirements
```

### 3.2 許容される差異

```yaml
allowed_differences:
  - language_style:
      - formality_level  # 敬語 vs カジュアル
      - sentence_structure
      - paragraph_flow
  - cultural_adaptation:
      - currency_examples  # USD vs JPY
      - date_formats
      - name_examples
  - external_links:
      - documentation_language  # 英語/日本語ドキュメント
      - community_resources
```

## 4. メンテナンスプロセス

### 4.1 更新時のチェックリスト

README更新時は以下を必ず確認：

```markdown
## PR提出前チェックリスト
- [ ] 両言語版を同時に更新した
- [ ] セクション構造が一致している
- [ ] パフォーマンス数値が同一
- [ ] コードサンプルが一致
- [ ] バージョン情報が同期されている
- [ ] コマンド例が同じ
- [ ] check_readme_sync.pyを実行して確認した（実装済みの場合）
```

### 4.2 レビュープロセス

1. **PR作成時**
   - タイトルに `[README-SYNC]` プレフィックスを付ける
   - 両言語版の変更内容を明記
   - 同期チェック結果を添付（ツール実装済みの場合）

2. **レビュー時**
   - レビュワーは両言語版を確認
   - 構造的一致を検証
   - 内容の同等性を確認

3. **マージ条件**
   - 両言語版が同時に更新されている
   - 同期チェックがパスしている（ツール実装済みの場合）
   - レビュワーの承認

## 5. 自動化ツール仕様

### 5.1 同期チェックスクリプト要件

**ファイル**: `scripts/check_readme_sync.py`

#### 基本機能要件

```python
"""
README同期チェッカー仕様

目的: README.mdとREADME-ja.mdの同期状態を検証

主要機能:
1. 構造比較
   - セクション見出しの抽出と比較
   - ネストレベルの一致確認
   - 順序の検証

2. 内容同期確認
   - パフォーマンス数値の抽出と比較
   - バージョン番号の一致確認
   - コードブロックの同一性確認

3. レポート生成
   - 不一致箇所の詳細リスト
   - 修正提案の生成
   - CI/CD用の終了コード

使用例:
  python scripts/check_readme_sync.py
  python scripts/check_readme_sync.py --strict  # 厳格モード
  python scripts/check_readme_sync.py --fix     # 自動修正提案
"""
```

#### インターフェース仕様

```python
class ReadmeSyncChecker:
    """README同期チェッカーのインターフェース"""
    
    def __init__(self, en_path="README.md", ja_path="README-ja.md"):
        """
        Args:
            en_path: 英語版READMEのパス
            ja_path: 日本語版READMEのパス
        """
        self.en_path = en_path
        self.ja_path = ja_path
    
    def check_structure(self) -> bool:
        """セクション構造の比較
        
        Returns:
            構造が一致する場合True
        """
        pass
    
    def check_metrics(self) -> bool:
        """数値データの同期確認
        
        Returns:
            数値が一致する場合True
        """
        pass
    
    def check_code_blocks(self) -> bool:
        """コードサンプルの一致確認
        
        Returns:
            コードブロックが一致する場合True
        """
        pass
    
    def generate_report(self) -> dict:
        """不一致レポートの生成
        
        Returns:
            レポートデータ（JSON形式）
        """
        pass
```

#### 出力形式仕様

```json
{
  "status": "passed|failed",
  "structure_match": true|false,
  "content_sync": {
    "performance_metrics": true|false,
    "version_info": true|false,
    "code_samples": true|false
  },
  "issues": [
    {
      "type": "issue_type",
      "language": "en|ja",
      "section": "section_name",
      "suggestion": "fix_suggestion"
    }
  ]
}
```

## 6. 参照文書

- [`documentation_refactoring_rules.md`](./documentation_refactoring_rules.md) - ドキュメント全般のリファクタリングルール
- [`naming_conventions.md`](./naming_conventions.md) - 命名規則と用語の統一
- [`plans/2025-08-28-readme-sync-implementation.md`](../../plans/2025-08-28-readme-sync-implementation.md) - 現在の不整合解消と実装計画

## 付録A: よくある質問

### Q: なぜgettext形式を使わないのか？
A: READMEは頻繁に更新され、GitHub上で直接閲覧されることが多いため、独立ファイルの方が管理しやすく、コントリビューターにとっても編集が容易です。

### Q: 新しい言語を追加する場合は？
A: まず英語版を基準として翻訳し、このルールに従って同期を保ちます。3言語以上になった場合は、gettext形式への移行を再検討します。

### Q: 技術的詳細はどこまでREADMEに含めるべき？
A: READMEは「最初の5分」のための文書です。詳細な技術情報はdocsディレクトリに配置し、READMEからリンクします。

### Q: セクションの順序は厳密に守る必要があるか？
A: はい。構造的一貫性を保つため、両言語版で同じ順序を維持します。これにより、メンテナンスが容易になり、自動チェックも実装しやすくなります。

### Q: 言語固有の表現はどこまで許容される？
A: 文体や敬語レベルは言語に応じて調整可能ですが、技術的な内容や情報の粒度は同一にします。例えば、英語版で3つの特徴を挙げたら、日本語版でも同じ3つを記載します。

## 付録B: テンプレート

### 新セクション追加時のテンプレート

```markdown
<!-- README.md -->
## New Section Title

Content in English...

<!-- README-ja.md -->
## 新セクションタイトル

日本語のコンテンツ...
```

### 同期コミットメッセージテンプレート

```
docs: sync README sections between en/ja

- Add/Update [section name] in README.md
- Add/Update [section name] in README-ja.md
- Ensure [specific metrics/code] are aligned

[README-SYNC]
```

### PR説明テンプレート

```markdown
## README Synchronization Update

### Changes
- [ ] README.md updated
- [ ] README-ja.md updated
- [ ] Structure aligned
- [ ] Content synchronized

### Sync Check Results
```
[Paste check_readme_sync.py output here if available]
```

### Reviewer Checklist
- [ ] Both language versions updated
- [ ] Section structure matches
- [ ] Technical information identical
- [ ] Code samples consistent
```
# README同期実装計画

## 実施日
2025-08-28

## 目的
README.mdとREADME-ja.mdの構造的不整合を解消し、継続的な同期管理体制を確立する。

## 関連文書
- [`docs/internal/readme_internationalization_rules.md`](../docs/internal/readme_internationalization_rules.md) - 恒久的な統一ルール定義

## 1. 現在の不整合状態（2025-08-28時点）

### 1.1 構造的不整合

| セクション | 英語版 | 日本語版 | 対応方針 | 優先度 |
|-----------|---------|----------|----------|--------|
| Overview / 概要 | なし | あり | 英語版に追加 | 高 |
| Implementation Details | あり | なし | 日本語版に追加 | 高 |
| Use Cases | あり | なし | 日本語版に追加 | 中 |
| Contact | あり | なし | 日本語版に追加 | 低 |
| 実装済み機能 | なし | あり | Featuresに統合 | 高 |
| QuantForgeが高速な理由 / Why QuantForge is Fast | なし | あり | 英語版に追加 | 中 |

### 1.2 内容的不整合

- パフォーマンス数値の表記形式が微妙に異なる
- コードサンプルのコメント言語が混在
- 測定環境の記載粒度が不一致

## 2. 解決スケジュール

### Phase 1: 緊急対応（1週間以内）
**完了期限**: 2025-08-04

- [ ] 英語版にOverviewセクション追加
  - 簡潔な概要（3-5文）
  - 主要な価値提案の明記
- [ ] 日本語版にImplementation Detailsセクション追加
  - Mathematical Foundationの翻訳
  - Architectureの翻訳
  - Validationの翻訳
- [ ] 「実装済み機能」をFeaturesセクションに統合
  - 重複内容の削除
  - 構造の統一

### Phase 2: 標準化（2週間以内）
**完了期限**: 2025-08-11

- [ ] 両言語版に"Why Fast"セクション追加
  - 英語版: "Why QuantForge is Fast"
  - 日本語版: 既存の内容を整理
  - 5つの要因に統一（Rust、最適化、並列化、ゼロコピー、数学関数）
- [ ] Use Casesセクションを日本語版に追加
  - High-Frequency Trading
  - Risk Management
  - Backtesting
  - Research
- [ ] Contactセクションを日本語版に追加
  - Issues、Discussions、Security

### Phase 3: 最適化（1ヶ月以内）
**完了期限**: 2025-08-28

- [ ] 重複内容の整理
  - Featuresと実装済み機能の統合完了
  - 冗長な説明の削減
- [ ] 技術的詳細の適切な配置
  - READMEからdocsへの移動検討
  - 参照リンクの追加
- [ ] 読みやすさの向上
  - セクション長の最適化
  - 視覚的な整理（表、リストの統一）

## 3. CI/CD統合計画

### 3.1 GitHub Actions設定

**ファイル**: `.github/workflows/readme-sync.yml`

```yaml
name: README Sync Check

on:
  pull_request:
    paths:
      - 'README*.md'

jobs:
  sync-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pyyaml markdown
      
      - name: Check README synchronization
        run: |
          python scripts/check_readme_sync.py --ci
      
      - name: Upload sync report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: sync-report
          path: sync_report.json
      
      - name: Comment PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('sync_report.json', 'utf8'));
            const issues = report.issues.map(i => `- ${i.type}: ${i.section}`).join('\n');
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `⚠️ README synchronization check failed.\n\n**Issues found:**\n${issues}\n\nPlease ensure both README.md and README-ja.md are updated consistently.`
            })
```

### 3.2 実装ステップ

1. **スクリプト実装**（1週目）
   - 基本的な構造比較機能
   - 数値データ抽出機能
   - レポート生成機能

2. **CI統合**（2週目）
   - GitHub Actionsワークフロー作成
   - PR自動チェック設定
   - レポート生成と通知

3. **改善と最適化**（3週目）
   - 誤検知の調整
   - パフォーマンス最適化
   - ユーザビリティ向上

## 4. 将来の国際化戦略

### 4.1 短期戦略（現在〜3ヶ月）

**アプローチ**: 独立ファイル管理の最適化

- README.md と README-ja.md を個別管理継続
- 手動同期プロセスの確立
- 自動チェックツールによる品質保証

**マイルストーン**:
- 月1: 不整合解消完了
- 月2: 自動チェックツール稼働
- 月3: CI/CD完全統合

### 4.2 中期戦略（3〜6ヶ月）

**アプローチ**: Sphinx i18n導入後の整合性確保

前提条件:
- Sphinx国際化設定完了（draft/sphinx-i18n.md参照）
- docsディレクトリのgettext化

実施項目:
- READMEとdocsの役割分担明確化
  - README: クイックスタート、基本情報
  - docs: 詳細な技術文書
- 共通部分のテンプレート化検討
- 重複コンテンツの削減

### 4.3 長期戦略（6ヶ月以降）

**判断基準による条件付き実施**:

gettext形式への移行検討条件:
- コントリビューター数が10人以上
- 3言語以上のサポート要求
- メンテナンス負荷が許容範囲を超える

多言語展開の検討:
- 中国語（簡体字）
- 韓国語
- その他需要に応じて

## 5. 自動チェックスクリプト実装詳細

### 5.1 実装優先順位

1. **必須機能**（Phase 1）
   - セクション構造の比較
   - 基本的なレポート生成
   - CI用終了コード

2. **重要機能**（Phase 2）
   - パフォーマンス数値の抽出と比較
   - コードブロックの比較
   - 詳細なレポート生成

3. **追加機能**（Phase 3）
   - 自動修正提案
   - 差分の視覚化
   - 翻訳メモリ機能

### 5.2 技術スタック

```python
# requirements.txt
pyyaml>=6.0
markdown>=3.4
click>=8.0  # CLI framework
colorama>=0.4  # Color output
jinja2>=3.0  # Report generation
```

## 6. 成功指標

### 定量的指標
- [ ] 構造的不整合: 0件
- [ ] CI/CDチェック成功率: 100%
- [ ] 同期更新の遵守率: 100%

### 定性的指標
- [ ] メンテナンス負荷の軽減
- [ ] コントリビューターからのフィードバック改善
- [ ] ドキュメント品質の向上

## 7. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 自動チェックの誤検知 | 中 | 段階的な導入とチューニング |
| メンテナンス負荷増大 | 高 | テンプレート化と自動化の推進 |
| コントリビューターの混乱 | 中 | 明確なガイドラインとテンプレート提供 |

## 8. 完了基準

- [ ] すべての構造的不整合が解消
- [ ] 自動チェックスクリプトが実装・稼働
- [ ] CI/CDパイプラインが設定・稼働
- [ ] ドキュメントとテンプレートが整備
- [ ] チーム全体への周知完了

## 9. 次のアクション

1. **即座に実施**
   - 英語版READMEにOverviewセクション追加
   - 日本語版READMEにImplementation Details追加

2. **今週中に実施**
   - check_readme_sync.pyの基本実装
   - 「実装済み機能」の統合

3. **来週以降**
   - CI/CD統合
   - 残りの不整合解消

---

## 改訂履歴

- 2025-08-28: 初版作成 - 現在の不整合を文書化し、実装計画を策定
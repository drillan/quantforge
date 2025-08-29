# QuantForge 計画管理

このディレクトリには、プロジェクトの各種計画文書を管理します。

## ⚠️ 重要な警告

**このディレクトリの文書は実装の参照用ではありません。**

- 計画文書は「一時的な設計スペース」です
- 仕様変更履歴や誤った実装の修正記録を含みます
- **実装時は必ず docs/api/ のドキュメントを参照してください**
- 計画文書を真実の源として扱うと、過去の誤りを繰り返す危険があります

---

## 📊 現在の状況を確認する方法

- **アクティブな計画**: `ls plans/*.md` でREADME.mdとCHANGELOG.md以外のファイルを確認
- **完了した計画**: `ls plans/archive/` でアーカイブ済みの計画を確認  
- **変更履歴**: [CHANGELOG.md](./CHANGELOG.md) で詳細な変更履歴を参照

### 最近完了した計画
| 計画名 | 完了日 | 成果 |
|--------|--------|------|
| [README.md同期実装](archive/2025-08-28-readme-sync-implementation.md) | 2025-08-29 | プロジェクト現状の正確な反映（v0.0.2） |
| [Pythonモジュール修正](archive/2025-08-28-python-fix-module-import-api.md) | 2025-08-29 | インポート問題の完全解決、mypy対応 |
| [GitHub Pages英語ドキュメント](archive/2025-01-28-both-github-pages-english-first-docs.md) | 2025-08-29 | MkDocs + CI/CD自動デプロイ |

## 📁 ディレクトリ構造

```
plans/
├── README.md                           # このファイル（警告含む）
├── YYYY-MM-DD-<lang>-<title>.md       # アクティブな計画（設計中）
├── templates/                          # 計画テンプレート
│   ├── rust/                          # Rust用テンプレート
│   │   └── implementation-plan.md     # Rust実装計画
│   └── python/                        # Python用テンプレート
│       └── implementation-plan.md     # Python実装計画
└── archive/                            # 完了計画（参照禁止）
    └── ⚠️ 過去の仕様変更・誤った実装を含む
```

**重要**: archive/内の文書は歴史的記録です。実装の参考にしないでください。

## 🏷️ ステータス定義

- **DRAFT**: 作成中
- **REVIEW**: レビュー中  
- **ACTIVE**: 実行中
- **COMPLETED**: 完了
- **CANCELLED**: 中止
- **ARCHIVED**: アーカイブ済み

## 📝 命名規則

```
YYYY-MM-DD-<lang>-<type>-<title>.md

言語プレフィックス:
- rust-    : Rust実装
- python-  : Python実装  
- both-    : 両言語統合

例:
2025-08-26-rust-implementation-greeks.md      # Rust実装
2025-08-26-python-implementation-api.md       # Python実装
2025-08-26-both-integration-testing.md        # 両言語統合
```

## 🔄 計画の作成プロセス

### 計画文書の役割と制限

**役割**: 一時的な設計スペース
- 新機能の検討と議論
- 技術的課題の整理
- 実装方針の策定

**制限事項**:
- ドキュメント（docs/）化されるまでは仕様ではない
- 過去の計画は参照しない（誤謬のリスク）
- 実装の根拠にしない

**ライフサイクル**:
1. **DRAFT**: 設計検討中
2. **ACTIVE**: 実装方針決定
3. **ドキュメント化**: docs/api/へ正式仕様として記載
4. **COMPLETED**: 役割終了、archive/へ移動
5. **以降参照禁止**: 過去の記録として保管のみ

### 計画文書の必須セクション

#### 4. 命名定義セクション
新機能の計画では以下を必ず記載：

##### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間"
    source: "naming_conventions.md#共通パラメータ"
```

##### 4.2 新規提案命名（必要な場合）
```yaml
proposed_names:
  - name: "kappa"
    meaning: "mean reversion rate"
    justification: "Heston modelで業界標準"
    references: "Heston (1993) Review of Financial Studies"
    status: "pending_approval"
```

##### 4.3 命名の一貫性チェックリスト
- [ ] 既存モデルとの整合性確認
- [ ] naming_conventions.mdとの一致確認
- [ ] ドキュメントでの使用方法定義
- [ ] APIパラメータは省略形を使用
- [ ] エラーメッセージでもAPI名を使用

#### 命名に関する注意事項
- **必ず** `docs/internal/naming_conventions.md` を参照
- **カタログにない命名は事前承認が必要**
- **独自判断での命名は技術的負債**

### 言語別テンプレートの使用

#### Rust実装の場合
```bash
cp templates/rust/implementation-plan.md 2025-MM-DD-rust-feature-name.md
```
- 品質管理: `.claude/commands/rust-quality-check.md`, `.claude/commands/rust-refactor.md`
- ツール: cargo, clippy, similarity-rs

#### Python実装の場合
```bash
cp templates/python/implementation-plan.md 2025-MM-DD-python-feature-name.md
```
- 品質管理: python-quality-check.md, python-refactor.md（今後作成）
- ツール: pytest, ruff, mypy

### ワークフロー
1. **テンプレート選択**: 言語に応じたテンプレートをコピー
2. **規模判定**: テンプレート内の判定基準で自動判定
3. **ステータス**: DRAFTから開始
4. **実行**: ACTIVEステータスで実行開始
5. **完了**: COMPLETEDマーク後、archive/へ移動

## 🎯 品質管理ツールの言語別適用基準

### Rust
| タスク規模 | cargo test/clippy | similarity-rs | rust-refactor.md |
|-----------|------------------|---------------|-----------------|
| 小（<100行） | ✅ | - | - |
| 中（100-500行） | ✅ | 条件付き | 条件付き |
| 大（>500行） | ✅ | ✅ | ✅ |

### Python  
| タスク規模 | pytest/ruff/mypy | 重複検出 | python-refactor.md |
|-----------|-----------------|----------|-------------------|
| 小（<100行） | ✅ | - | - |
| 中（100-500行） | ✅ | 条件付き | 条件付き |
| 大（>500行） | ✅ | ✅ | ✅ |

※「条件付き」= 閾値を超える重複や問題が検出された場合のみ適用

## 🚀 Quick Links

- [プロジェクトルート](../)
- [設計文書](../draft/)
- [ソースコード](../src/)
- [Rustテンプレート](./templates/rust/)
- [Pythonテンプレート](./templates/python/)


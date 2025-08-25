# QuantForge 計画管理

このディレクトリには、プロジェクトの各種計画文書を管理します。

## 📋 アクティブな計画

*現在アクティブな計画はありません*

## 📦 完了した計画

### 実装計画
- [2025-01-24 実装計画](./archive/2025-01-24-implementation-plan.md) - **COMPLETED** - 14週間の包括的実装計画（基本設計完了）
- [2025-01-24 Rust BSコア実装](./archive/2025-01-24-rust-bs-core.md) - **COMPLETED** - Black-Scholesコア実装計画策定済み

### ドキュメント計画
- [2025-01-24 Sphinxドキュメント作成](./archive/2025-01-24-sphinx-documentation.md) - **COMPLETED** - Sphinxドキュメント構造作成済み

### テスト計画
- [2025-01-24 Pytestカバレッジ戦略](./archive/2025-01-24-pytest-coverage-strategy.md) - **COMPLETED** - 包括的テストカバレッジ戦略実装完了
- [2025-01-25 ゴールデンマスターテスト](./archive/2025-01-25-golden-master-testing.md) - **COMPLETED** - ゴールデンマスター実装完了

### リファクタリング計画
- [2025-08-25 コード重複削除とリファクタリング](./archive/2025-08-25-code-duplication-refactoring.md) - **COMPLETED** - similarity-rsで検出された重複の解消

## 📁 ディレクトリ構造

```
plans/
├── README.md                           # このファイル
├── YYYY-MM-DD-<title>.md             # 日付ベースの計画文書
├── archive/                           # 完了・廃止された計画
│   └── YYYY-MM-DD-<title>.md
└── templates/                         # 計画テンプレート
    └── implementation-plan.md
```

## 🏷️ ステータス定義

- **DRAFT**: 作成中
- **REVIEW**: レビュー中  
- **ACTIVE**: 実行中
- **COMPLETED**: 完了
- **CANCELLED**: 中止
- **ARCHIVED**: アーカイブ済み

## 📝 命名規則

```
YYYY-MM-DD-<type>-<title>.md

例:
2025-01-24-implementation-plan.md
2025-01-25-phase1-detail.md
2025-02-01-performance-optimization.md
```

## 🔄 計画の作成プロセス

1. **新規計画作成**: `plans/`ディレクトリに新規ファイル作成
2. **ステータス**: DRAFTから開始
3. **レビュー**: 必要に応じてREVIEWステータスへ
4. **実行**: ACTIVEステータスで実行開始
5. **完了**: COMPLETEDマーク後、必要に応じてarchive/へ移動

## 📊 進捗サマリー

### アクティブな計画
| 計画 | ステータス | 開始日 | 完了予定 | 進捗 |
|------|-----------|--------|----------|------|
| *なし* | - | - | - | - |

### 完了した計画
| 計画 | ステータス | 開始日 | 完了日 | 成果物 |
|------|-----------|--------|--------|--------|
| [実装計画](./archive/2025-01-24-implementation-plan.md) | **COMPLETED** | 2025-01-24 | 2025-01-24 | 14週間の詳細実装計画書 ✅ |
| [Rust BSコア](./archive/2025-01-24-rust-bs-core.md) | **COMPLETED** | 2025-01-24 | 2025-01-24 | 技術設計書 ✅ |
| [Sphinxドキュメント](./archive/2025-01-24-sphinx-documentation.md) | **COMPLETED** | 2025-01-24 | 2025-01-25 | docs/配下の完全なドキュメント構造 ✅ |
| [Pytestカバレッジ戦略](./archive/2025-01-24-pytest-coverage-strategy.md) | **COMPLETED** | 2025-01-24 | 2025-08-25 | 127テスト実装、Pythonカバレッジ100%達成 ✅ |
| [ゴールデンマスター](./archive/2025-01-25-golden-master-testing.md) | **COMPLETED** | 2025-01-25 | 2025-01-25 | 158テストケース生成、テスト基盤構築 ✅ |
| [コード重複削除](./archive/2025-08-25-code-duplication-refactoring.md) | **COMPLETED** | 2025-08-25 | 2025-08-25 | 重複削減4→ 3箇所、Critical Bug解消 ✅ |

## 🚀 Quick Links

- [プロジェクトルート](../)
- [設計文書](../draft/)
- [ソースコード](../src/)

---

**最終更新**: 2025-08-25
# QuantForge 計画管理

このディレクトリには、プロジェクトの各種計画文書を管理します。

## 📋 アクティブな計画

### 実装計画
- [2025-01-24 実装計画](./2025-01-24-implementation-plan.md) - **ACTIVE** - 14週間の包括的実装計画

### ドキュメント計画
- [2025-01-24 Sphinxドキュメント作成](./2025-01-24-sphinx-documentation.md) - **DRAFT** - 7日間のドキュメント作成計画

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

| 計画 | ステータス | 開始日 | 完了予定 | 進捗 |
|------|-----------|--------|----------|------|
| [実装計画](./2025-01-24-implementation-plan.md) | ACTIVE | 2025-01-24 | 2025-04-30 | 0% |
| [Sphinxドキュメント](./2025-01-24-sphinx-documentation.md) | DRAFT | - | 2025-01-31 | 0% |

## 🚀 Quick Links

- [プロジェクトルート](../)
- [設計文書](../draft/)
- [ソースコード](../src/) *(未作成)*

---

**最終更新**: 2025-01-24
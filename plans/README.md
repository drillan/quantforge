# QuantForge 計画管理

このディレクトリには、プロジェクトの各種計画文書を管理します。

## 📋 アクティブな計画

### 標準化計画
- [2025-08-25 精度設定一元化](./2025-08-25-both-precision-standardization.md) - **ACTIVE** - 精度設定の階層化と一元管理（実施中: 95%完了）

## 📦 完了した計画

### 実装計画
- [2025-01-24 実装計画](./archive/2025-01-24-implementation-plan.md) - **COMPLETED** - 14週間の包括的実装計画（基本設計完了）
- [2025-01-24 Rust BSコア実装](./archive/2025-01-24-rust-bs-core.md) - **COMPLETED** - Black-Scholesコア実装計画策定済み

### ドキュメント計画
- [2025-01-24 Sphinxドキュメント作成](./archive/2025-01-24-sphinx-documentation.md) - **COMPLETED** - Sphinxドキュメント構造作成済み

### テスト計画
- [2025-01-24 Pytestカバレッジ戦略](./archive/2025-01-24-pytest-coverage-strategy.md) - **COMPLETED** - 包括的テストカバレッジ戦略実装完了
- [2025-01-25 ゴールデンマスターテスト](./archive/2025-01-25-golden-master-testing.md) - **COMPLETED** - ゴールデンマスター実装完了

### 実装改善
- [2025-01-25 norm_cdf高精度化](./archive/2025-01-25-rust-norm-cdf-erf.md) - **COMPLETED** - erfベース実装で機械精度達成（<1e-15）

### リファクタリング計画
- [2025-08-25 コード重複削除とリファクタリング](./archive/2025-08-25-code-duplication-refactoring.md) - **COMPLETED** - similarity-rsで検出された重複の解消

### パフォーマンス最適化
- [2025-08-25 erfベース最適化戦略](./archive/2025-08-25-erf-based-optimization-strategy.md) - **COMPLETED** - Rayon並列化で5.3倍高速化達成

## 📁 ディレクトリ構造

```
plans/
├── README.md                           # このファイル
├── YYYY-MM-DD-<lang>-<title>.md      # 言語プレフィックス付き計画文書
├── templates/                         # 計画テンプレート
│   ├── rust/                          # Rust用テンプレート
│   │   └── implementation-plan.md     # Rust実装計画
│   └── python/                        # Python用テンプレート
│       └── implementation-plan.md     # Python実装計画
└── archive/                           # 完了・廃止された計画
    └── YYYY-MM-DD-<lang>-<title>.md
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

## 📊 進捗サマリー

### アクティブな計画（言語別）

#### 両言語統合計画
| 計画 | ステータス | 開始日 | 完了予定 | 進捗 |
|------|-----------|--------|----------|------|
| [精度基準統一化](./2025-08-25-both-precision-standardization.md) | **ACTIVE** | 2025-08-25 | 2025-08-25 | 95% |

#### Rust計画
| 計画 | ステータス | 開始日 | 完了予定 | 進捗 |
|------|-----------|--------|----------|------|
| *アクティブなRust計画なし* | - | - | - | - |

#### Python計画
| 計画 | ステータス | 開始日 | 完了予定 | 進捗 |
|------|-----------|--------|----------|------|
| *アクティブなPython計画なし* | - | - | - | - |

### 完了した計画
| 計画 | ステータス | 開始日 | 完了日 | 成果物 |
|------|-----------|--------|--------|--------|
| [実装計画](./archive/2025-01-24-implementation-plan.md) | **COMPLETED** | 2025-01-24 | 2025-01-24 | 14週間の詳細実装計画書 ✅ |
| [Rust BSコア](./archive/2025-01-24-rust-bs-core.md) | **COMPLETED** | 2025-01-24 | 2025-01-24 | 技術設計書 ✅ |
| [Sphinxドキュメント](./archive/2025-01-24-sphinx-documentation.md) | **COMPLETED** | 2025-01-24 | 2025-01-25 | docs/配下の完全なドキュメント構造 ✅ |
| [Pytestカバレッジ戦略](./archive/2025-01-24-pytest-coverage-strategy.md) | **COMPLETED** | 2025-01-24 | 2025-08-25 | 127テスト実装、Pythonカバレッジ100%達成 ✅ |
| [ゴールデンマスター](./archive/2025-01-25-golden-master-testing.md) | **COMPLETED** | 2025-01-25 | 2025-01-25 | 158テストケース生成、テスト基盤構築 ✅ |
| [norm_cdf高精度化](./archive/2025-01-25-rust-norm-cdf-erf.md) | **COMPLETED** | 2025-01-25 | 2025-01-25 | 機械精度<1e-15、全127テスト成功 ✅ |
| [コード重複削除](./archive/2025-08-25-code-duplication-refactoring.md) | **COMPLETED** | 2025-08-25 | 2025-08-25 | 重複削減4→ 3箇所、Critical Bug解消 ✅ |
| [erfベース最適化](./archive/2025-08-25-erf-based-optimization-strategy.md) | **COMPLETED** | 2025-08-25 | 2025-08-25 | 51ms→9.7ms（5.3倍高速化）、Rayon並列化 ✅ |

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

---

**最終更新**: 2025-08-25

## 📝 計画の変更履歴

### 2025-01-25
- **完了**: `2025-01-25-rust-norm-cdf-erf.md` → `archive/`へ移動
  - 成果: erfベース実装により機械精度レベル（<1e-15）達成、全127テスト成功

### 2025-08-25
- **新規追加**: `2025-08-25-erf-based-optimization-strategy.md` - erfベース実装後のパフォーマンス最適化戦略
- **キャンセル**: `2025-08-25-rust-performance-optimization.md` → `archive/2025-08-25-rust-performance-optimization-cancelled.md`
  - 理由: erfベース実装により前提条件が根本的に変化（高速近似が不要に）
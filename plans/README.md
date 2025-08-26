# QuantForge 計画管理

このディレクトリには、プロジェクトの各種計画文書を管理します。

## ⚠️ 重要な警告

**このディレクトリの文書は実装の参照用ではありません。**

- 計画文書は「一時的な設計スペース」です
- 仕様変更履歴や誤った実装の修正記録を含みます
- **実装時は必ず docs/api/ のドキュメントを参照してください**
- 計画文書を真実の源として扱うと、過去の誤りを繰り返す危険があります

---

## 📋 アクティブな計画

### アーキテクチャ設計
- [2025-08-26 複数オプション価格モデル対応](./2025-08-26-multi-model-architecture.md) - **ACTIVE** - モジュールベースのマルチモデルアーキテクチャ

## 📦 完了した計画

### API改善計画
- [2025-08-26 レガシーAPI完全削除](./archive/2025-08-26-both-destroy-legacy-api.md) - **COMPLETED** - calculate_*関数群の完全削除、95%のコード削減達成
- [2025-08-26 Python API引数名標準化](./archive/2025-08-26-python-api-standardization.md) - **COMPLETED** - Black-Scholesモデルの業界標準表記への統一（v → sigma）

### 実装計画
- [2025-01-24 実装計画](./archive/2025-01-24-implementation-plan.md) - **COMPLETED** - 14週間の包括的実装計画（基本設計完了）
- [2025-01-24 Rust BSコア実装](./archive/2025-01-24-rust-bs-core.md) - **COMPLETED** - Black-Scholesコア実装計画策定済み
- [2025-08-25 Rustプットオプション実装](./archive/2025-08-25-rust-put-option.md) - **COMPLETED** - ヨーロピアンプットオプション完全実装

### 標準化計画
- [2025-08-25 精度設定一元化](./archive/2025-08-25-both-precision-standardization.md) - **COMPLETED** - 精度設定の階層化と一元管理（100%完了）

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

#### アーキテクチャ計画
| 計画 | ステータス | 開始日 | 完了予定 | 進捗 |
|------|-----------|--------|----------|------|
| [複数モデル対応](./2025-08-26-multi-model-architecture.md) | **ACTIVE** | 2025-08-26 | 2025-09-23 | 55% |

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
| [Rustプットオプション](./archive/2025-08-25-rust-put-option.md) | **COMPLETED** | 2025-08-25 | 2025-08-25 | プット価格計算実装、Put-Callパリティ検証 ✅ |
| [Rustインプライドボラティリティ](./archive/2025-08-25-rust-implied-volatility.md) | **COMPLETED** | 2025-08-25 | 2025-08-25 | Newton-Raphson/Brent法、並列化、Python統合 ✅ |
| [精度設定一元化](./archive/2025-08-25-both-precision-standardization.md) | **COMPLETED** | 2025-08-25 | 2025-08-25 | 精度基準の階層化、ハードコード除去 ✅ |

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

**最終更新**: 2025-08-26

## 📝 計画の変更履歴

### 2025-08-26
- **新規追加**: `2025-08-26-multi-model-architecture.md` - 複数オプション価格モデル対応アーキテクチャ設計
- **完了**: `2025-08-26-python-api-standardization.md` → `archive/`へ移動
  - 成果: Black-Scholesモデルの引数名をv→sigmaへ統一、業界標準準拠
- **完了**: `2025-08-25-both-precision-standardization.md` → `archive/`へ移動
  - 成果: 精度設定の階層化、ハードコード完全除去、全テスト成功
- **README更新**: インプライドボラティリティ計画の重複記載を修正

### 2025-08-25
- **完了**: `2025-08-25-rust-put-option.md` → `archive/`へ移動
  - 成果: ヨーロピアンプットオプション完全実装、Put-Callパリティ検証、全テスト成功
- **新規追加**: `2025-08-25-erf-based-optimization-strategy.md` - erfベース実装後のパフォーマンス最適化戦略
- **キャンセル**: `2025-08-25-rust-performance-optimization.md` → `archive/2025-08-25-rust-performance-optimization-cancelled.md`
  - 理由: erfベース実装により前提条件が根本的に変化（高速近似が不要に）

### 2025-01-25
- **完了**: `2025-01-25-rust-norm-cdf-erf.md` → `archive/`へ移動
  - 成果: erfベース実装により機械精度レベル（<1e-15）達成、全127テスト成功
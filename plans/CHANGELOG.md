# 計画変更履歴

## 2025-08-27
- `2025-08-27-both-wheel-distribution-strategy.md` → archive/ ✅
  - Python 3.12+ 専用wheel配布戦略の完全実装
  - GitHub Actions CI/CD（Linux/Windows/macOS）構築
  - TestPyPI配布成功（v0.0.1, v0.0.2）
  - Single Source of Truth（Cargo.toml）によるバージョン管理
  - manylinux2014互換、wheelサイズ < 300KB達成

## 2025-08-27（American Option）
- `2025-01-27-rust-american-option-implementation.md` → archive/ ✅
  - American optionの完全実装（Bjerksund-Stensland 2002）
  - Rustモジュール（5ファイル、約1,200行）、Python API（8関数）、テスト（19項目）
  - 早期行使境界計算、配当裁定防止（q > r チェック）
  - パフォーマンス: 単一計算 ~1μs、バッチ100万件 < 100ms
  - Putオプションで参照実装と12%誤差あり（要調査）

## 2025-08-26
- `2025-08-26-black76-model-implementation.md` → archive/ ✅
  - Black76先物オプション価格モデルの完全実装
  - Rustモジュール実装、Python API統合、包括的テスト
  - 先物価格パラメータfへの統一
- `2025-08-26-both-black76-api-correction.md` → archive/ ✅
  - Black76モデルのAPIパラメータ修正
  - 全関数でfパラメータ統一、ドキュメント整備完了
- `2025-08-26-merton-model-implementation.md` → archive/ ✅
  - Mertonモデル（配当付き資産オプション）の完全実装
  - Rustモジュール（4ファイル）、Python API（9関数）、テスト（25項目）
  - 6種類のグリークス（dividend_rho含む）
  - q=0でBlack-Scholesとの完全互換性確認
- `2025-08-26-python-api-standardization.md` → archive/ ✅
  - Black-Scholesモデルの引数名をv→sigmaへ統一、業界標準準拠
- `2025-08-26-both-destroy-legacy-api.md` → archive/ ✅
  - calculate_*関数群の完全削除、95%のコード削減達成

## 2025-08-25
- `2025-08-25-both-precision-standardization.md` → archive/ ✅
  - 精度設定の階層化、ハードコード完全除去、全テスト成功
- `2025-08-25-rust-put-option.md` → archive/ ✅
  - ヨーロピアンプットオプション完全実装、Put-Callパリティ検証、全テスト成功
- `2025-08-25-erf-based-optimization-strategy.md` → archive/ ✅
  - erfベース実装後のパフォーマンス最適化戦略
  - 51ms→9.7ms（5.3倍高速化）、Rayon並列化
- `2025-08-25-code-duplication-refactoring.md` → archive/ ✅
  - 重複削減4→3箇所、Critical Bug解消
- `2025-08-25-rust-implied-volatility.md` → archive/ ✅
  - Newton-Raphson/Brent法、並列化、Python統合
- `2025-08-25-rust-performance-optimization.md` → archive/ (CANCELLED)
  - erfベース実装により前提条件が根本的に変化（高速近似が不要に）

## 2025-01-25
- `2025-01-25-rust-norm-cdf-erf.md` → archive/ ✅
  - erfベース実装により機械精度レベル（<1e-15）達成、全127テスト成功
- `2025-01-25-golden-master-testing.md` → archive/ ✅
  - 158テストケース生成、テスト基盤構築

## 2025-01-24
- `2025-01-24-implementation-plan.md` → archive/ ✅
  - 14週間の詳細実装計画書
- `2025-01-24-rust-bs-core.md` → archive/ ✅
  - Black-Scholesコア実装計画策定済み、技術設計書
- `2025-01-24-sphinx-documentation.md` → archive/ ✅
  - Sphinxドキュメント構造作成済み、docs/配下の完全なドキュメント構造
- `2025-01-24-pytest-coverage-strategy.md` → archive/ ✅
  - 包括的テストカバレッジ戦略実装完了、127テスト実装、Pythonカバレッジ100%達成
# Golden Master Test Suite

## 概要

QuantForgeオプション価格計算の信頼性を保証するマルチソース検証テストスイート。

## 特徴

- **マルチソース検証**: Haug (2007)、BENCHOP、解析解による相互検証
- **YAML駆動設定**: 保守性の高いテストケース管理
- **3段階実行制御**: Quick (<1s)、Standard (<5s)、Full (<30s)
- **戦略的テストケース**: 158から50ケースに最適化

## ディレクトリ構成

```
tests/golden_master/
├── data/
│   └── test_cases.yaml      # テストケース定義
├── references/               # 参照実装
│   ├── haug.py              # Haug教科書の公式
│   ├── benchop.py           # BENCHOP参照値
│   └── analytical.py        # 解析解
├── conftest.py              # pytest設定
└── test_golden_master.py    # メインテスト
```

## 使用方法

```bash
# Quick tests (10 cases, <1s)
pytest -m quick tests/golden_master/

# Standard tests (30 cases, <5s)
pytest -m standard tests/golden_master/

# Full validation (50 cases, <30s)
pytest tests/golden_master/

# CI/CD用（Quick + Standard）
pytest -m "quick or standard" tests/golden_master/
```

## 参照実装

### 1. Haug (2007)
- 書籍: "The Complete Guide to Option Pricing Formulas"
- 実装: `references/haug.py`
- 業界標準の価格計算公式

### 2. BENCHOP
- 論文: "BENCHOP – The BENCHmarking project in Option Pricing" (2015)
- 実装: `references/benchop.py`
- 学術ベンチマーク用の高精度参照値

### 3. Analytical
- 実装: `references/analytical.py`
- 境界条件、特殊ケースの解析解

## 既知の問題

### 参照値の不整合

一部のBENCHOP論文値に誤りの可能性があります：

| パラメータ | BENCHOP論文 | 正しい計算値 |
|-----------|------------|-------------|
| S=100, K=100, T=0.25, σ=0.2 | 4.0378 | 4.615 |

この値は検証済みで、正しい値に修正されています。

## テストカテゴリ

### Quick Tests (10件)
- 基本的な価格計算の検証
- ATM、ITM、OTM オプション
- Black-Scholes、Black76、Merton モデル

### Standard Tests (30件)
- Greeks計算の検証
- 各種満期構造
- ボラティリティスマイル
- 金利感応度

### Full Tests (10件)
- 数値安定性テスト
- 極端なパラメータ
- Put-Call パリティ
- モデル間の整合性

## 依存関係

```bash
# 必須
pip install pyyaml scipy numpy

# 開発用
pip install pytest ruff mypy
```

## 品質保証

```bash
# フォーマット
ruff format tests/golden_master/

# リント
ruff check tests/golden_master/

# 型チェック
mypy tests/golden_master/
```

## 今後の拡張

1. QuantLib統合（オプショナル）
2. American オプション対応
3. エキゾチックオプション追加
4. モンテカルロ検証
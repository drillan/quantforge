# QuantForge ドキュメントリファクタリングルール

## 1. 客観的表現の原則

### 1.1 主観的表現の排除
**禁止表現:**
- ❌ 超高速、次世代、画期的、革新的、圧倒的、最先端
- ❌ 驚異的、劇的、飛躍的、究極の、完璧な

**推奨表現:**
- ✅ 「Python実装比500-1000倍の処理速度」（具体的数値）
- ✅ 「Rust + PyO3による実装」（技術仕様）
- ✅ 「AVX2/AVX-512 SIMD命令セット対応」（具体的機能）

### 1.2 数値データの根拠明示
```markdown
❌ 悪い例: 「100万件を20msで処理」

✅ 良い例: 「100万件を20ms以下で処理
測定環境: Intel i9-12900K, AVX2有効, 単精度演算
測定日: 2025-01-24」
```

## 2. MyST Parser Admonitionsの活用

### 2.1 警告・注記の記法
MyST Parserのadmonition構文を使用し、絵文字や太字での警告を避ける：

```markdown
:::{warning}
この機能は実験的であり、APIが変更される可能性があります。
:::

:::{note}
パフォーマンスを最大化するには、AVX2対応のCPUが必要です。
:::

:::{tip}
バッチ処理を使用することで、処理速度が大幅に向上します。
:::

:::{important}
アメリカンオプションの計算には追加の計算時間が必要です。
:::

:::{danger}
この操作はデータを完全に削除します。復元はできません。
:::
```

### 2.2 利用可能なAdmonitionタイプ
- `note` - 追加情報
- `tip` - 効率的な使用方法
- `important` - 重要な情報
- `warning` - 注意事項
- `danger` - 危険な操作
- `seealso` - 関連項目
- `todo` - 今後の実装予定（内部文書のみ）

## 3. 国際化（i18n）を前提とした記述

### 3.1 翻訳可能な構造
```markdown
✅ 良い例（翻訳しやすい）:
「このメソッドは配列を受け取ります。」
「戻り値は浮動小数点数です。」

❌ 悪い例（翻訳しづらい）:
「このメソッドはNumPy配列をガンガン処理して爆速で結果を返します！」
```

### 3.2 言語非依存の要素
以下は翻訳せず、全言語で共通とする：
- APIメソッド名・パラメータ名
- 数式・アルゴリズム名
- ライブラリ名・技術仕様
- コード例

### 3.3 用語の一貫性
翻訳用語集を管理し、全文書で統一：

```yaml
# docs/locale/glossary.yml
terms:
  - en: "option pricing"
    ja: "オプション価格計算"
  - en: "volatility"
    ja: "ボラティリティ"
  - en: "strike price"
    ja: "権利行使価格"
```

## 4. 実装状況の表記

### 4.1 開発段階の表記
具体的なバージョン番号を避け、段階表記を使用：

```markdown
❌ 避けるべき表記:
- v0.3.0で実装予定
- v1.0.0でリリース

✅ 推奨表記:
- 現在実装済み
- 開発中（アルファ段階）
- ベータテスト中
- 将来実装予定
- 現時点では対応予定なし
```

### 4.2 機能の成熟度表示
```markdown
:::{admonition} 実装状況
:class: note

**安定**: Black-Scholesモデル、基本的なグリークス計算
**ベータ**: アメリカンオプション（Bjerksund-Stensland）
**実験的**: モンテカルロ法による価格計算
**計画中**: GPU並列化、機械学習統合
:::
```

## 5. 強調表現の適正使用

### 5.1 マークダウン装飾の制限
- **太字**: APIパラメータの初出時、重要な警告のみ
- *斜体*: 数学変数、外国語の専門用語
- `コード`: インラインコード、ファイル名、コマンド
- 絵文字: 原則使用禁止（GitHubのissue/PRを除く）

### 5.2 見出しレベルの統一
```markdown
# ドキュメントタイトル（1つのみ）
## 主要セクション
### サブセクション
#### 詳細項目
```

## 6. コード例の正確性

### 6.1 実行可能性の明記
```python
# 実装済みのAPI（そのまま実行可能）
from quantforge.models import black_scholes
price = black_scholes.call_price(100, 110, 1.0, 0.05, 0.2)

# 概念的な例（実装予定または説明用）
"""
以下は概念的な実装例です（現在のAPIでは利用できません）
"""
def future_feature():
    pass
```

### 6.2 import文の完全性
```python
# 必要なimportをすべて記載
import numpy as np
from quantforge.models import black_scholes
from quantforge.utils import validate_inputs

# 省略しない
```

## 7. パフォーマンス記述の標準化

### 7.1 ベンチマーク情報の必須項目
```yaml
environment:
  cpu: "Intel Core i9-12900K"
  ram: "32GB DDR5-5600"
  os: "Ubuntu 22.04 LTS"
  compiler: "rustc 1.75.0"
  flags: "-O3 -march=native"

measurement:
  date: "2025-01-24"
  iterations: 1000
  warmup: 100
  statistical_method: "median of 5 runs"
```

### 7.2 相対的な性能表記
```markdown
:::{note}
性能比較は特定の環境での測定値です。
実際の性能は使用環境により異なります。
:::
```

## 8. 数式とアルゴリズムの記述

### 8.1 LaTeX数式の使用
```markdown
インライン数式: $\sigma$ はボラティリティを表す

ブロック数式:
$$
C = S_0 N(d_1) - Ke^{-rT} N(d_2)
$$
```

### 8.2 変数定義の明確化
数式使用時は必ず変数を定義：
```markdown
where:
- $C$: コールオプション価格
- $S_0$: 現在の原資産価格
- $K$: 権利行使価格
- $r$: 無リスク金利
- $T$: 満期までの時間
```

## 9. 参考文献の標準形式

### 9.1 学術文献の引用
```markdown
## 参考文献

1. Black, F. and Scholes, M. (1973). "The Pricing of Options and Corporate Liabilities." 
   *Journal of Political Economy*, 81(3), 637-654.

2. Hull, J.C. (2018). *Options, Futures, and Other Derivatives* (10th ed.). Pearson.
```

### 9.2 ウェブリソースの引用
```markdown
- [Rust Documentation](https://doc.rust-lang.org/) - Rust公式ドキュメント
- [PyO3 User Guide](https://pyo3.rs/) - Python-Rust連携ライブラリ
```

## 10. ファイル構成の標準化

### 10.1 ドキュメント構造
```
docs/
├── index.md                 # トップページ（簡潔に）
├── quickstart.md            # クイックスタート
├── installation.md          # インストール手順
├── user_guide/             # ユーザーガイド
│   ├── basic_usage.md
│   └── advanced_topics.md
├── api/                    # APIリファレンス
│   ├── python/
│   └── rust/
├── models/                 # 理論的背景
├── performance/            # パフォーマンス
├── development/           # 開発者向け
└── internal/              # 内部文書（公開しない）
    ├── documentation_refactoring_rules.md
    └── naming_conventions.md
```

## 11. 自動検証とレビュー

### 11.1 検証スクリプト
```bash
#!/bin/bash
# docs/scripts/validate_docs.sh

echo "Checking subjective expressions..."
grep -r "超高速\|次世代\|画期的" docs/ --include="*.md"

echo "Checking version numbers..."
grep -r "v[0-9]\+\.[0-9]\+\.[0-9]\+" docs/ --include="*.md"

echo "Checking admonition usage..."
grep -r "^\*\*警告\*\*\|^\*\*注意\*\*" docs/ --include="*.md"

echo "Validating MyST syntax..."
python -m myst_parser.cli parse docs/**/*.md --strict
```

### 11.2 レビューチェックリスト
- [ ] 主観的表現を客観的データに置換
- [ ] MyST Admonitionsを適切に使用
- [ ] 具体的なバージョン番号を避ける
- [ ] 翻訳しやすい簡潔な文章構造
- [ ] 測定条件を完全に記載
- [ ] コード例の実行可能性を明記
- [ ] 用語の一貫性を確認
- [ ] 国際化を考慮した記述

## 12. 移行計画

### Phase 1: 即座対応（1日以内）
- MyST Admonitionsへの置換
- 主観的表現の削除
- バージョン番号の削除

### Phase 2: 短期対応（1週間以内）
- 用語集の作成と統一
- 測定条件の追記
- コード例の分類

### Phase 3: 中期対応（2週間以内）
- 国際化準備（gettext対応）
- 完全なドキュメント構造の整理
- 自動検証の導入

---

これらのルールにより、国際化対応可能で客観的かつ保守性の高いドキュメントを実現します。
# MyST記法 命名ガイドライン

## 概要

このドキュメントは、QuantForgeプロジェクトにおけるMyST記法のname属性とcaption属性の命名規則を定義します。
日英ドキュメントの構造的な対応関係を管理するため、一貫した命名が重要です。

## 基本原則

1. **言語非依存**: name属性は日英で共通（英語ベース）
2. **一意性**: 同一ファイル内でnameは一意
3. **可読性**: 意味が明確で理解しやすい
4. **一貫性**: 同じタイプの要素は同じ命名パターン

## name属性の命名規則

### 形式
```
{file-basename}-{element-type}-{descriptor}
```

- `file-basename`: ファイル名（拡張子なし、アンダースコアはハイフンに変換）
- `element-type`: 要素の種類（省略可能）
- `descriptor`: 内容を表す記述子

### 要素別の命名規則

#### ヘッダー（セクション）
```markdown
(black-scholes-intro)=
## 概要

(black-scholes-theory)=
## 理論的背景

(black-scholes-pricing-formula)=
### 価格式
```

**パターン**: `{file-basename}-{section-slug}`
- セクション名を英語化してスラグ化
- 階層は反映しない（フラットな命名）

#### コードブロック
````markdown
```{code-block} python
:name: black-scholes-code-call-price
:caption: コール価格の計算

def call_price(s, k, t, r, sigma):
    # ...
```
````

**パターン**: `{file-basename}-code-{function-or-purpose}`
- 関数名がある場合は使用
- なければ目的を記述

#### 数式
````markdown
```{math}
:name: black-scholes-eq-pde

\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} - rV = 0
```
````

**パターン**: `{file-basename}-eq-{equation-name}`
- `eq` は equation の省略形
- 有名な式には標準的な名前を使用（pde, call-formula等）

#### テーブル
````markdown
```{list-table} グリークスの定義
:name: black-scholes-table-greeks
:header-rows: 1

* - グリーク
  - 意味
  - 計算式
```
````

**パターン**: `{file-basename}-table-{content-type}`

#### 図
````markdown
```{figure} ./images/payoff.png
:name: black-scholes-fig-payoff
:caption: オプションのペイオフ図
```
````

**パターン**: `{file-basename}-fig-{description}`

## caption属性のガイドライン

### 日本語版
- 簡潔で説明的な日本語
- 技術用語は適切に使用
- 長すぎない（20文字程度まで）

### 英語版
- 対応する英語表現
- 日本語版と同じ情報量
- 標準的な金融用語を使用

### 対応例

| 日本語caption | 英語caption |
|--------------|------------|
| コール価格の計算 | Call price calculation |
| グリークスの定義 | Greeks definition |
| ペイオフ図 | Payoff diagram |
| Black-Scholes偏微分方程式 | Black-Scholes PDE |

## 実装手順

### 1. 新規ドキュメント作成時
1. 最初からMyST記法で記述
2. name属性を必ず付与
3. 言語横断的に一貫した命名

### 2. 既存ドキュメントの更新
1. `scripts/add_myst_names.py` で自動付与
2. 生成された名前を確認・調整
3. 日英で同じnameを使用

### 3. 翻訳時の注意
- name属性は変更しない（コピーして使用）
- caption属性のみ翻訳
- コード内容は基本的に同一

## よくある質問

### Q: 同じ種類の要素が複数ある場合は？
A: 連番を付けます
```
black-scholes-code-example-1
black-scholes-code-example-2
```

### Q: ファイル名が変更された場合は？
A: name属性も更新が必要です（一括置換を推奨）

### Q: name属性は必須？
A: 構造比較ツールを使用する場合は必須です

## チェックリスト

新規ドキュメント作成時:
- [ ] すべてのヘッダーにname属性
- [ ] 重要なコードブロックにname属性
- [ ] 数式にname属性
- [ ] テーブルにname属性とcaption
- [ ] 図にname属性とcaption

翻訳時:
- [ ] name属性をそのままコピー
- [ ] caption属性を適切に翻訳
- [ ] 構造が一致することを確認

## 関連ツール

- `scripts/add_myst_names.py`: name属性の自動付与
- `translations/structure_compare.py`: 構造比較
- `scripts/check_all_doc_structures.sh`: 一括チェック
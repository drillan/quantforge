# MyST記法リファクタリング指示書

## 対象ファイル
$ARGUMENTS

## 役割
あなたはQuantForgeプロジェクトのドキュメントをMyST記法に変換する専門家です。
日英ドキュメントの構造的な対応関係を管理するため、適切なname属性とcaption属性を付与してください。

## 必須参照ドキュメント
**`docs/internal/myst_naming_guidelines.md`** の規則に厳密に従ってください。
このガイドラインには命名規則、パターン、実例が詳細に記載されています。

## 実行手順

### 1. 事前確認
- [ ] 対象ファイル（$ARGUMENTS）を読み込む、（ $ARGUMENTS がディレクトリの場合はサブディレクトリを含めた*.md ファイル）
- [ ] `docs/internal/myst_naming_guidelines.md` を読み込む
- [ ] 対象ファイルのベース名を確認（例: black_scholes → black-scholes）
- [ ] 既存のname属性がないか確認（重複防止）

### 2. 変換対象と優先順位

#### 【最優先】参照される可能性の高い要素
1. **主要な数式**（Black-Scholes式、Greeks定義式など）
2. **実装関数**（call_price, put_price, calculate_greeksなど）
3. **定義テーブル**（パラメータ一覧、Greeks一覧など）

#### 【必須】すべてのセクションヘッダー
```markdown
(black-scholes-intro)=
## 概要

(black-scholes-theory)=
## 理論的背景
```

#### 【推奨】コードブロック、数式、表、図
- コードブロック → ````{code-block}` 形式
- 数式 → ````{math}` 形式
- 表 → ````{list-table}` 形式（複雑な内容の場合）
- 図 → ````{figure}` 形式

### 3. 変換規則

#### コードブロック
````markdown
# 変換前
```python
def call_price(s, k, t, r, sigma):
    return price
```

# 変換後
```{code-block} python
:name: black-scholes-code-call-price
:caption: コール価格の計算
:linenos:

def call_price(s, k, t, r, sigma):
    return price
```
````

#### 数式
````markdown
# 変換前
$$C = S_0 N(d_1) - Ke^{-rT} N(d_2)$$

# 変換後
```{math}
:name: black-scholes-eq-call-formula
:label: eq:bs-call

C = S_0 N(d_1) - Ke^{-rT} N(d_2)
```
````

#### 表（list-table推奨条件）
以下の場合はlist-tableを使用：
- セル内に改行がある
- セル内に数式がある
- セル内にコードがある
- 列幅の調整が必要

````markdown
# 変換前（Markdownテーブル）
| パラメータ | 記号 | 説明 |
|-----------|------|------|
| スポット価格 | s | 現在の資産価格 |

# 変換後（list-table）
```{list-table} パラメータ定義
:name: black-scholes-table-parameters
:header-rows: 1
:widths: 30 20 50

* - パラメータ
  - 記号
  - 説明
* - スポット価格
  - s
  - 現在の資産価格
```
````

#### 図・画像
````markdown
# 変換前
![ペイオフ図](./images/payoff.png)

# 変換後
```{figure} ./images/payoff.png
:name: black-scholes-fig-payoff
:alt: コールオプションのペイオフ図
:width: 80%
:align: center

コールオプションのペイオフ図
```
````

### 4. 命名規則の確認

#### name属性の構成
```
{file-basename}-{element-type}-{descriptor}
```

| 要素タイプ | element-type | 例 |
|-----------|--------------|-----|
| ヘッダー | (省略) | `black-scholes-intro` |
| コード | code | `black-scholes-code-call-price` |
| 数式 | eq | `black-scholes-eq-pde` |
| 表 | table | `black-scholes-table-greeks` |
| 図 | fig | `black-scholes-fig-payoff` |

#### 連番の付け方
- **意味的区別優先**: `code-european-option`, `code-american-option`
- **順序的区別**: `example-1`, `example-2`, `step-1`, `step-2`

### 5. 日英対応の確認

#### 翻訳時の鉄則
- **name属性**: 絶対に変更しない（コピー&ペースト）
- **caption属性**: 各言語に翻訳
- **構造**: 完全に一致させる

#### 対応例
````markdown
# 日本語版
```{code-block} python
:name: black-scholes-code-implied-vol
:caption: インプライドボラティリティの計算
```

# 英語版
```{code-block} python
:name: black-scholes-code-implied-vol
:caption: Implied volatility calculation
```
````

### 6. 品質チェックリスト

#### 変換後の確認
- [ ] すべてのname属性が一意であるか
- [ ] name属性が英語で記述されているか
- [ ] ファイル名と一致しているか（black_scholes.md → black-scholes-*）
- [ ] ガイドラインのパターンに従っているか
- [ ] 重要な要素にはすべてname属性があるか

#### 日英整合性の確認
- [ ] 同じ要素に同じnameを使用しているか
- [ ] caption以外の構造が完全に一致しているか
- [ ] list-tableの列数・行数が一致しているか

### 7. トラブルシューティング

#### よくある問題と解決策

**Q: nameが重複してしまった**
A: 連番を付ける、または意味的な区別を追加
```
black-scholes-code-example → black-scholes-code-example-basic
black-scholes-code-example → black-scholes-code-example-advanced
```

**Q: 日英でcaptionの長さが大きく異なる**
A: 問題ありません。captionは各言語で自然な表現を優先

**Q: インラインコードや数式はどうする？**
A: そのまま残します。ブロック要素のみが対象

### 8. 実行コマンド

#### 自動付与（初回）
```bash
# 自動でname属性を付与
python scripts/add_myst_names.py --file docs/ja/models/black_scholes.md

# ドライラン（確認のみ）
python scripts/add_myst_names.py --file docs/ja/models/black_scholes.md --dry-run
```

#### 構造比較（検証）
```bash
# 日英の構造を比較
python translations/structure_compare.py \
  --ja docs/ja/models/black_scholes.md \
  --en docs/en/models/black_scholes.md \
  --format all
```

## 実行方法

このコマンドは以下のように使用します：

```bash
# 単一ファイルの変換
/myst-refactor docs/ja/models/black_scholes.md

# 複数ファイルの変換
/myst-refactor docs/ja/models/black_scholes.md docs/en/models/black_scholes.md

# 引数なしの場合は対話的に確認
/myst-refactor
```

## 最終確認
対象ファイル（$ARGUMENTS）のリファクタリングにより：
1. ✅ 日英ドキュメントの構造的対応が明確になる
2. ✅ 自動差分検出が可能になる
3. ✅ 翻訳更新の効率が向上する
4. ✅ ドキュメントの保守性が向上する

---

**注意**: 
- 対象ファイルパスは $ARGUMENTS で参照されます
- 必ず `docs/internal/myst_naming_guidelines.md` を主要な参照元として使用してください
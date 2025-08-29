# MyST記法リファクタリング指示書

## 対象ファイル
$ARGUMENTS

## 役割
あなたはQuantForgeプロジェクトのドキュメントをMyST記法に変換する専門家です。
日英ドキュメントの構造的な対応関係を管理するため、適切なname属性とcaption属性を付与してください。

## ⚠️ 重要な教訓（2025-08-29の実装経験より）
- **汎用的な名前は絶対に避ける**: `*-code-section`のような名前は18個の重複を引き起こした実例あり
- **captionから具体的な名前を生成**: 同期率を85.7%→94.7%に改善した実績
- **Single Source of Truth原則**: 重複する情報源は削除（changelog.md, faq.md削除の実例）

## 必須参照ドキュメント
**`docs/ja/internal/myst_naming_guidelines.md`** の規則に厳密に従ってください。
このガイドラインには命名規則、パターン、実例が詳細に記載されています。

## 実行手順

### 1. 事前確認
- [ ] 対象ファイル（$ARGUMENTS）を読み込む
  - $ARGUMENTSがディレクトリの場合：サブディレクトリを含めた*.mdファイル
  - $ARGUMENTSがファイルの場合：そのファイルのみ
  - $ARGUMENTSが空の場合：docs/ja/とdocs/en/の全*.mdファイル
- [ ] `docs/ja/internal/myst_naming_guidelines.md` を読み込む
- [ ] 対象ファイルのベース名を確認（例: black_scholes → black-scholes）
- [ ] 既存のname属性を検出して重複を防ぐ
- [ ] Sphinxビルドで既存の警告がないか確認

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

# 変換後（captionから具体的な名前を生成）
```{code-block} python
:name: black-scholes-code-call-price
:caption: コール価格の計算
:linenos:

def call_price(s, k, t, r, sigma):
    return price
```

# ⚠️ 避けるべき汎用名（実際に18個の重複を引き起こした例）
# :name: black-scholes-code-section  ❌
# :name: pricing-code-section  ❌  
# :name: installation-code-section  ❌
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

#### captionからの自動生成ルール（推奨）
1. **英語caption優先**: 英語版のcaptionから生成
2. **日本語の場合**: 意味を英訳して生成
3. **変換規則**:
   - スペース → ハイフン
   - 特殊文字 → 削除
   - 大文字 → 小文字
   
**実例（成功事例）**:
- "全グリークスを一括計算" → `american-greeks-calculation`
- "Visual C++ Redistributable" → `installation-code-visual-c-redistributable`
- "TestPyPIから最新開発版をインストール" → `installation-code-testpypi`

#### 連番の付け方
- **意味的区別優先**: `code-european-option`, `code-american-option`
- **順序的区別**: `example-1`, `example-2`, `step-1`, `step-2`
- **❌ 避けるべき**: 単純な`-1`, `-2`, `-3`（意味が不明）

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

#### 重複検出の自動実行
```bash
# Sphinxビルドで警告チェック
cd docs && sphinx-build -M html ja _build/ja 2>&1 | grep "duplicate label"
cd docs && sphinx-build -M html en _build/en 2>&1 | grep "duplicate label"

# 構造比較ツールでの検証
python translations/compare/structure_compare.py \
  --ja docs/ja/models/black_scholes.md \
  --en docs/en/models/black_scholes.md \
  --format json | jq '.summary.issues'
```

#### 日英整合性の確認
- [ ] 同じ要素に同じnameを使用しているか
- [ ] caption以外の構造が完全に一致しているか
- [ ] list-tableの列数・行数が一致しているか
- [ ] 同期率95%以上を達成しているか

### 7. トラブルシューティング

#### よくある問題と解決策（実際の事例に基づく）

**Q: nameが重複してしまった（実例：18個の重複）**
A: captionの内容から具体的な名前を生成する
```
# 問題のあった例（18個の重複を引き起こした）
:name: installation-code-section  ❌
:name: installation-code-section  ❌
:name: installation-code-section  ❌

# 解決策（captionから生成）
:name: installation-code-testpypi  ✅
:name: installation-code-visual-studio-build-tools  ✅  
:name: installation-code-rust  ✅
```

**Q: 汎用的な名前しか思いつかない**
A: captionの内容を英訳して使用
```
caption: "バッチサイズを調整"
→ name: installation-code-batch-size

caption: "早期行使境界の計算"  
→ name: american-exercise-boundary
```

**Q: 日英でcaptionの長さが大きく異なる**
A: 問題ありません。captionは各言語で自然な表現を優先

**Q: インラインコードや数式はどうする？**
A: そのまま残します。ブロック要素のみが対象

**Q: Sphinxビルドで"duplicate label"警告が出る**
A: name属性が重複しています。構造比較ツールで特定：
```bash
python translations/compare/check_duplicates.py docs/ja/
```

### 8. 実装経験に基づくベストプラクティス

#### ❌ 失敗パターン（実際に発生した問題）

1. **汎用的すぎる命名（18個の重複を引き起こした）**
```markdown
# すべて同じ名前になってしまった失敗例
:name: installation-code-section
:name: pricing-code-section  
:name: american-code-section
```

2. **連番の安易な使用**
```markdown
# 意味が不明な名前
:name: code-1
:name: code-2
:name: code-3
```

3. **英訳せずに日本語のまま**
```markdown
# ローマ字化は避ける
:name: keisan-kekka  ❌
:name: calculation-result  ✅
```

#### ✅ 成功パターン（94.7%同期率を達成）

1. **captionベースの具体的命名**
```markdown
caption: "TestPyPIから最新開発版をインストール"
→ name: installation-code-testpypi

caption: "全グリークスを一括計算"
→ name: american-greeks-calculation

caption: "早期行使境界の計算"
→ name: american-exercise-boundary
```

2. **意味的な区別の明確化**
```markdown
:name: black-scholes-code-european-option
:name: black-scholes-code-american-option
:name: black-scholes-code-asian-option
```

3. **階層的な命名**
```markdown
:name: installation-code-prerequisites
:name: installation-code-prerequisites-ubuntu
:name: installation-code-prerequisites-macos
```

### 9. 実行コマンド

#### 自動付与（初回）
```bash
# 自動でname属性を付与
python scripts/add_myst_names.py --file docs/ja/models/black_scholes.md

# ドライラン（確認のみ）
python scripts/add_myst_names.py --file docs/ja/models/black_scholes.md --dry-run
```

#### 構造比較（検証）
```bash
# 日英の構造を比較（正しいパス）
python translations/compare/structure_compare.py \
  --ja docs/ja/models/black_scholes.md \
  --en docs/en/models/black_scholes.md \
  --format all

# 全体の検証
cd translations/compare && ./check_all.sh

# レポート確認（同期率95%以上が目標）
cat translations/compare/reports/latest/summary.json | jq '.average_sync_rate'
```

## 実行方法

このコマンドは以下のように使用します：

```bash
# 単一ファイルの変換
/myst-refactor docs/ja/models/black_scholes.md

# 複数ファイルの変換
/myst-refactor docs/ja/models/black_scholes.md docs/en/models/black_scholes.md

# ディレクトリ全体の変換
/myst-refactor docs/ja/models/

# 引数なしの場合はdocs全体を処理
/myst-refactor
```

### $ARGUMENTSの処理ロジック

1. **$ARGUMENTSが与えられた場合**：
   - 指定されたファイル/ディレクトリを処理
   - 複数のパスがスペース区切りで指定された場合は順次処理

2. **$ARGUMENTSが空の場合**：
   - docs/ja/とdocs/en/配下のすべての*.mdファイルを処理
   - 日英両方のドキュメントを一括でMyST記法に変換
   - 構造比較ツールで同期率を確認

## 最終確認
対象ファイル（$ARGUMENTSまたはdocs全体）のリファクタリング効果：
1. ✅ 日英ドキュメントの構造的対応が明確になる
2. ✅ 自動差分検出が可能になる（同期率95%以上を目標）
3. ✅ 翻訳更新の効率が向上する
4. ✅ ドキュメントの保守性が向上する
5. ✅ Sphinxビルド時の警告がゼロになる

---

**重要な注意**: 
- **汎用的な名前を避ける**: `-code-section`のような名前は使用禁止
- **captionから生成**: 具体的で意味のある名前を生成
- **重複チェック必須**: Sphinxビルドで警告が出ないことを確認
- 必ず `docs/ja/internal/myst_naming_guidelines.md` を主要な参照元として使用してください
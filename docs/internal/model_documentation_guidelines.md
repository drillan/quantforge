# モデルドキュメントガイドライン

## 1. 基本原則

### 1.1 ドキュメント分離の原則
- **理論と実装の分離**: 数学的理論は `docs/models/`、API使用方法は `docs/api/python/`
- **完全性**: 各モデルは必ず両方のドキュメントを持つ
- **対称性**: 全モデルが同じ構造を持つ

### 1.2 一貫性の原則
- **構造の統一**: 全モデルで同じセクション構成
- **パラメータ記述**: 位置引数、省略形の使用
- **命名規則遵守**: `docs/internal/naming_conventions.md`に準拠
- **相互リンク**: APIと理論の相互参照

## 2. ファイル構成

### 2.1 新モデル追加時に必要なファイル
1. `docs/api/python/<model_name>.md` - API使用方法
2. `docs/models/<model_name>.md` - 理論的背景
3. 既存ファイルの更新:
   - `docs/api/python/pricing.md` - モデル概要追加
   - `docs/api/python/implied_vol.md` - IV機能があれば追加
   - `docs/index.md` - toctree更新

### 2.2 ファイル命名規則
- モデル名はアンダースコア区切り（例: `black_scholes.md`, `heston_model.md`）
- Pythonモジュール名と一致させる

## 3. APIドキュメント構造 (`docs/api/python/<model_name>.md`)

### 3.1 必須セクション（順序厳守）

```markdown
# [モデル名] API

[モデルの用途を1行で説明]

## 概要

[モデルの簡潔な説明（2-3文）]
[主な用途・適用分野]

詳細な理論的背景は[{モデル名}理論](../../models/{model_name}.md)を参照してください。

## API使用方法

### 基本的な価格計算

```python
from quantforge.models import {module_name}

# コールオプション価格
# パラメータ: [パラメータ名を列挙]
call_price = {module_name}.call_price(...)

# プットオプション価格
# パラメータ: [パラメータ名を列挙]
put_price = {module_name}.put_price(...)
```

### バッチ処理

[バッチ処理の例]

### グリークス計算

[グリークス計算の例]

### インプライドボラティリティ

[IV計算の例（対応している場合）]

## パラメータ説明

### 入力パラメータ

[パラメータ表 - naming_conventions.mdの名前を使用]

### バッチ処理用パラメータ

[バッチ用パラメータ表]

## 価格式（参考）

[簡潔な数式のみ - 詳細は理論ドキュメントへ誘導]

## エラーハンドリング

[エラー条件と処理]

## パフォーマンス指標

[処理速度の目安]

## 使用例

[実践的な使用例]

## 関連情報

- [{他モデル名} API]({other_model}.md)
- [インプライドボラティリティAPI](implied_vol.md)
- [{モデル名}理論的背景](../../models/{model_name}.md)
```

### 3.2 コード例の規則

**naming_conventions.mdに基づく規則：**

1. **関数パラメータ**: 必ず省略形を使用
   - 共通: `k`(strike), `t`(time), `r`(rate), `sigma`(volatility)
   - Black-Scholes系: `s`(spot), `f`(forward), `q`(dividend)
   - その他はnaming_conventions.mdのカタログ参照

2. **位置引数のみ使用**
   ```python
   # ✅ 正しい
   price = model.call_price(100.0, 105.0, 1.0, 0.05, 0.2)
   
   # ❌ 間違い（キーワード引数）
   price = model.call_price(spot=100.0, strike=105.0, ...)
   ```

3. **パラメータ説明はコメントで記載**
   ```python
   # パラメータ: s(spot), k(strike), t(time), r(rate), sigma
   price = black_scholes.call_price(100.0, 105.0, 1.0, 0.05, 0.2)
   ```

## 4. 理論ドキュメント構造 (`docs/models/<model_name>.md`)

### 4.1 必須セクション（順序厳守）

```markdown
# [モデル名]

[モデルの理論的位置づけを1行で説明]

## 理論的背景

### 基本概念
[モデルの基本的な考え方]

### 基本仮定
[数学的仮定のリスト]

## 価格式の導出

### [モデル名]方程式
[偏微分方程式]

### 境界条件
[コール・プットの境界条件]

## 解析解

### ヨーロピアンコール
[価格式]

### ヨーロピアンプット
[価格式]

## グリークス

[各グリークスの導出式]

## [他モデル]との関係

[関連モデルとの数学的関係]

## 応用分野

[実務での具体的な使用例]

## 数値計算上の考慮事項

### 精度要件
[数値精度の目標と実装上の注意]

### 数値的課題と対策
[計算上の問題と解決策]

## モデルの限界と拡張

### 限界
[モデルの制約]

### 拡張モデル
[発展的なモデル]

## 実装例（概念）

```python
# 概念的な実装例（実際のAPIとは異なる）
def {model}_call(params):
    ...
```

## 参考文献

[学術論文・書籍のリスト]

## 関連ドキュメント

- [{モデル名} API](../api/python/{model_name}.md)
- [関連モデル](related_model.md)
```

## 5. pricing.md更新ルール

### 5.1 モデル追加時の更新箇所

```markdown
### [新モデル名]
[1行説明]。[主要入力パラメータ]を入力として使用します。

```python
from quantforge.models import {module_name}

# パラメータ: [省略形パラメータリスト]
price = {module_name}.call_price(...)
```

詳細: [[モデル名] API]({model_name}.md)
```

### 5.2 モデル選択ガイドへの追加

適切なセクション（使用する場合/パラメータの対応など）に新モデルの情報を追加

## 6. implied_vol.md更新ルール

インプライドボラティリティ機能を持つモデルの場合：

```markdown
### [モデル名]

[モデル固有のIV計算の説明]

```python
from quantforge.models import {module_name}

# パラメータ: price, [モデル固有パラメータ], is_call
iv = {module_name}.implied_volatility(...)
```
```

## 7. toctree更新ルール

`docs/index.md`の更新：

```rst
```{toctree}
:caption: API リファレンス
:maxdepth: 2

api/python/index
api/python/pricing
api/python/black_scholes
api/python/black76
api/python/{new_model}  # アルファベット順に追加
api/python/implied_vol
```

```{toctree}
:caption: 数理モデル
:maxdepth: 2

models/index
models/black_scholes
models/black76
models/{new_model}  # アルファベット順に追加
```
```

## 8. チェックリスト

### 8.1 ドキュメント作成前

- [ ] `naming_conventions.md`でパラメータ名を確認
- [ ] 既存モデルのドキュメントを参考に構造確認
- [ ] 理論とAPIの分離を意識

### 8.2 ドキュメント作成後

- [ ] APIドキュメント作成（全必須セクション含む）
- [ ] 理論ドキュメント作成（全必須セクション含む）
- [ ] pricing.md更新（モデル概要追加）
- [ ] implied_vol.md更新（IV機能がある場合）
- [ ] index.md toctree更新
- [ ] パラメータ名が省略形を使用
- [ ] コード例が位置引数のみ使用
- [ ] パラメータ説明がコメントで記載
- [ ] 相互リンクが正しく設定
- [ ] Sphinxビルドエラーなし

## 9. 参照ドキュメント

- `docs/internal/naming_conventions.md` - パラメータ命名規則
- `docs/api/python/black_scholes.md` - APIドキュメントの例
- `docs/api/python/black76.md` - APIドキュメントの例
- `docs/models/black_scholes.md` - 理論ドキュメントの例
- `docs/models/black76.md` - 理論ドキュメントの例
# Naming Protocol for AI

AIが命名を扱う際の行動原則。具体的な命名規則は @docs/ja/internal/naming_conventions.md を参照。

## 基本原則

**命名は創造ではなく選択。独自判断での命名は技術的負債。**

## 命名選択フロー

```
1. @docs/ja/internal/naming_conventions.md のカタログを確認
2. カタログに存在 → その名前を使用
3. カタログに不在 → 以下の手順を実行：
   
   if 業界標準が明確:
       理由と参考資料を提示してユーザー承認を求める
   else:
       複数の選択肢を提示してユーザーに選択を依頼
```

## 禁止事項

- ❌ **その場での「創作」** - 「こっちの方が分かりやすい」という主観的判断
- ❌ **一貫性のない混在** - 同じファイルでspot/sを混在
- ❌ **カタログにない省略形の独自作成** - 勝手な省略は混乱の元
- ❌ **過去の命名への回帰** - 一度変更した命名を勝手に戻す

## 推奨事項

- ✅ **不明な場合は必ず確認** - 推測より確認
- ✅ **naming_conventions.mdを常に参照** - 記憶に頼らない
- ✅ **改善案はユーザーに提案** - 独断での変更は避ける
- ✅ **カタログ更新も同時に提案** - 新規追加時は文書化

## 実装時のチェックリスト

```
□ naming_conventions.mdのカタログを確認した
□ 既存コードでの使用例を検索した
□ カタログにない場合はユーザーに確認した
□ エラーメッセージでもAPI命名を使用した
□ ドキュメントでも一貫した命名を使用した
```

## 改善提案のテンプレート

```
「現在のカタログでは '{current}' を{用途}に使用していますが、
{理由}により '{proposed}' の方が適切と考えられます。

参考：{出典}

以下の変更を提案します：
1. naming_conventions.mdに '{proposed}' を追加
2. 既存コードの '{current}' を '{proposed}' に更新

この変更を承認しますか？」
```

## 具体例

### ❌ 悪い例：独自判断
```python
# AIが「分かりやすい」と判断して独自に命名
def calculate_option_value(current_price, exercise_price, ...):
```

### ✅ 良い例：カタログに従う
```python
# naming_conventions.mdに従って命名
def call_price(s, k, t, r, sigma):
```

### ✅ 良い例：改善提案
```
「現在のカタログでは 's' をスポット価格に使用していますが、
Black76では先物価格なので 'f' の方が適切です。
参考：Hull (2018) Options, Futures, and Other Derivatives

naming_conventions.mdの更新も含めて承認しますか？」
```

## エラーメッセージでの命名

APIパラメータ名を使用：
```python
# ✅ 良い例
raise ValueError("s must be positive")
raise ValueError("k, t, and sigma must be positive")

# ❌ 悪い例
raise ValueError("spot_price must be positive")  # APIでは 's' を使用
```

## ドキュメントでの命名

- 初出時: フルネームを併記 `s (spot price)`
- 以降: 省略形のみ `s = 100.0`
- コード例: API通りの省略形を使用

## 命名の一貫性維持

### コード内での統一
```python
# ✅ 一貫性あり
def call_price(s, k, t, r, sigma):
    if s <= 0:
        raise ValueError("s must be positive")
    # ...

# ❌ 一貫性なし
def call_price(s, k, t, r, sigma):
    if spot <= 0:  # 突然 'spot' が出現
        raise ValueError("spot must be positive")
```

### モジュール間での統一
- Black-Scholes: `s` (spot)
- Black76: `f` (forward)
- 両方で共通: `k, t, r, sigma`

## 新規命名の承認プロセス

1. **既存カタログの確認** - まず再利用可能な名前を探す
2. **業界標準の調査** - 学術論文、既存ライブラリを参照
3. **ユーザー提案** - 理由と参考資料を含めて提示
4. **カタログ更新** - 承認後、naming_conventions.mdに追加

詳細な命名規則は @docs/ja/internal/naming_conventions.md を参照。
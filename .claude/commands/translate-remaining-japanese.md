# 英語ドキュメント内の残存日本語翻訳タスク

## 役割
あなたは優秀な技術ドキュメント翻訳者です。金融工学とプログラミングの専門知識を持ち、QuantForgeプロジェクトのドキュメント品質向上を担当します。

## メインタスク
`docs/en/**/*.md` 内のすべての日本語テキストを適切な英語に翻訳してください。

## 詳細な指示

### 1. 翻訳対象
- **ドキュメント本文**: すべての日本語説明文を英語化
- **コードコメント**: コードブロック内の日本語コメントも英訳
  ```python
  # 現在価格 → # Current price (spot)
  # コールオプション価格 → # Call option price
  ```
- **エラーメッセージ**: 日本語のエラーメッセージも英訳
- **インラインコメント**: コード内のすべての日本語コメント

### 2. 翻訳不要な要素（維持すべきもの）
- **API変数名**: `s, k, t, r, sigma` などの確立された変数名
- **URLとパス**: ファイルパスやWebリンク
- **数式**: LaTeX記法や数学表記
- **固有名詞**: QuantForge、PLaMo-2など

### 3. 参照リソース
- **日本語オリジナル**: `docs/ja/**/*.md` の対応ファイルを参照
- **既存の英訳**: すでに翻訳済みの部分のスタイルに合わせる
- **命名規則**: `docs/internal/naming_conventions.md` を遵守

### 4. 技術用語の統一
金融・オプション用語は業界標準の英語表記を使用：
- 現在価格 → spot price (または単に spot)
- 権利行使価格 → strike price (または単に strike)
- 満期までの時間 → time to maturity
- 無リスク金利 → risk-free rate
- ボラティリティ → volatility (sigma)
- プット・コール・パリティ → put-call parity
- インプライド・ボラティリティ → implied volatility
- グリークス → Greeks

### 5. 翻訳の優先順位

#### 最優先（ユーザー向けドキュメント）
1. `docs/en/user_guide/basic_usage.md` - コード内コメント
2. `docs/en/user_guide/examples.md` - コード内コメント  
3. `docs/en/quickstart.md` - 残存する日本語部分

#### 高優先（APIドキュメント）
4. `docs/en/user_guide/numpy_integration.md` - コード内コメント
5. `docs/en/user_guide/advanced_models.md` - コード内コメント

#### 中優先（インストール関連）
6. `docs/en/installation.md` - TestPyPI関連の日本語コメント

### 6. 品質基準

#### 文体とトーン
- **簡潔で明確**: 技術文書として適切な簡潔さ
- **一貫性**: 既存の英語ドキュメントと同じトーン
- **初心者配慮**: 専門用語には必要に応じて簡単な説明を追加

#### 翻訳例
```python
# ❌ 悪い例（直訳的）
# The present value of the underlying asset  

# ✅ 良い例（簡潔）
# Spot price

# ❌ 悪い例（日本語残存）
prices = black_scholes.call_price_batch(
    spots=spots,  # 現在価格の配列
    
# ✅ 良い例
prices = black_scholes.call_price_batch(
    spots=spots,  # Array of spot prices
```

### 7. 作業前チェック

実行すべきコマンド：
```bash
# 日本語が残っているファイルを特定
grep -r '[ぁ-んァ-ヶ一-龠]' docs/en/ --include="*.md"

# 各ファイルの日本語行数をカウント
for file in docs/en/**/*.md; do
  count=$(grep -c '[ぁ-んァ-ヶ一-龠]' "$file" 2>/dev/null || echo 0)
  if [ "$count" -gt 0 ]; then
    echo "$file: $count lines"
  fi
done
```

### 8. 作業後の検証

#### 必須チェック
- [ ] すべての日本語が英訳されている
- [ ] コードサンプルが動作する
- [ ] Sphinxビルドが成功する
- [ ] 内部リンクが有効である

#### 確認コマンド
```bash
# ビルドテスト
uv run sphinx-build -b html docs/en docs/en/_build/html

# 残存日本語チェック
grep -r '[ぁ-んァ-ヶ一-龠]' docs/en/ --include="*.md" | wc -l
# 結果が0であることを確認
```

### 9. コミットメッセージ規約

```
docs(en): translate remaining Japanese text in English documentation

- Translate all Japanese comments in code examples
- Ensure consistency with established terminology
- Maintain API parameter naming conventions (s, k, t, r, sigma)
- Verify all code examples remain functional

This completes the English documentation translation for global accessibility.
```

### 10. 注意事項

⚠️ **重要な警告**：
- 変数名 `s, k, t, r, sigma` は絶対に変更しない
- 既に確立されたAPIの命名は維持する
- コードの動作を変更しない（コメントのみ翻訳）
- 数式やLaTeX記法は触らない

### 11. 完了基準

- [ ] `grep -r '[ぁ-んァ-ヶ一-龠]' docs/en/` の結果が0件
- [ ] すべてのコードサンプルが動作確認済み
- [ ] Sphinx buildエラーなし
- [ ] GitHub Pagesで正常表示確認

---

このタスクを実行することで、QuantForgeの英語ドキュメントが完全に国際化対応され、グローバルなユーザーベースに対応できるようになります。
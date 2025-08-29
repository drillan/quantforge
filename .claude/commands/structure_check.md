# MyST構造比較コマンド

## 概要
日英ドキュメントのMyST記法構造を比較し、不一致を検出・修正します。

## 処理フロー

### 1. 構造比較の実行

引数 `$ARGUMENTS` が指定された場合、以下のコマンドでMyST構造比較を実行します：

```bash
# ファイル名から拡張子を除去してベース名を取得
BASENAME=$(basename "$ARGUMENTS" .md)

# JSONレポートの生成
python translations/compare/structure_compare.py \
  --ja $ARGUMENTS \
  --en ${ARGUMENTS/\/ja\//\/en\/} \
  --format json \
  --output translations/compare/reports/latest/$BASENAME
```

生成されるJSONファイル：
`translations/compare/reports/latest/${BASENAME}.json`

例：
- 入力: `docs/ja/models/black_scholes.md`
- 英語側: `docs/en/models/black_scholes.md` (自動変換)
- 出力: `translations/compare/reports/latest/black_scholes.json`

### 2. 構造確認と修正

JSONレポートを基に以下を確認します：

#### 2.1 メタデータ確認
```json
"metadata": {
  "timestamp": "実行時刻",
  "ja_file": "日本語ファイルパス",
  "en_file": "英語ファイルパス",
  "tool_version": "1.1.0"
}
```

#### 2.2 同期状態の評価
```json
"summary": {
  "sync_rate": 38.2,  // 同期率（%）
  "severity": "high", // low/medium/high
  "issues": {
    "missing_in_en": 16,  // 英語側で不足
    "missing_in_ja": 18,  // 日本語側で不足
    "type_mismatch": 0    // タイプ不一致
  }
}
```

#### 2.3 不一致の修正手順

**missing_in_en の修正例：**
```json
{
  "name": "black-scholes-analytical-solution",
  "type": "header",
  "level": 2,
  "parent": "black-scholes",
  "caption": "解析解",
  "suggestion": "Add level 2 section '解析解' under 'black-scholes'"
}
```
→ 英語ファイルの該当箇所に以下を追加：
```markdown
(black-scholes-analytical-solution)=
## Analytical Solutions
```

**missing_in_ja の修正例：**
```json
{
  "name": "black-scholes-eq-d1-d2",
  "type": "math",
  "suggestion": "Add math equation 'black-scholes-eq-d1-d2'"
}
```
→ 日本語ファイルに数式ブロックを追加

### 3. 引数なしの場合の処理

`$ARGUMENTS` が指定されない場合：

```bash
# 全ドキュメントの一括チェック
cd translations/compare
./check_all.sh
```

処理対象ディレクトリ：
- `docs/ja/models/*.md` ↔ `docs/en/models/*.md`
- `docs/ja/api/python/*.md` ↔ `docs/en/api/python/*.md`
- `docs/ja/user_guide/*.md` ↔ `docs/en/user_guide/*.md`

レポート出力（各ファイルごとに3形式）：
```
translations/compare/reports/latest/
├── models/
│   ├── black_scholes.json  # AI処理用（推奨）
│   ├── black_scholes.csv   # 人間レビュー用
│   └── merton.json
│       ...
├── api/python/
│   └── ...
└── user_guide/
    └── ...
```

**重要**: AIアシスタントはJSONファイルを優先的に使用してください。CSVは人間のレビュー用です。

## 修正の優先順位

| 同期率 | 重要度 | 対応 |
|--------|--------|------|
| 70%未満 | HIGH | 即座に修正が必要 |
| 70-89% | MEDIUM | 重要な不一致を優先的に修正 |
| 90%以上 | LOW | 軽微な調整のみ |

## 修正時の注意事項

### name属性の一貫性
- 両言語で完全に同じname属性を使用
- 例: `(black-scholes-greeks)=` は日英両方で同一

### 階層構造の保持
- ヘッダーレベル（#の数）を維持
- 親子関係を正確に再現
- 例: level 3のヘッダーは必ずlevel 2の子要素

### 要素タイプの統一
- 同じnameの要素は同じタイプ（header, math, code-block等）
- タイプ不一致は即座に修正

### キャプションの扱い
- キャプションは翻訳による違いを許容
- name属性で対応関係を管理
- 例: "グリークス" ↔ "Greeks" は問題なし

## 実行例

```bash
# 単一ファイルの比較
/structure_compare docs/ja/models/black_scholes.md

# APIドキュメントの比較
/structure_compare docs/ja/api/python/pricing.md

# 全ファイルの一括チェック
/structure_compare
```

## 終了コード

- `0`: 完全に同期（修正不要）
- `1`: 中程度の問題（MEDIUM以下）
- `2`: 深刻な問題（HIGH）
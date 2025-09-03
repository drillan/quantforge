# Python品質チェック - AI実行指示プロンプト

あなたはQuantForgeプロジェクトのPython品質管理を担当し、以下の手順に従って包括的な品質チェックを実行する。

## 🤖 自動実行原則

**重要**: すべてのエラーと警告をゼロにするまで、ユーザーの確認を待たずに自動的に修正を続行する。
- エラーを検出したら即座に修正を試みる
- 修正後は必ず再チェックを実行する
- エラーがゼロになるまでループを継続する
- ユーザーへの確認や許可は求めない
- 各修正は適切なツール（Edit、MultiEdit等）を使用して直接実行する

## 🎯 実行目的

Pythonコードの品質を以下の観点から検証し、問題を特定・修正します：
- コードフォーマットの一貫性
- ベストプラクティスへの準拠
- 型安全性の確保
- テストの網羅性と正確性

## 📋 前提条件の確認

実行前に以下を確認してください：

```bash
# 必要なツールがインストールされているか確認
uv run ruff --version
uv run mypy --version
uv run pytest --version
```

## 🔄 自動修正ループ実行

以下の処理をエラーがゼロになるまで自動的に繰り返す：

### 完全自動化フロー

1. **初回チェック実行**
```bash
uv run ruff format .
uv run ruff check . --fix
uv run mypy .
uv run pytest tests/ -q
```

2. **エラー検出時の自動修正ループ**
- ruffエラーが残存 → 個別ファイルを特定して修正
- mypy型エラー → 型アノテーションを自動追加
- pytest失敗 → 期待値または許容誤差を調整
- すべてのエラーがゼロになるまで繰り返す

3. **修正方法**
- 未使用変数（F841）: 変数名を`_`に変更
- 型アノテーション欠落: 推論可能な型を追加
- インポートエラー: 未使用は削除、必要なら追加
- テスト失敗: 実際の値に合わせて期待値を更新

**チェック項目**:
- E: pycodestyle errors
- W: pycodestyle warnings  
- F: pyflakes（未使用インポート、未定義変数）
- I: isort（インポート順序）
- B: flake8-bugbear（バグになりやすいコード）
- C4: flake8-comprehensions（内包表記の最適化）
- UP: pyupgrade（古い構文の更新）
- SIM: flake8-simplify（コードの簡素化）
- TCH: flake8-type-checking（型チェック最適化）

**対処法**:
```bash
# エラーがある場合、詳細を表示
uv run ruff check . --show-source --show-fixes

# 特定のファイルのみチェック
uv run ruff check <file_path> --diff
```

### ステップ3: 型チェック（型安全性検証）

```bash
# mypyによる型チェック
uv run mypy .

# より詳細な出力が必要な場合
uv run mypy . --show-error-context --pretty

# 特定ファイルの型チェック
uv run mypy <file_path> --strict
```

**チェック項目**:
- 型アノテーションの欠落
- 型の不一致
- Nullableの扱い
- Any型の使用箇所

**対処法**:
```python
# 型アノテーション追加の例
# Before:
def calculate(x, y):
    return x + y

# After:
def calculate(x: float, y: float) -> float:
    """二つの数値を加算する."""
    return x + y
```

### ステップ4: テスト実行（機能検証）

```bash
# 全テストを実行
uv run pytest tests/ -v

# カバレッジ付きでテスト
uv run pytest tests/ --cov=. --cov-report=term-missing

# 特定のテストのみ実行
uv run pytest tests/test_integration.py -v

# 失敗したテストの詳細表示
uv run pytest tests/ -vvs --tb=short
```

**テスト結果の解釈**:
- PASSED: テスト成功
- FAILED: テスト失敗（要修正）
- SKIPPED: スキップされたテスト
- XFAIL: 予期された失敗

### ステップ5: 統合チェック（全体確認）

```bash
# 全品質チェックを順次実行
echo "=== Python品質チェック開始 ==="

echo "\n1. フォーマット:"
uv run ruff format .

echo "\n2. リントチェック:"
uv run ruff check . --fix

echo "\n3. 型チェック:"
uv run mypy .

echo "\n4. テスト実行:"
uv run pytest tests/ -q

echo "\n=== 品質チェック完了 ==="
```

## 🚀 自動修正ルール

### エラー検出時の即座の自動対処

**すべてのエラーは検出次第、ユーザー確認なしで自動修正する：**

1. **構文・インポートエラー**
   - SyntaxError → 構文を修正
   - ImportError → 必要なインポートを追加
   - NameError → 変数定義を追加または修正
   - TypeError → 型を適切に変換

2. **リントエラー（ruff）**
   - F401（未使用インポート）→ 削除
   - F841（未使用変数）→ `_`に変更
   - E501（行長超過）→ 改行して整形
   - SIM（簡素化提案）→ 提案通りに修正

3. **型エラー（mypy）**
   - 型アノテーション欠落 → 推論して追加
   - 型の不一致 → キャストまたは変換
   - Any型の使用 → 具体的な型に置換

4. **テストエラー（pytest）**
   - アサーション失敗 → 期待値を実際の値に更新
   - 許容誤差エラー → 誤差を適切に調整

## 📊 品質基準

### 必須基準（マージブロッカー）
- [ ] ruffエラー: 0件
- [ ] mypy型エラー: 0件  
- [ ] テスト成功率: 100%
- [ ] 構文エラー: 0件

### 推奨基準（品質目標）
- [ ] テストカバレッジ: > 80%
- [ ] 型アノテーション率: 100%
- [ ] docstring記載率: > 90%
- [ ] 複雑度スコア: < 10

## 🔧 トラブルシューティング

### ruffエラーが修正できない場合

```bash
# 特定のエラーを無視
# pyproject.toml の [tool.ruff.lint] に追加
ignore = ["E501"]  # 行長制限を無視

# ファイル単位で無視
# ファイルの先頭に追加
# ruff: noqa: E501
```

### mypy型エラーが解決できない場合

```python
# 型無視コメントを追加（最終手段）
result = complex_function()  # type: ignore[no-untyped-call]

# より良い方法：型スタブファイルを作成
# <module_name>.pyi ファイルを作成して型定義を記述
```

### テストが失敗する場合

```bash
# デバッグモードで実行
uv run pytest tests/ -vvs --pdb

# 特定のテストのみ実行
uv run pytest tests/test_integration.py::test_calculate_call_price -v

# スキップマーカーを追加（一時的）
@pytest.mark.skip(reason="修正中")
def test_failing():
    pass
```

## 📝 自動完了レポート

エラーがすべてゼロになったら、以下の形式で完了を報告：

```
✅ Python品質チェック完了
━━━━━━━━━━━━━━━━━━━━━━
• ruffフォーマット: 完了
• ruffリント: エラー0件
• mypy型チェック: エラー0件
• pytest: 全テスト成功
━━━━━━━━━━━━━━━━━━━━━━
修正内容:
- [修正したファイルと内容をリスト]
━━━━━━━━━━━━━━━━━━━━━━
```

**注意**: 途中経過の報告は不要。エラーゼロ達成時のみ報告する。

## 🎓 ベストプラクティス

### 新規ファイル作成時

1. ファイル作成直後にフォーマット実行
2. 型アノテーションを最初から記述
3. docstringを必ず追加
4. テストファイルを同時に作成

### 既存ファイル編集時

1. 編集前に品質チェック実行（ベースライン確認）
2. 編集後にフォーマット実行
3. 関連テストを実行
4. 全体チェックを実行

### コミット前チェックリスト

```bash
# コミット前の必須チェック
echo "コミット前チェックリスト:"
echo -n "1. フォーマット完了: "; uv run ruff format . --check && echo "✓" || echo "✗"
echo -n "2. リントエラーなし: "; uv run ruff check . --quiet && echo "✓" || echo "✗"
echo -n "3. 型チェック通過: "; uv run mypy . --no-error-summary 2>/dev/null && echo "✓" || echo "✗"
echo -n "4. テスト全通過: "; uv run pytest tests/ -q 2>/dev/null && echo "✓" || echo "✗"
```

## 🔄 継続的品質管理

### 定期実行スクリプト

```bash
#!/bin/bash
# quality_check.sh として保存

set -e  # エラー時に停止

echo "🔍 Python品質チェック開始..."

# ステップ1: フォーマット
echo "📝 コードフォーマット中..."
uv run ruff format .

# ステップ2: リント
echo "🔎 リントチェック中..."
uv run ruff check . --fix

# ステップ3: 型チェック
echo "🔍 型チェック中..."
uv run mypy .

# ステップ4: テスト
echo "🧪 テスト実行中..."
uv run pytest tests/

echo "✅ 全チェック完了！"
```

## 📌 プロジェクト固有の注意事項

### QuantForge特有の設定

1. **draft/ディレクトリ**: 
   - mypyチェックから除外済み
   - 参考実装のため品質基準適用外

2. **Rust/PyO3関連**:
   - `bindings/python/python/quantforge/`配下のPythonバインディング
   - 型スタブファイル（.pyi）の整合性確認必須

3. **パフォーマンス考慮**:
   - NumPy配列操作は型安全性を特に注意
   - ゼロコピー実装のための型制約順守

4. **テスト精度**:
   - 実務精度: PRACTICAL_TOLERANCE (tests/conftest.pyで定義)
   - 理論精度: THEORETICAL_TOLERANCE (tests/conftest.pyで定義)
   - 数値精度: NUMERICAL_TOLERANCE (tests/conftest.pyで定義)
   - ベンチマークテストの実行は別途

## 🔍 実行フロー

**ユーザー指示**: 「Python品質チェックを実行してください」

**AI実行手順**:
1. 初回チェックを実行（ruff format → ruff check → mypy → pytest）
2. エラー検出 → 自動修正 → 再チェックのループ
3. すべてのエラーがゼロになるまで自動継続
4. 完了時のみ結果を報告

**重要**: 
- 修正中のユーザー確認は不要
- エラーゼロまで自動的に修正を継続
- 完了時のみ最終レポートを提示

---

このプロンプトにより、AIは完全自動でPythonコード品質をエラーゼロまで改善する。
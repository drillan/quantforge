# [Both] 包括的品質改善 実装計画

## メタデータ
- **作成日**: 2025-09-02
- **言語**: Both (Python + Rust)
- **ステータス**: DRAFT
- **推定規模**: 大規模
- **推定作業時間**: 4-6時間（自動化により短縮）
- **対象**: 全コードベース

## ⚠️ Critical Rules適用
本計画は以下のCritical Rulesを厳格に適用します：
- **C002**: エラー迂回禁止 - すべてのエラーを即座に修正
- **C004/C014**: 理想実装ファースト - 妥協なき品質実現
- **C011-3**: ハードコード禁止 - すべての定数を適切に定義
- **C012**: DRY原則 - コード重複を徹底排除

## タスク規模判定

### 判定基準
- 推定修正行数: 500-1000行
- 影響範囲: 全体（src/, python/, tests/）
- 自動化レベル: 90%以上（エラー自動修正ループ）
- PyO3連携: 必須（品質検証含む）

### 規模判定結果
**大規模タスク** - 4つの品質管理コマンドを統合実行

## 実行戦略

### 基本方針
1. **Python優先**: 修正が高速で効果が即座に見える
2. **自動修正ループ**: エラーゼロまで人手介入なし
3. **並列実行**: 独立したツールは同時実行
4. **技術的負債ゼロ**: 妥協なき品質追求

## 実行フェーズ

### Phase 1: Python品質改善（1-2時間）

#### Step 1: Python品質チェック（python-quality-check.md適用）
```bash
# 自動修正ループ（エラーゼロまで継続）
while true; do
    uv run ruff format .
    uv run ruff check . --fix
    if uv run mypy . && uv run pytest tests/ -q; then
        break
    fi
done
```

**チェック項目**:
- [ ] ruffフォーマット: 差分なし
- [ ] ruffリント: エラー0件
- [ ] mypy型チェック: エラー0件（strict mode）
- [ ] pytest: 全テスト成功
- [ ] カバレッジ: 80%以上

#### Step 2: Pythonリファクタリング（python-refactor.md適用）
```bash
# 重複検出と自動リファクタリング
similarity-py --threshold 0.80 --min-lines 5 quantforge/

# 重複率が閾値を超えた場合の対処
# - ジェネリクス/プロトコルによる統一
# - 共通関数の抽出
# - DRY原則の徹底適用
```

**実施内容**:
- [ ] コード重複率: 5%未満達成
- [ ] 型アノテーション: 100%完全化
- [ ] NumPyベクトル化: 該当箇所すべて
- [ ] エラーハンドリング: 統一された例外クラス使用
- [ ] ゼロコピー実装: PyO3連携部分

### Phase 2: Rust品質改善（2-3時間）

#### Step 3: Rust品質チェック（rust-quality-check.md適用）
```bash
# 自動修正ループ（エラーゼロまで継続）
while true; do
    cargo fmt --all
    cargo clippy --all-targets --all-features -- -D warnings
    if cargo test --release && uv run maturin develop --release && uv run pytest tests/ -q; then
        break
    fi
done
```

**チェック項目**:
- [ ] rustfmt: 差分なし
- [ ] clippy: 警告0件（pedantic含む）
- [ ] cargo test: 全テスト成功
- [ ] cargo doc: 警告0件
- [ ] maturin develop: ビルド成功
- [ ] 数値精度: エラー率 < 1e-3

#### Step 4: Rustリファクタリング（rust-refactor.md適用）
```bash
# 重複検出と自動リファクタリング
similarity-rs --threshold 0.80 --min-lines 5 --skip-test src/

# パフォーマンス最適化
# - 並列化閾値の調整（実測基準）
# - キャッシュ最適化
# - インライン化ヒント追加
```

**実施内容**:
- [ ] コード重複率: 5%未満達成
- [ ] ジェネリクス統一: 汎用トレイト実装
- [ ] 並列化閾値: 実測に基づく最適値設定
- [ ] PyO3最適化: ゼロコピー確認
- [ ] unsafe使用: 最小限かつSAFETYコメント完備

### Phase 3: 統合検証（30分）

#### Step 5: 統合テスト実行
```bash
# Python-Rust連携テスト
uv run pytest tests/test_integration.py -v

# パフォーマンスベンチマーク
uv run python benchmarks/run_practical_scenarios.py

# メモリリークチェック（オプション）
valgrind --leak-check=full python -c "import quantforge; ..."
```

**検証項目**:
- [ ] PyO3連携: エラーなし
- [ ] パフォーマンス: 目標値達成
  - Black-Scholes単一: < 10ns
  - バッチ100万件: < 20ms
- [ ] メモリ使用: 入力データの2倍以内
- [ ] 精度検証: Golden Masterテスト成功

### Phase 4: 最終品質レポート生成

```bash
# 品質メトリクス集計スクリプト
cat << 'EOF' > /tmp/quality_report.sh
#!/bin/bash
echo "✅ 包括的品質改善完了"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "【Python】"
echo "• ruff: $(uv run ruff check . 2>&1 | grep -c 'error') エラー"
echo "• mypy: $(uv run mypy . 2>&1 | grep -c 'error') エラー"
echo "• pytest: $(uv run pytest tests/ -q 2>&1 | tail -1)"
echo "• カバレッジ: $(uv run pytest --cov=quantforge --cov-report=term | grep TOTAL | awk '{print $4}')"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "【Rust】"
echo "• clippy: $(cargo clippy 2>&1 | grep -c 'warning') 警告"
echo "• test: $(cargo test --release 2>&1 | grep 'test result')"
echo "• unsafe使用: $(grep -r 'unsafe' src/ | wc -l) 箇所"
echo "━━━━━━━━━━━━━━━━━━━━━━"
EOF

bash /tmp/quality_report.sh
```

## 成功基準

### Python品質基準
| 項目 | 必須基準 | 達成目標 |
|------|----------|----------|
| ruffエラー | 0件 | ✅ |
| mypy型エラー | 0件 | ✅ |
| pytest成功率 | 100% | ✅ |
| 型カバレッジ | 100% | ✅ |
| テストカバレッジ | 80%以上 | 90%以上 |
| コード重複率 | < 10% | < 5% |

### Rust品質基準
| 項目 | 必須基準 | 達成目標 |
|------|----------|----------|
| clippy警告 | 0件 | ✅ |
| cargo test | 全成功 | ✅ |
| 数値精度 | < 1e-3 | < 1e-5 |
| unsafe使用 | 4箇所以下 | 最小限 |
| コード重複率 | < 10% | < 5% |
| ドキュメント | 警告0件 | 100%記載 |

### 統合品質基準
| 項目 | 基準 |
|------|------|
| PyO3連携 | エラーなし |
| メモリリーク | なし |
| パフォーマンス | 目標値達成 |
| 後方互換性 | 不要（ユーザーゼロ） |

## 自動化の特徴

### エラー自動修正フロー
```
1. エラー検出
    ↓
2. 修正可能？
    Yes → 即座に自動修正 → 1へ戻る
    No → 作業停止、ユーザーに報告
    ↓
3. エラーゼロ？
    No → 1へ戻る
    Yes → 次のフェーズへ
```

### 並列実行可能なタスク
- ruff format + mypy（別プロセス）
- cargo fmt + cargo clippy（別プロセス）
- 複数ファイルの修正（並列編集）

### 無限ループ防止
- 最大試行回数: 10回
- タイムアウト: 各ツール5分
- 進捗なし検出: 3回連続同一エラー

## リスクと対策

| リスク | 影響度 | 発生確率 | 対策 |
|--------|--------|----------|------|
| 自動修正による意図しない変更 | 高 | 低 | git diff確認、必要時revert |
| テスト失敗の連鎖 | 中 | 中 | 個別修正、根本原因特定 |
| パフォーマンス劣化 | 高 | 低 | ベンチマーク前後比較 |
| 型アノテーション破壊 | 中 | 低 | mypy incrementalモード |
| CI/CD破壊 | 高 | 極低 | ローカル実行、PR前確認 |

## チェックリスト

### 実装前
- [ ] gitブランチ作成（plan/quality-improvement）
- [ ] 現在の品質メトリクス記録
- [ ] Critical Rules確認（C001-C014）

### 実装中
- [ ] Phase 1: Python品質改善
- [ ] Phase 2: Rust品質改善
- [ ] Phase 3: 統合検証
- [ ] Phase 4: レポート生成

### 実装後
- [ ] 全品質ゲート通過確認
- [ ] git diff レビュー
- [ ] コミット（メッセージ: "chore: comprehensive quality improvement"）
- [ ] 計画をarchive/へ移動

## 実行コマンド一覧

```bash
# Python品質チェック（自動修正付き）
uv run ruff format .
uv run ruff check . --fix
uv run mypy .
uv run pytest tests/ --cov=quantforge

# Pythonリファクタリング判断
similarity-py --threshold 0.80 --min-lines 5 quantforge/

# Rust品質チェック（自動修正付き）
cargo fmt --all
cargo clippy --all-targets --all-features -- -D warnings
cargo test --release
cargo doc --no-deps --all-features

# Rustリファクタリング判断
similarity-rs --threshold 0.80 --min-lines 5 --skip-test src/

# PyO3統合確認
uv run maturin develop --release
uv run pytest tests/test_integration.py

# パフォーマンス測定
uv run python benchmarks/run_practical_scenarios.py
cargo bench
```

## 成果物

- [ ] エラー・警告ゼロのコードベース
- [ ] 完全な型アノテーション（Python）
- [ ] 最適化されたパフォーマンス
- [ ] 統一されたエラーハンドリング
- [ ] 品質改善レポート
- [ ] 更新されたベンチマーク結果

## 備考

- 本計画は完全自動化を前提とし、人手介入を最小化
- Critical Rules違反は即座に修正（C002適用）
- 技術的負債は一切作らない（C004/C014適用）
- 実行時間は自動化により大幅短縮可能

## 参照

- `.claude/commands/rust-refactor.md`
- `.claude/commands/rust-quality-check.md`
- `.claude/commands/python-refactor.md`
- `.claude/commands/python-quality-check.md`
- `.claude/critical-rules.xml`
- `.claude/development-principles.md`
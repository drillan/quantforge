# [Python] PyPI本番リリース準備 実装計画

## メタデータ
- **作成日**: 2025-01-30
- **言語**: Python/Both (設定ファイル更新)
- **ステータス**: ACTIVE
- **推定規模**: 小規模
- **推定コード行数**: <100行（主に設定ファイル変更）
- **対象モジュール**: pyproject.toml, Cargo.toml, .github/workflows/, README.md, CHANGELOG.md

## ⚠️ 技術的負債ゼロの原則

このリリースでは以下を徹底：
- TestPyPI参照を完全削除（中途半端な移行はしない）
- バージョン番号の完全一致（0.1.0で統一）
- PyPI環境のみを使用（動的値による失敗を回避）

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 50行未満
- [x] 新規ファイル数: 0個
- [x] 影響範囲: 設定ファイルのみ
- [x] Rust連携: 不要（バージョン更新のみ）
- [x] NumPy/Pandas使用: なし
- [x] 非同期処理: 不要

### 規模判定結果
**小規模タスク**

## 4. 命名定義セクション

### 4.1 使用する既存命名
本リリースでは新規APIは追加しないため、既存命名の変更なし。

### 4.2 新規提案命名
なし

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認（変更なし）
- [x] naming_conventions.mdとの一致確認（変更なし）
- [x] ドキュメントでの使用方法定義（変更なし）

## フェーズ構成

### Phase 1: バージョン・ステータス更新（20分）

#### 1.1 Cargo.toml更新
- [x] version = "0.0.14" → "0.1.0"

#### 1.2 pyproject.toml更新
- [x] Development Status :: 3 - Alpha → 4 - Beta

#### 1.3 CHANGELOG.md更新
- [x] v0.1.0エントリー追加（2025-01-30）
- [x] PyPI移行の詳細記載

### Phase 2: ドキュメント更新（15分）

#### 2.1 README.md & README-ja.md
- [x] TestPyPI参照を完全削除
- [x] インストール方法を `pip install quantforge` に統一

#### 2.2 ベンチマークデータ更新
- [ ] `.internal/benchmark_automation/update_all.sh` 実行

### Phase 3: GitHub Actions更新（10分）

#### 3.1 .github/workflows/release.yml
- [x] workflow_dispatch.inputsセクション削除
- [x] environment: pypi を静的に設定
- [x] TestPyPI関連ステップ完全削除
- [x] PyPIパブリッシュステップの条件分岐削除

### Phase 4: 品質チェック（15分）

- [ ] Rustフォーマット・リント
  - [ ] cargo fmt --all
  - [ ] cargo clippy --all-targets --all-features
- [ ] Pythonフォーマット・リント
  - [ ] uv run ruff format .
  - [ ] uv run ruff check . --fix
  - [ ] uv run mypy .
- [ ] テスト実行
  - [ ] cargo test --lib --release
  - [ ] uv run pytest tests/ -q
- [ ] Critical Rules検証
  - [ ] ./scripts/check_critical_rules.sh
  - [ ] ./scripts/detect_hardcode.sh

### Phase 5: 最終確認とリリース（10分）

#### 5.1 コミット前チェックリスト
- [x] バージョン番号の一致確認（Cargo.toml: 0.1.0）
- [x] CHANGELOG.mdの日付確認
- [x] README.mdからTestPyPI参照完全削除
- [x] README-ja.mdからTestPyPI参照完全削除
- [x] release.ymlの動的値削除確認
- [ ] 全テスト成功（Rust 38件、Python 620件）

#### 5.2 コミット・タグ作成
```bash
# 変更をコミット
git add -A
git commit -m "chore: prepare v0.1.0 for PyPI release

- Update version to 0.1.0
- Change Development Status to Beta
- Remove TestPyPI references
- Simplify GitHub Actions for PyPI-only deployment"

# タグ作成
git tag v0.1.0
git push origin main --tags
```

#### 5.3 GitHubリリース作成
1. GitHub Releases → Draft a new release
2. Tag: v0.1.0を選択
3. Title: v0.1.0 - First PyPI Release
4. Description: CHANGELOG.mdの内容をコピー
5. "Publish release"をクリック → 自動的にPyPIへアップロード

## 成果物

- [x] 更新された設定ファイル（Cargo.toml, pyproject.toml）
- [x] 更新されたドキュメント（README.md, README-ja.md, CHANGELOG.md）
- [x] 簡略化されたGitHub Actions（release.yml）
- [ ] PyPIにアップロードされたwheel
- [ ] GitHubリリースページ

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| PyPI Trusted Publisher未設定 | 高 | 事前にPyPIで設定確認 |
| バージョン重複 | 高 | 0.1.0が未使用であることを確認 |
| GitHub環境未設定 | 中 | Settings→Environments→pypi作成 |
| 初回アップロード失敗 | 低 | 手動でtwineアップロード可能 |

## チェックリスト

### 実装前
- [x] 現在のバージョン確認（0.0.14）
- [x] PyPIでquantforgeプロジェクト作成済み確認
- [x] GitHub環境'pypi'設定確認
- [x] Trusted Publisher設定確認

### 実装中
- [x] 各ファイルのバージョン更新
- [x] TestPyPI参照の完全削除
- [x] 動的環境値の削除

### 実装後
- [ ] 全品質チェック通過
- [ ] git tag v0.1.0作成
- [ ] GitHubリリース公開
- [ ] PyPIでパッケージ確認
- [ ] pip install quantforgeでインストール確認

## 現在の進捗状況

### 完了タスク
- ✅ Cargo.toml: version 0.1.0に更新
- ✅ pyproject.toml: Development Status をBetaに更新
- ✅ CHANGELOG.md: v0.1.0エントリー追加
- ✅ README.md: TestPyPI参照削除
- ✅ README-ja.md: TestPyPI参照削除
- ✅ release.yml: PyPI専用に簡略化

### 進行中タスク
- 🔄 品質チェック実行中
- 🔄 ベンチマークデータ更新

### 残タスク
- コミット・タグ作成
- GitHubリリース作成

## 推定作業時間
- Phase 1: 20分（バージョン更新）✅ 完了
- Phase 2: 15分（ドキュメント更新）✅ 完了
- Phase 3: 10分（GitHub Actions更新）✅ 完了
- Phase 4: 15分（品質チェック）🔄 進行中
- Phase 5: 10分（リリース実行）

**合計: 約1時間10分**
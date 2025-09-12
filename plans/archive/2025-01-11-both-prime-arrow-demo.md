# [Both] Prime-Arrow: Arrow-native FFI デモンストレーション実装計画

## メタデータ
- **作成日**: 2025-01-11
- **言語**: Rust + Python (Both)
- **ステータス**: ACTIVE
- **推定規模**: 小
- **推定コード行数**: 200-300行
- **対象**: 新規GitHubリポジトリ (prime-arrow)

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 200-300行
- [x] 新規ファイル数: 10個
- [x] 影響範囲: 新規プロジェクト（独立）
- [x] PyO3バインディング: 必要
- [x] SIMD最適化: 不要（本質から外れる）
- [x] 並列化: 不要（シンプルさ優先）

### 規模判定結果
**小規模タスク** - シンプルなデモンストレーション実装

## 品質管理ツール

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| cargo test | ✅ | `cargo test` |
| cargo clippy | ✅ | `cargo clippy -- -D warnings` |
| cargo fmt | ✅ | `cargo fmt --check` |
| pytest | ✅ | `pytest tests/` |
| ruff | ✅ | `ruff check .` |
| mypy | ✅ | `mypy python/` |

## 4. 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  # 該当なし（素数判定専用の新規プロジェクト）
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "is_prime"
    meaning: "素数判定関数"
    justification: "数学的に標準的な命名"
    references: "一般的なプログラミング慣習"
    status: "standard"
  
  - name: "is_prime_batch"
    meaning: "バッチ素数判定関数"
    justification: "QuantForgeの_batch命名規則に準拠"
    references: "QuantForge命名規則"
    status: "standard"
```

### 4.3 命名の一貫性チェックリスト
- [x] シンプルで直感的な命名
- [x] 数学的慣習との一致
- [x] バッチ処理の_batchサフィックス
- [x] エラーメッセージでも同じ名前を使用

## 実装フェーズ

### Phase 1: プロジェクト構造作成（30分）
- [x] 実装計画書作成
- [ ] 基本ディレクトリ構造
- [ ] Cargo.toml / pyproject.toml設定
- [ ] README.md作成

### Phase 2: Rust実装（1時間）
- [ ] src/lib.rs - エントリーポイント
- [ ] src/prime.rs - 素数判定ロジック
- [ ] PyO3バインディング実装
- [ ] Rustテスト作成

### Phase 3: Python統合（30分）
- [ ] python/prime_arrow/__init__.py
- [ ] 型ヒントファイル(.pyi)
- [ ] Pythonテスト作成

### Phase 4: サンプル・ドキュメント（1時間）
- [ ] examples/basic_usage.py
- [ ] examples/benchmark.py
- [ ] examples/numpy_interop.py
- [ ] README.md完成

### Phase 5: 品質確認（30分）
```bash
# Rust品質
cargo fmt --all
cargo clippy -- -D warnings
cargo test

# Python品質
ruff check .
mypy python/
pytest tests/

# ビルド確認
maturin develop
python examples/basic_usage.py
```

## 技術要件

### 必須要件
- [x] ゼロコピーFFI実装
- [x] Arrow配列の直接処理
- [x] NumPy自動互換（pyo3-arrow経由）
- [x] 型変換コード0行

### パフォーマンス目標
- [ ] 100万要素: < 100ms
- [ ] メモリコピー: 0回
- [ ] 従来手法比: 2倍以上高速

### 依存関係
```toml
# Cargo.toml
[dependencies]
pyo3 = { version = "0.22", features = ["extension-module"] }
pyo3-arrow = "0.11"
arrow = "52"

# pyproject.toml
dependencies = [
    "pyarrow>=15.0",
    "numpy>=1.24",  # オプション
]
```

## プロジェクト構造

```
prime-arrow/
├── Cargo.toml
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
├── src/
│   ├── lib.rs       # PyO3モジュール定義
│   └── prime.rs     # 素数判定実装
├── python/
│   └── prime_arrow/
│       ├── __init__.py
│       └── prime_arrow.pyi
├── examples/
│   ├── basic_usage.py
│   ├── benchmark.py
│   └── numpy_interop.py
└── tests/
    ├── test_prime.rs
    └── test_python.py
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Arrow型の理解不足 | 低 | pyo3-arrowドキュメント参照 |
| NumPy互換性問題 | 低 | pyo3-arrowが自動処理 |
| パフォーマンス未達 | 低 | シンプルな実装で十分高速 |

## 成果物

- [ ] prime-arrowディレクトリ（quantforge/prime-arrow/）
- [ ] 完全動作するRust+Pythonパッケージ
- [ ] 3つの実用的なサンプル
- [ ] パフォーマンス測定結果
- [ ] 詳細なREADME.md

## 特記事項

### 本質に集中
- CI/CD設定は不要（サンプルプロジェクト）
- SIMD最適化は含まない（Arrow-nativeの価値に集中）
- 複雑な最適化より、コードの明瞭性を優先
- 型変換コード0行の実証が最重要

### 教育的価値
- FFIベストプラクティスの実例
- ゼロコピーの具体的実装
- pyo3-arrowの活用方法
- 従来手法との比較

## 参考資料

- 元記事: draft/arrow-native-zero-copy-ffi.md
- pyo3-arrow: https://github.com/pola-rs/pyo3-arrow
- arro3: https://github.com/kylebarron/arro3
- Apache Arrow: https://arrow.apache.org/

## 実装チェックリスト

### 実装前
- [x] 実装計画書作成
- [ ] プロジェクトディレクトリ作成
- [ ] 基本構成ファイル準備

### 実装中
- [ ] コードのシンプルさ維持
- [ ] コメントで重要ポイント説明
- [ ] テストカバレッジ確保

### 実装後
- [ ] ベンチマーク実行・記録
- [ ] README.md最終確認
- [ ] 動作確認完了
- [ ] 計画をarchiveへ移動
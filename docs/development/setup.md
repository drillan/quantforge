# 開発環境セットアップ

QuantForgeの開発環境構築手順です。

## 必要なツール

### Rust環境

```bash
# Rustインストール
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# バージョン確認
rustc --version  # 1.75以上推奨
cargo --version
```

### Python環境

```bash
# Python 3.12+
python --version

# uv インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 仮想環境作成
uv venv
source .venv/bin/activate
```

### 開発ツール

```bash
# Maturin（Rust-Pythonブリッジ）
uv pip install maturin

# 開発依存関係
uv pip install -r requirements-dev.txt
```

## プロジェクト構成

```
quantforge/
├── Cargo.toml          # Rust依存関係
├── pyproject.toml      # Pythonパッケージ設定
├── src/
│   ├── lib.rs         # Rustライブラリエントリ
│   ├── models/        # 価格モデル実装
│   ├── parallel/      # 並列処理
│   └── python.rs      # PyO3バインディング
├── python/
│   └── quantforge/    # Pythonパッケージ
└── tests/
    ├── rust/          # Rustテスト
    └── python/        # Pythonテスト
```

## ビルド手順

### 開発ビルド

```bash
# デバッグビルド（高速コンパイル）
maturin develop

# リリースビルド（最適化）
maturin develop --release
```

### テスト実行

```bash
# Rustテスト
cargo test

# Pythonテスト
pytest tests/python/

# ベンチマーク
cargo bench
```

## IDEセットアップ

### VS Code

推奨拡張機能：
- rust-analyzer
- Python
- Even Better TOML

設定例（`.vscode/settings.json`）：
```json
{
    "rust-analyzer.cargo.features": ["python"],
    "python.linting.enabled": true,
    "python.formatting.provider": "black"
}
```

### IntelliJ IDEA / PyCharm

- Rustプラグインインストール
- Python SDK設定
- Cargo統合有効化

## デバッグ

### Rustデバッグ

```bash
# デバッグ情報付きビルド
RUST_BACKTRACE=1 cargo build

# ログ出力
RUST_LOG=debug cargo run
```

### Pythonデバッグ

```python
import quantforge as qf
import logging

logging.basicConfig(level=logging.DEBUG)
# デバッグ実行
```

## コーディング規約

### Rust

- `cargo fmt` でフォーマット
- `cargo clippy` でリント
- 安全でない操作は最小限に

### Python

- Black でフォーマット
- mypy で型チェック
- PEP 8 準拠

## パフォーマンス分析

### プロファイリング

```bash
# Rust プロファイリング
cargo install flamegraph
cargo flamegraph

# Python プロファイリング
python -m cProfile -o profile.out script.py
```

### ベンチマーク

```bash
# Criterion.rs ベンチマーク
cargo bench

# Python ベンチマーク
python benchmarks/benchmark.py
```

## トラブルシューティング

### ビルドエラー

```bash
# クリーンビルド
cargo clean
rm -rf target/
maturin develop --release
```

### リンクエラー

```bash
# macOS
export DYLD_LIBRARY_PATH=$HOME/.rustup/toolchains/stable-*/lib

# Linux
export LD_LIBRARY_PATH=$HOME/.rustup/toolchains/stable-*/lib
```

## 次のステップ

- [アーキテクチャ](architecture.md)
- [コントリビューション](contributing.md)
- [テスト戦略](testing.md)
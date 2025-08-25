# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

QuantForgeは量的金融分析とオプション価格計算のための高性能ライブラリです。Rust + PyO3による実装で、Python比500-1000倍の高速化を実現します。

## 開発コマンド

### 依存関係のインストール
```bash
# 基本的な依存関係のインストール
uv sync

# 開発用依存関係を含むインストール
uv sync --group dev

# ドキュメント生成用の依存関係を含むインストール
uv sync --extra docs
```

### コード品質管理
```bash
# Pythonコードのフォーマット
uv run ruff format .

# Pythonコードのリントチェック
uv run ruff check .

# リント問題の自動修正
uv run ruff check --fix .

# 型チェック
uv run mypy .
```

### ドキュメントのビルド
```bash
# Sphinxドキュメントのビルド
uv run sphinx-build -M html docs docs/_build

# ビルドされたドキュメントは docs/_build/html/index.html で確認可能
```

## プロジェクト構造

### 現在の構成
- **main.py**: 簡単なエントリーポイント（現在は基本的な実装のみ）
- **docs/**: Sphinxベースのドキュメント
  - `development/`: アーキテクチャ、貢献ガイド、セットアップ、テスト
  - `models/`: 各種オプションモデルのドキュメント
  - `api/`: Python/Rust APIドキュメント（将来実装）
  - `performance/`: ベンチマーク、最適化、チューニング
- **plans/**: 実装計画
  - `2025-01-24-implementation-plan.md`: 14週間の詳細な実装計画
  - `2025-01-24-sphinx-documentation.md`: ドキュメント構築計画
- **draft/**: 設計文書とプロトタイプ
  - `GBS_2025.py`: 参考となるPython実装
  - Rust実装の設計書と改善提案

### 将来的なアーキテクチャ（計画中）

システムは以下の層で構成される予定：

1. **Python API層**: ユーザー向けインターフェース、入力検証
2. **PyO3バインディング層**: Python-Rust間のゼロコピー連携
3. **Rustコア層**: 
   - 価格モデル（Black-Scholes、American、Asian等）
   - SIMDエンジン（AVX2/AVX-512対応）
   - 並列実行エンジン（Rayon使用）
   - 高精度数学関数

### 重要な設計方針

- **ゼロコピー設計**: NumPy配列の直接参照による高速化
- **階層的並列化**: データ量に応じてSIMD/スレッド並列を自動選択
- **動的ディスパッチ**: CPU機能を検出し最適な実装を選択
- **型安全性**: Rustの型システムによるコンパイル時エラー検出

## 🚫 技術的負債ゼロの原則

### 基本方針
このプロジェクトでは技術的負債を一切作らないことを最優先とします。
段階的実装や一時的な実装は行わず、最初から理想形を実装します。

### 禁止事項（アンチパターン）
以下のアプローチは絶対に避けてください：

❌ **段階的移行**
- Python実装を作ってからRustに移植
- 「とりあえず動くもの」を作って後で改善
- プロトタイプを本番コードに含める

❌ **重複実装**
- 同じ機能の複数バージョンを共存させる
- 互換性レイヤーやアダプターの追加
- レガシーコードを残したまま新実装を追加

❌ **中途半端な最適化**
- 「後でSIMD化する」前提の実装
- 「将来的に並列化する」前提の設計
- パフォーマンスを後回しにした実装

### 推奨アプローチ
✅ **最初から理想形**
- Rust + PyO3で直接実装
- SIMD/並列化を最初から組み込む
- 高精度数学関数を最初から実装

✅ **機能の垂直統合**
- 1つの機能を完全に実装してから次へ
- テスト・ドキュメント・最適化を含めて完成させる
- 部分的な機能の放置を避ける

✅ **明確な境界**
- 実装する/しないを明確に分ける
- スコープクリープを防ぐ
- 将来の拡張点を明確に定義

### 例外条件
以下の場合のみ、段階的アプローチを検討可能：
1. 技術的検証が必要な未知の領域（ただしdraft/に隔離）
2. 外部ライブラリの評価（本番コードには含めない）

## パフォーマンス目標

- Black-Scholes単一計算: < 10ns
- 全グリークス計算: < 50ns
- インプライドボラティリティ計算: < 200ns
- 100万件バッチ処理: < 20ms

## 開発時の注意事項

- **Rust + PyO3による本番実装を直接行う**（段階的実装は禁止）
- 実装は`plans/2025-01-24-rust-bs-core.md`に従って進行
- ドキュメントは日本語で記述されている
- 数値精度はエラー率 < 1e-15を必達

## コード品質管理ルール

### Pythonコード編集時の必須実行事項

**重要**: Pythonファイルを作成・編集した場合、以下を必ず実行してください：

1. **フォーマット実行** (編集直後):
   ```bash
   uv run ruff format <編集したファイル>
   ```

2. **最終チェック** (作業完了時):
   ```bash
   # ruffによるリントチェック
   uv run ruff check .
   
   # mypyによる型チェック
   uv run mypy .
   ```

3. **問題があった場合**:
   - ruffのエラーは `uv run ruff check --fix .` で自動修正を試みる
   - mypyのエラーは型アノテーションを追加して解決

### 品質基準
- ruffの警告・エラー: ゼロ
- mypyの型チェック: strictモードでクリーン
- 全てのPython関数に型アノテーションを付与
- docstringは必須（Googleスタイル推奨）

## 実装判断フローチャート

新機能を実装する前に、以下の質問に答えてください：

1. **理想形が明確か？**
   - Yes → 2へ
   - No → 設計を完成させてから実装

2. **必要な技術がすべて利用可能か？**
   - Yes → 3へ
   - No → 技術調査を別途実施（draft/に記録）

3. **一度の実装で完成できるか？**
   - Yes → 実装開始
   - No → スコープを縮小して完成可能な単位に

4. **既存コードとの重複はないか？**
   - No → 実装継続
   - Yes → 既存コードを削除してから新実装

## 実装例

### ❌ 悪い例：段階的実装
```python
# phase1.py - 一時的なPython実装
def calculate_price():
    pass  # TODO: 後でRustに移植

# phase2.rs - 並行して存在するRust実装
# Python版と共存している重複実装
```

### ✅ 良い例：直接理想形
```rust
// src/models/black_scholes.rs
// 最初からRust + SIMD + 高精度で実装
#[pyfunction]
pub fn calculate_price(...) -> PyResult<f64> {
    // 完全な実装
}
```

## 検証用ファイルの作成ルール

### ディレクトリ構造と用途

プロジェクトには3種類のディレクトリがあります：

1. **`examples/`** - 公式サンプルコード
   - Git管理対象
   - ruff/mypy品質チェック対象
   - ユーザー向けの教育的コード

2. **`playground/`** - 検証・実験用コード
   - .gitignore対象（Git管理外）
   - 品質チェック対象外
   - AIや開発者の検証作業用

3. **`scratch/`** - 一時的なテストコード
   - .gitignore対象（Git管理外）
   - 品質チェック対象外
   - 短期的な確認用（30日経過で削除可）

### 一時的な検証が必要な場合

```bash
# playgroundディレクトリに検証スクリプトを作成
uv run python playground/test_新機能.py

# 例：新しい価格モデルの検証
echo "from quantforge import *" > playground/verify_asian_option.py
```

**重要**：
- ファイル名は`test_*.py`または`verify_*.py`を推奨
- 品質チェック不要（ruff/mypy対象外）
- Git管理外なので自由に編集・削除可能

### 公式サンプルを作成する場合

```bash
# examplesディレクトリに公式サンプルを作成
# 必ず品質チェックを実施
uv run ruff format examples/新サンプル.py
uv run ruff check examples/新サンプル.py
uv run mypy examples/新サンプル.py
```

**要件**：
- 完全な型アノテーション
- docstringによるドキュメント
- エラーハンドリング
- 教育的価値のあるコード
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🤖 AI 動作制御ルール

@.claude/critical-rules.xml

上記のクリティカルルール（C001-C014）は絶対遵守事項として、すべての作業に適用されます。
特に以下のルールはQuantForgeプロジェクトで重点的に適用：

- **C002**: エラー迂回絶対禁止（エラーは即座に修正）
- **C004**: 理想実装ファースト（技術的負債ゼロと同義）
- **C010**: テスト駆動開発必須（Red-Green-Refactor）
- **C011**: データ正確性絶対遵守（ハードコード禁止）
- **C012**: DRY原則（コード重複禁止）
- **C013**: 破壊的リファクタリング推奨（V2クラス禁止）
- **C014**: 妥協実装絶対禁止（段階的実装の禁止）

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

## 🚫 技術的負債ゼロの原則 [C004, C014適用]

このセクションは critical-rules.xml の C004（理想実装ファースト）および
C014（妥協実装絶対禁止）の具体的実装方法を定義します。

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

## 🔒 設定値管理の鉄則 - ZERO HARDCODE POLICY [C011-3適用]

このセクションは critical-rules.xml の C011-3（設定値ハードコード禁止プロトコル）の
具体的実装方法を定義します。

### 基本原則
**すべての設定値は必ず定義済みの場所から参照する。ハードコードは技術的負債。**

### 設定値の定義
以下はすべて「設定値」とみなし、ハードコードを禁止する：
- 数値定数（精度、閾値、境界値、制限値）
- 数学定数（係数、パラメータ）
- ビジネスルール（最大値、最小値、デフォルト値）
- アルゴリズムパラメータ（反復回数、収束条件）

例外：0, 1, 2, -1, 0.5（1/2）のみ直接記述可

### 実装前の必須確認事項

#### STEP 1: 既存定数の確認
新しい値を使う前に必ず確認：
```bash
# Rust定数の確認
grep -r "const.*=" src/constants.rs src/config/

# Python定数の確認  
grep -r "TOLERANCE\|EPSILON" tests/conftest.py

# 類似値の検索（例：1e-3を探す場合）
rg "1e-3\|0\.001" --type rust --type python
```

#### STEP 2: 定数の配置場所
定数を見つけたら/新規追加する場合の配置ルール：

| 種類 | 配置場所 | 例 |
|------|----------|-----|
| 精度・許容誤差 | src/constants.rs + tests/conftest.py | PRACTICAL_TOLERANCE |
| 数学定数・係数 | 使用箇所の近くで const 定義 | Abramowitz係数 |
| 入力検証制限 | src/validation.rs の InputLimits | 価格・時間の範囲 |
| テスト用値 | tests/conftest.py または各テストファイル | 標準テストケース |

#### STEP 3: 実装時のルール

```rust
// ❌ 禁止：マジックナンバー
if x > 8.0 { return 1.0; }  // 8.0とは何？なぜ8.0？

// ✅ 必須：名前付き定数
const NORM_CDF_UPPER_BOUND: f64 = 8.0;  // 正規分布の実質的な上限（Φ(8) ≈ 1.0）
if x > NORM_CDF_UPPER_BOUND { return 1.0; }
```

```python
# ❌ 禁止：テストでのハードコード
assert abs(price - expected) < 1e-5

# ✅ 必須：定義済み定数を使用
from conftest import THEORETICAL_TOLERANCE
assert abs(price - expected) < THEORETICAL_TOLERANCE
```

### コードレビューチェックリスト

新規コード/修正をレビューする際の必須確認：

- [ ] 数値リテラル（0,1,2,-1,0.5以外）が const/定数として定義されているか
- [ ] 定数には説明的な名前とコメントがあるか
- [ ] 同じ値が複数箇所で使われていないか（DRY原則）
- [ ] テストコードでも定数を使用しているか
- [ ] 新規定数は適切な場所に配置されているか

### 定数追加時の手順

1. **重複確認**
   ```bash
   rg "追加したい値" src/ tests/
   ```

2. **定義追加**
   - Rust: 適切な.rsファイルに `pub const NAME: type = value; // 説明`
   - Python: conftest.pyに `NAME: Final[type] = value  # 説明`

3. **同期確認**
   - Rust/Python両方で使う場合は値を同期
   - コメントで「Python側と同期」と明記

4. **ドキュメント**
   - なぜその値なのか根拠を記載
   - 参考文献があれば記載

### 自動検出スクリプト

定期的に実行してハードコードを検出：

```bash
# scripts/detect_hardcode.sh
#!/bin/bash

echo "🔍 Detecting hardcoded values..."

# 浮動小数点数の検出（0.0, 1.0, 2.0, 0.5以外）
rg '\b\d*\.\d+\b' src/ tests/ \
  --type rust --type python \
  | grep -v "const\|TOLERANCE\|EPSILON" \
  | grep -vE '\b(0\.0|1\.0|2\.0|0\.5)\b'

# 科学記法の検出
rg '\d+e[+-]\d+' src/ tests/ \
  --type rust --type python \
  | grep -v "const\|TOLERANCE\|EPSILON"

# 大きな整数の検出（100以上）
rg '\b[1-9]\d{2,}\b' src/ tests/ \
  --type rust --type python \
  | grep -v "const\|MAX\|MIN"
```

### 違反例と改善例

#### 例1: 精度値
```rust
// ❌ 違反
assert_relative_eq!(value, expected, epsilon = 1e-7);

// ✅ 改善
use crate::constants::NUMERICAL_TOLERANCE;
assert_relative_eq!(value, expected, epsilon = NUMERICAL_TOLERANCE);
```

#### 例2: 境界値
```rust
// ❌ 違反
if volatility < 0.005 || volatility > 10.0 { 
    return Err(...);
}

// ✅ 改善
const MIN_VOLATILITY: f64 = 0.005;  // 0.5% - 実務上の最小ボラティリティ
const MAX_VOLATILITY: f64 = 10.0;   // 1000% - 理論上の最大ボラティリティ
if volatility < MIN_VOLATILITY || volatility > MAX_VOLATILITY {
    return Err(...);
}
```

#### 例3: アルゴリズムパラメータ
```rust
// ❌ 違反
for _ in 0..1000 {  // 最大反復回数
    if converged { break; }
}

// ✅ 改善
const MAX_ITERATIONS: usize = 1000;  // Newton-Raphson法の最大反復回数
for _ in 0..MAX_ITERATIONS {
    if converged { break; }
}
```

### よくある質問

**Q: 一時的なデバッグ値も定数化が必要？**
A: playground/やscratch/での実験は例外。本番コード（src/, tests/）では必須。

**Q: 数式の中の係数はどうする？**
A: 意味のある係数は必ず名前を付ける。例：`0.5 * sigma * sigma` → `0.5`は数学的に1/2なのでOK

**Q: 既存のハードコード値を見つけたら？**
A: 即座に定数化。「後で」は技術的負債。

**Q: 外部ライブラリの定数は？**
A: 可能な限り再定義して意味を明確化。例：`std::f64::EPSILON`より`MACHINE_EPSILON`

### 実施により期待される効果

1. **保守性**: 値の変更が1箇所で完結
2. **可読性**: マジックナンバーの意味が明確
3. **一貫性**: 同じ目的の値が統一される
4. **検証可能性**: 定数の妥当性を一覧で確認可能
5. **技術的負債ゼロ**: ハードコードによる将来の問題を防止

## 📚 Document as Single Source of Truth (D-SSoT) プロトコル [C008強化版]

このセクションは critical-rules.xml の C008（ドキュメント整合性絶対遵守）を
強化し、ドキュメントを唯一の真実の源とするプロトコルです。

### 根本原則
**ドキュメントは唯一の真実。実装はその具現化。計画は一時的な設計メモ。**

### ⚠️ 重要な警告
**計画文書（plans/archive/*.md）は参照しないこと。**
計画文書には仕様変更履歴、誤った実装の修正記録、破棄された設計が含まれており、
これらを参照すると過去の誤りを繰り返す危険があります。

### 情報源の優先順位

1. **docs/api/** - 唯一の真実（最優先）
   - 現在有効な仕様のみ
   - ユーザーとの契約
   - 実装が従うべき仕様書

2. **実装コード** - ドキュメントの具現化
   - ドキュメントに完全準拠
   - ドキュメントにない機能は存在禁止

3. **plans/archive** - 設計メモ（参照禁止）
   - 新機能の検討用のみ
   - ドキュメント化で役割終了
   - 過去の記録（参照による誤謬リスク）

### 正しい実装フロー

#### 新機能開発
```
1. 計画作成（plans/） → 設計検討のみ
2. ドキュメント作成（docs/api/） → ここで仕様確定
3. ドキュメントから実装へコピペ → 手打ち禁止
4. 検証（ドキュメントと実装の一致）
5. 計画をarchive/へ → 以降参照禁止
```

#### 既存機能修正
```
1. docs/api/ で現在の仕様確認 ← 必須
2. 計画文書は一切参照しない ← 絶対
3. ドキュメント通りに実装
```

### 禁止事項

❌ **計画文書の参照**
```bash
# 絶対禁止：計画を真実として扱う
cat plans/2025-01-24-implementation-plan.md  # 過去の誤りを含む

# 必須：ドキュメントのみ参照
cat docs/api/python/pricing.md  # 現在の真実
```

❌ **ドキュメント化前の実装**
```python
# 禁止：計画から直接実装
plans/*.md → 実装  # ドキュメント化されていない

# 必須：ドキュメント経由
plans/*.md → docs/api/ → 実装
```

❌ **実装優先の修正**
```python
# 禁止：実装してからドキュメント修正
実装 → docs/api/  # 逆順は契約違反

# 必須：ドキュメント優先
docs/api/ → 実装
```

### 自動検証

```bash
# scripts/verify_doc_implementation.sh
#!/bin/bash

echo "📚 D-SSoT検証開始..."

# 計画文書への参照を検出（エラー）
if grep -r "plans/" src/ python/ --include="*.py" --include="*.rs"; then
    echo "❌ エラー：実装コードが計画文書を参照しています"
    exit 1
fi

# ドキュメントと実装の一致を検証
python scripts/verify_doc_implementation_consistency.py

echo "✅ D-SSoT検証完了"
```

### チェックリスト

実装前に必ず確認：
- [ ] docs/api/ で仕様を確認した（plans/は見ていない）
- [ ] ドキュメントから関数名をコピーした（手打ちしていない）
- [ ] ドキュメントにない機能を追加していない
- [ ] 計画文書を一切参照していない

## パフォーマンス目標

- Black-Scholes単一計算: < 10ns
- 全グリークス計算: < 50ns
- インプライドボラティリティ計算: < 200ns
- 100万件バッチ処理: < 20ms

## 開発時の注意事項

- **Rust + PyO3による本番実装を直接行う**（段階的実装は禁止）
- 実装は`plans/2025-01-24-rust-bs-core.md`に従って進行
- ドキュメントは日本語で記述されている
- 数値精度はエラー率 < 1e-3（実務精度）

## コード品質管理ルール [C006, C007適用]

このセクションは critical-rules.xml の C006（堅牢コード品質）および
C007（品質例外化禁止）の具体的実装方法を定義します。

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
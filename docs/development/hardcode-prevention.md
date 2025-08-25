# ハードコード防止ガイドライン

## 概要

QuantForgeプロジェクトでは、技術的負債ゼロの原則に基づき、設定値のハードコードを完全に禁止しています。
このドキュメントは、開発者がハードコードを避け、適切な定数管理を行うためのガイドラインです。

## なぜハードコードが問題なのか

1. **保守性の低下**: 同じ値が複数箇所に散在し、変更時に漏れが発生
2. **可読性の低下**: マジックナンバーの意味が不明確
3. **テストの困難さ**: 値の変更が困難でテストの柔軟性が失われる
4. **技術的負債**: 後で修正するコストが増大

## 設定値の管理体系

### 定数の配置場所

| 種類 | Rust配置場所 | Python配置場所 | 例 |
|------|-------------|---------------|-----|
| 精度・許容誤差 | `src/constants.rs` | `tests/conftest.py` | `PRACTICAL_TOLERANCE = 1e-3` |
| 数学定数・係数 | 使用箇所の近く | 使用箇所の近く | Abramowitz係数 |
| 入力検証制限 | `src/validation.rs` | - | 価格・時間の範囲 |
| テスト用値 | - | `tests/conftest.py` | 標準テストケース |

### 現在定義されている主要定数

#### 精度レベル（Rust/Python共通）

```rust
// src/constants.rs
pub const PRACTICAL_TOLERANCE: f64 = 1e-3;   // 実務精度
pub const THEORETICAL_TOLERANCE: f64 = 1e-5; // 理論精度
pub const NUMERICAL_TOLERANCE: f64 = 1e-7;   // 数値精度
```

```python
# tests/conftest.py
PRACTICAL_TOLERANCE: Final[float] = 1e-3   # 実務精度
THEORETICAL_TOLERANCE: Final[float] = 1e-5 # 理論精度
NUMERICAL_TOLERANCE: Final[float] = 1e-7   # 数値精度
```

## 開発ワークフロー

### 1. 新規実装時

```bash
# Step 1: 既存定数の確認
grep -r "使いたい値" src/constants.rs tests/conftest.py

# Step 2: 定数が存在しない場合は定義
# 例: src/constants.rs に追加
pub const NEW_CONSTANT: f64 = 3.14159; // π - 円周率

# Step 3: 実装で使用
use crate::constants::NEW_CONSTANT;

# Step 4: 検証
./scripts/detect_hardcode.sh
```

### 2. 既存コード修正時

ハードコードを見つけた場合：

```rust
// Before（悪い例）
if x > 8.0 { return 1.0; }

// After（良い例）
const NORM_CDF_UPPER_BOUND: f64 = 8.0;
if x > NORM_CDF_UPPER_BOUND { return 1.0; }
```

### 3. テストコード作成時

```python
# Before（悪い例）
assert abs(actual - expected) < 1e-5

# After（良い例）
from conftest import THEORETICAL_TOLERANCE
assert abs(actual - expected) < THEORETICAL_TOLERANCE
```

## ハードコード検出ツール

### 自動検出スクリプト

```bash
# 実行方法
./scripts/detect_hardcode.sh

# 出力例
🔍 QuantForge ハードコード検出スクリプト
=========================================
📊 浮動小数点数の検出...
✅ 問題なし
🔬 科学記法の検出...
✅ 問題なし
```

### CI/CDでの自動チェック

PRやコミット時に自動的にハードコード検出が実行されます。

## 許可される例外

以下の値のみハードコード可能：

- `0`, `1`, `2`, `-1`（基本的な整数）
- `0.5`（1/2 の数学的表現）
- 配列インデックス
- ループカウンタ
- エラーメッセージ内の説明的な数値

## よくある質問

### Q: playground/での実験コードも定数化が必要？

A: playground/とscratch/は例外ですが、可能な限り定数を使用することを推奨します。

### Q: 外部ライブラリの定数はどうする？

A: 意味を明確化するため、可能な限り再定義します：

```rust
// std::f64::EPSILON より
pub const MACHINE_EPSILON: f64 = std::f64::EPSILON;
```

### Q: テスト専用の値はどこに定義？

A: `tests/conftest.py`に集約するか、各テストファイルの先頭で定義します。

## チェックリスト

新規コード/PRレビュー時の確認事項：

- [ ] 数値リテラル（許可された例外以外）がすべて定数化されている
- [ ] 定数には説明的な名前が付けられている
- [ ] 同じ値が複数箇所で重複していない
- [ ] Rust/Python間で共通の値が同期されている
- [ ] `./scripts/detect_hardcode.sh`でエラーが出ない

## まとめ

ハードコード防止は技術的負債を防ぐ重要な実践です。
「後で修正」ではなく「最初から正しく」実装することで、
保守性の高い高品質なコードベースを維持できます。
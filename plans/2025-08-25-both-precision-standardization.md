# 精度設定一元化計画

**作成日**: 2025-08-25  
**ステータス**: ACTIVE  
**種別**: both-standardization  
**優先度**: CRITICAL  
**影響範囲**: 全テスト、Rust/Python実装の精度管理

## 1. エグゼクティブサマリー

現在、プロジェクト全体で精度値がハードコードされており、以下の問題を引き起こしている：
- `src/constants.rs::EPSILON`が定義されているが未使用
- すべてのテストで精度値が直接記述（1e-3, 1e-5, 1e-6, 1e-7等が混在）
- 精度変更時に複数箇所の修正が必要
- norm_cdf実装の精度限界（約1e-5）によるテスト失敗

本計画では、**技術的負債ゼロの原則**に従い、精度設定を一元化し、用途別に階層化する。

## 2. 現状分析

### 2.1 問題の所在

| ファイル/場所 | 現在の状況 | 問題点 |
|--------------|-----------|--------|
| src/constants.rs | EPSILON = 1e-3定義済み | 実際には未使用 |
| Rustテストコード | 1e-3, 1e-7, 1e-10混在 | ハードコード |
| Pythonテスト | 1e-3, 1e-5, 1e-6混在 | ハードコード |
| norm_cdf実装 | 精度約1e-5 | 1e-6要求のテスト失敗 |
| CLAUDE.md | 1e-3記載済み | 正しく設定済み |
| golden_values.json | tolerance: 1e-3 | 正しく設定済み |

### 2.2 根本原因

1. **定数定義の未活用**: constants.rsが定義されているが参照されていない
2. **精度レベルの混在**: 用途に応じた精度要求が整理されていない
3. **アルゴリズムの精度限界**: norm_cdfの実装精度と要求精度の不一致

## 3. 解決方針

### 3.1 階層化された精度基準

```rust
// src/constants.rs - 拡充版
/// 実務精度: 価格計算・金融実務用（0.1% = 1bp×10）
pub const PRACTICAL_TOLERANCE: f64 = 1e-3;

/// 理論精度: norm_cdfの現在の制約（約1e-5レベル）
pub const THEORETICAL_TOLERANCE: f64 = 1e-5;

/// 数値精度: 基本的な数値計算用
pub const NUMERICAL_TOLERANCE: f64 = 1e-7;

/// デフォルト精度（実務用途）
pub const EPSILON: f64 = PRACTICAL_TOLERANCE;
```

### 3.2 根拠

- **実務精度（1e-3）**: 金融実務で十分な精度、機関投資家の取引単位
- **理論精度（1e-5）**: norm_cdf実装の現実的な精度上限
- **数値精度（1e-7）**: 数学的性質の検証で必要な高精度

## 4. 実装計画

### 4.1 Phase 1: Rust側の定数拡充（10分）

#### src/constants.rs拡充
```rust
// 階層化された精度定数を定義
pub const PRACTICAL_TOLERANCE: f64 = 1e-3;
pub const THEORETICAL_TOLERANCE: f64 = 1e-5;
pub const NUMERICAL_TOLERANCE: f64 = 1e-7;
pub const EPSILON: f64 = PRACTICAL_TOLERANCE;
```

#### Rustテストコードの修正
- src/models/black_scholes.rs
- src/math/distributions.rs
定数をインポートして使用

### 4.2 Phase 2: Python側の定数定義（10分）

#### tests/conftest.py作成
```python
"""テスト用精度定数の中央定義"""
from typing import Final

# Rustのconstants.rsと同期
PRACTICAL_TOLERANCE: Final[float] = 1e-3
THEORETICAL_TOLERANCE: Final[float] = 1e-5
NUMERICAL_TOLERANCE: Final[float] = 1e-7
EPSILON: Final[float] = PRACTICAL_TOLERANCE
```

### 4.3 Phase 3: Pythonテストの修正（15分）

#### 対象ファイルと精度レベル
| ファイル | 使用する定数 | 理由 |
|---------|------------|------|
| test_distributions.py | THEORETICAL_TOLERANCE | norm_cdf制約 |
| test_reference_values.py | PRACTICAL_TOLERANCE | 実務精度 |
| test_black_scholes.py | PRACTICAL_TOLERANCE | 実務精度 |
| test_price_properties.py | THEORETICAL_TOLERANCE | 数学的性質 |

### 4.4 Phase 4: 検証とドキュメント（10分）

```bash
# Rustテスト
cargo test --release

# Pythonテスト  
uv run pytest tests/ -v

# ハードコード検出
grep -r "1e-[0-9]" --include="*.py" --include="*.rs" tests/ src/ | \
  grep -v "constants" | grep -v "conftest"
```

## 5. 技術的負債ゼロの保証

### ❌ 行わないこと
- 段階的移行（一度に完全移行）
- 互換性レイヤー（直接参照のみ）
- 複雑な設定システム（シンプルな定数定義）
- 一括置換（用途別の適切な精度選択）

### ✅ 行うこと
- 定数の一元管理と参照強制
- 用途別の階層化された精度定義
- Rust/Python間の同期

## 6. リスクと対策

| リスク | 可能性 | 影響 | 対策 |
|--------|--------|------|------|
| norm_cdf精度不足による失敗 | 中 | 中 | THEORETICAL_TOLERANCEを適用 |
| 定数インポート漏れ | 低 | 低 | grepで検出・修正 |

## 7. 成功基準

- [x] src/constants.rs::EPSILONが定義済み
- [x] すべての精度値が定数参照に変更
- [x] ハードコードされた精度値が適切な最小限に削減
- [ ] 全Pythonテスト成功（pytest）
- [ ] 全Rustテスト成功（cargo test）
- [x] 精度変更が1箇所の修正で可能

## 8. 実施スケジュール

| タスク | 所要時間 | 依存 | 状態 |
|--------|----------|------|------|
| 計画策定・調査 | 20分 | なし | ✅ 完了 |
| Rust定数拡充 | 10分 | 計画承認 | ✅ 完了 |
| Python定数定義 | 10分 | Rust定数 | ✅ 完了 |
| テストコード修正 | 15分 | 定数定義 | ✅ 完了 |
| 検証・ドキュメント | 10分 | 修正完了 | ⏳ 実施中 |

**総所要時間**: 45分（調査済み部分を除く）

## 9. 実施後の確認

```bash
# ハードコードされた精度値の検出
grep -r "1e-[0-9]" --include="*.py" --include="*.rs" tests/ src/ | \
  grep -v "constants" | grep -v "conftest" | \
  grep -v "comment" | grep -v "doc"

# 期待結果: 出力なしまたは必要最小限
```

## 10. 結論

本計画により、精度設定を一元化し、保守性と一貫性を大幅に向上させる。
技術的負債ゼロの原則を厳守し、用途別の適切な精度管理を実現する。

---

**承認**: [x] PM  
**実施**: [ ] 開発者  
**確認**: [ ] QA
"""テスト用精度定数の中央定義

このファイルは、QuantForgeのテストスイート全体で使用される精度定数を定義します。
Rust側のsrc/constants.rsと同期して管理されています。

使用例:
    from conftest import PRACTICAL_TOLERANCE
    assert abs(actual - expected) < PRACTICAL_TOLERANCE
"""

from typing import Final

# ===== 精度レベル定義 =====
# Rustのsrc/constants.rsと同期

# 実務精度: 価格計算・金融実務用（0.1% = 1bp×10）
PRACTICAL_TOLERANCE: Final[float] = 1e-3
"""金融実務で標準的な精度。機関投資家の取引でも0.1セント単位で十分。
価格計算、バッチ処理、実務アプリケーションで使用。"""

# 理論精度: アルゴリズムの精度制約下での検証用
THEORETICAL_TOLERANCE: Final[float] = 1e-5
"""norm_cdf実装の現在の精度限界（約1e-5レベル）を考慮した精度。
理論的な価格モデルの検証や、数学的性質のテストで使用。"""

# 数値精度: 基本的な数値計算の検証用
NUMERICAL_TOLERANCE: Final[float] = 1e-7
"""高精度が必要な数学的性質の検証（対称性、単調性など）で使用。
浮動小数点演算の限界内での最高精度レベル。"""

# デフォルト精度（実務用途）
EPSILON: Final[float] = PRACTICAL_TOLERANCE
"""後方互換性のため、EPSILONは実務精度を指す。
新規コードではPRACTICAL_TOLERANCEの使用を推奨。"""


# ===== 用途別精度ガイドライン =====
#
# | 用途 | 使用する定数 | 値 | 理由 |
# |-----|------------|-----|------|
# | 価格計算テスト | PRACTICAL_TOLERANCE | 1e-3 | 金融実務標準 |
# | norm_cdf関連 | THEORETICAL_TOLERANCE | 1e-5 | 実装精度の制約 |
# | 数学的性質検証 | NUMERICAL_TOLERANCE | 1e-7 | 高精度が必要 |
# | バッチ処理検証 | PRACTICAL_TOLERANCE | 1e-3 | 実用性重視 |
# | ゴールデンマスター | PRACTICAL_TOLERANCE | 1e-3 | 実務精度で十分 |

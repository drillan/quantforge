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

# ===== Arrow Native Support =====
# Arrow配列とNumPy配列の統一的な操作をサポート

from typing import Any, List, Union
try:
    import arro3.core
    ARROW_AVAILABLE = True
except ImportError:
    ARROW_AVAILABLE = False

import pyarrow as pa
import numpy as np


class ArrowArrayHelper:
    """Arrow配列とNumPy配列の統一的な操作を提供"""
    
    @staticmethod
    def is_arrow(obj: Any) -> bool:
        """オブジェクトがArrow配列かチェック"""
        if not ARROW_AVAILABLE:
            return False
        return isinstance(obj, arro3.core.Array)
    
    @staticmethod
    def to_list(arr: Any) -> List[float]:
        """配列をPythonリストに変換"""
        if ArrowArrayHelper.is_arrow(arr):
            return arr.to_pylist()
        elif hasattr(arr, 'tolist'):  # NumPy array
            return arr.tolist()
        else:
            return list(arr)
    
    @staticmethod
    def get_value(arr: Any, index: int) -> float:
        """配列から値を取得"""
        if ArrowArrayHelper.is_arrow(arr):
            scalar = arr[index]
            if hasattr(scalar, 'as_py'):
                return scalar.as_py()
            return float(scalar)
        else:
            return float(arr[index])
    
    @staticmethod
    def assert_type(result: Any) -> None:
        """結果がArrow配列であることを確認"""
        assert ArrowArrayHelper.is_arrow(result), \
            f"Expected arro3.core.Array, got {type(result)}"
    
    @staticmethod
    def assert_allclose(
        actual: Any, 
        expected: Any, 
        rtol: float = PRACTICAL_TOLERANCE,
        err_msg: str = ""
    ) -> None:
        """値の近似チェック"""
        actual_list = ArrowArrayHelper.to_list(actual)
        if hasattr(expected, '__iter__') and not isinstance(expected, str):
            expected_list = ArrowArrayHelper.to_list(expected)
        else:
            expected_list = [expected] * len(actual_list)
        
        assert len(actual_list) == len(expected_list), \
            f"Length mismatch: {len(actual_list)} != {len(expected_list)}"
        
        for i, (a, e) in enumerate(zip(actual_list, expected_list)):
            if not (np.isnan(a) and np.isnan(e)):  # NaN同士は等しいとみなす
                assert abs(a - e) <= rtol * max(abs(e), 1.0), \
                    f"Value mismatch at index {i}: {a} != {e} (rtol={rtol}){' - ' + err_msg if err_msg else ''}"
    
    @staticmethod
    def assert_comparison(
        arr: Any,
        op: str,
        value: float = 0.0
    ) -> None:
        """配列要素の比較操作を確認"""
        values = ArrowArrayHelper.to_list(arr)
        
        if op == "all_positive":
            assert all(v >= 0 for v in values), "負の値が含まれています"
        elif op == "increasing":
            assert all(values[i] < values[i+1] for i in range(len(values)-1)), \
                "単調増加でありません"
        elif op == "decreasing":
            assert all(values[i] > values[i+1] for i in range(len(values)-1)), \
                "単調減少でありません"
        elif op == "all_finite":
            assert all(np.isfinite(v) for v in values), \
                "無限大またはNaNが含まれています"


# 短縮エイリアス
arrow = ArrowArrayHelper()

# ===== 両データ型テスト用ユーティリティ =====

INPUT_ARRAY_TYPES = ["numpy", "pyarrow"]

def create_test_array(values: Union[List[float], float], array_type: str) -> Any:
    """テスト用配列を指定された型で作成
    
    Args:
        values: 値のリストまたは単一値
        array_type: "numpy" または "pyarrow"
    
    Returns:
        指定された型の配列
    """
    # 単一値の場合はリストに変換
    if isinstance(values, (int, float)):
        values = [values]
    
    if array_type == "numpy":
        return np.array(values, dtype=np.float64)
    elif array_type == "pyarrow":
        return pa.array(values, type=pa.float64())
    else:
        raise ValueError(f"Unknown array type: {array_type}")

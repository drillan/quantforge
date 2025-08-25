# Pythonコードリファクタリング - AI実行指示プロンプト

あなたはPython + PyO3プロジェクトのリファクタリングを担当し、以下の手順に従ってコードの重複削除と品質改善を実行する。

## 🤖 自動実行原則

**重要**: コード重複とアンチパターンを検出したら、ユーザーの確認を待たずに以下を自動実行する：
- similarity-pyで重複を検出し、即座にリファクタリング案を提示
- 技術的負債となるパターンを発見次第、修正を実行
- パフォーマンス改善の機会を見つけたら、最適化を適用
- 各修正は適切なツール（Edit、MultiEdit等）で直接実行

## 🎯 実行目的

あなたはPythonコードベースを以下の観点から分析し、積極的にリファクタリングを実施します：
- コード重複の排除（similarity-py閾値80%以上）
- 型アノテーションの完全性確保（mypy strictモード準拠）
- NumPyベクトル化による高速化
- PyO3バインディングのゼロコピー最適化
- エラーハンドリングの一貫性確保

## 📋 前提条件の確認

リファクタリング開始前に以下を実行してください：

```bash
# similarity-pyのインストール確認
similarity-py --version || echo "similarity-pyがインストールされていません"

# 現在のコード重複状況を分析
similarity-py --threshold 0.80 --min-lines 5 src/ quantforge/

# 既存ツールの確認
uv run ruff --version    # フォーマッター兼リンター
uv run mypy --version    # 型チェッカー
uv run pytest --version  # テストランナー
```

### パフォーマンス目標（プロジェクトごとに調整）
- **単一計算**: マイクロ秒〜ミリ秒オーダー
- **バッチ処理**: NumPy/pandasによるベクトル化で線形以下
- **メモリ使用量**: 入力データサイズの2倍以内
- **Rust実装比**: Pure Pythonで1/100の性能を目標

## 🚫 技術的負債ゼロの絶対原則

### 禁止事項（アンチパターン）

❌ **段階的移行・暫定実装**
```python
# 絶対にダメな例
def compute(data):
    # TODO: 後で最適化する
    result = []
    for item in data:  # 後でベクトル化
        result.append(item * 2)
    return result
```

❌ **重複実装の共存**
```python
# 絶対にダメな例
def algorithm_v1():  # 旧実装を残す
    pass

def algorithm_v2():  # 新実装を追加
    pass
```

✅ **正しいアプローチ：最初から完全実装**
```python
# 最初から最適化された完全な実装
from typing import Union, Optional
import numpy as np
from numpy.typing import NDArray

def compute(
    data: Union[NDArray[np.float64], list[float]],
    *,
    parallel: bool = True,
    chunk_size: Optional[int] = None
) -> NDArray[np.float64]:
    """完全に最適化された実装（型アノテーション、エラーハンドリング含む）."""
    data_array = np.asarray(data, dtype=np.float64)
    
    if data_array.size == 0:
        raise ValueError("Input data cannot be empty")
    
    # ベクトル化された演算
    return data_array * 2
```

## 📋 汎用リファクタリング指針

### 1. 数値計算アーキテクチャの最適化パターン

#### 計算戦略の動的選択
```python
from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, Generic
import numpy as np
from numpy.typing import NDArray

T = TypeVar('T', bound=np.generic)

class ComputeStrategy(Protocol[T]):
    """汎用的な計算戦略プロトコル."""
    
    def select_strategy(self, size: int) -> str:
        """データサイズに基づいて最適な実行戦略を選択."""
        if size <= 1000:
            return "sequential"
        elif size <= 10000:
            return "vectorized"
        elif size <= 100000:
            return "chunked"
        else:
            return "parallel"
    
    def execute(
        self, 
        data: NDArray[T], 
        strategy: str
    ) -> NDArray[T]:
        """選択された戦略で計算を実行."""
        ...
```

#### NumPy最適化の汎用パターン
```python
from typing import Callable, TypeVar
import numpy as np
from numpy.typing import NDArray

T = TypeVar('T', bound=np.generic)

def apply_vectorized(
    data: NDArray[T],
    operation: Callable[[NDArray[T]], NDArray[T]],
    *,
    chunk_size: int = 10000,
    parallel: bool = True
) -> NDArray[T]:
    """ベクトル化された演算の汎用適用."""
    if data.size <= chunk_size or not parallel:
        # 小規模データは直接処理
        return operation(data)
    
    # 大規模データはチャンク処理
    from concurrent.futures import ThreadPoolExecutor
    import numpy as np
    
    chunks = np.array_split(data, data.size // chunk_size + 1)
    
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(operation, chunks))
    
    return np.concatenate(results)
```

### 2. PyO3バインディングの最適化パターン

#### ゼロコピー実装の汎用テンプレート
```python
from typing import Optional, Union
import numpy as np
from numpy.typing import NDArray

def prepare_for_rust(
    data: Union[list, NDArray[np.float64]]
) -> NDArray[np.float64]:
    """Rustバインディング用のデータ準備（ゼロコピー最適化）."""
    # NumPy配列に変換（既にNumPy配列ならコピーなし）
    array = np.asarray(data, dtype=np.float64)
    
    # C連続性を確保（必要な場合のみコピー）
    if not array.flags['C_CONTIGUOUS']:
        array = np.ascontiguousarray(array)
    
    return array

def call_rust_function(
    data: NDArray[np.float64],
    *,
    validate: bool = True
) -> NDArray[np.float64]:
    """Rust実装の呼び出しラッパー."""
    if validate:
        # 入力検証はPython側で実施
        if data.size == 0:
            raise ValueError("Input cannot be empty")
        if not np.isfinite(data).all():
            raise ValueError("Input contains NaN or Inf")
    
    # Rust関数呼び出し（実際の実装に置き換え）
    # result = quantforge_core.process(data)
    
    # 仮の実装
    result = data * 2
    
    return result
```

### 3. エラーハンドリングの汎用設計

```python
from typing import Any, Optional, Union
from dataclasses import dataclass

@dataclass
class ComputeError(Exception):
    """計算エラーの基底クラス."""
    message: str
    context: Optional[dict[str, Any]] = None
    
    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} ({context_str})"
        return self.message

class ValidationError(ComputeError):
    """入力検証エラー."""
    pass

class NumericalError(ComputeError):
    """数値計算エラー."""
    pass

class ConvergenceError(ComputeError):
    """収束エラー."""
    pass

class DimensionMismatchError(ComputeError):
    """次元不一致エラー."""
    
    def __init__(self, expected: int, actual: int):
        super().__init__(
            f"Dimension mismatch",
            {"expected": expected, "actual": actual}
        )

class OutOfRangeError(ComputeError):
    """範囲外エラー."""
    
    def __init__(self, value: float, min_val: float, max_val: float):
        super().__init__(
            f"Value out of range",
            {"value": value, "min": min_val, "max": max_val}
        )
```

### 4. 拡張可能なアーキテクチャパターン

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Protocol, Any
import numpy as np
from numpy.typing import NDArray

InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')
ConfigT = TypeVar('ConfigT')

class ComputeEngine(ABC, Generic[InputT, OutputT, ConfigT]):
    """汎用計算エンジンの抽象基底クラス."""
    
    @abstractmethod
    def compute_single(
        self,
        input_data: InputT,
        config: ConfigT
    ) -> OutputT:
        """単一計算の実行."""
        ...
    
    def compute_batch(
        self,
        inputs: list[InputT],
        config: ConfigT
    ) -> list[OutputT]:
        """バッチ計算（デフォルト実装提供）."""
        return [self.compute_single(inp, config) for inp in inputs]
    
    def compute_batch_parallel(
        self,
        inputs: list[InputT],
        config: ConfigT,
        max_workers: Optional[int] = None
    ) -> list[OutputT]:
        """並列バッチ計算（デフォルト実装提供）."""
        from concurrent.futures import ProcessPoolExecutor
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(self.compute_single, inp, config)
                for inp in inputs
            ]
            return [f.result() for f in futures]

class OptimizationHints(Protocol):
    """最適化ヒントプロトコル."""
    
    @property
    def prefers_contiguous_memory(self) -> bool:
        """連続メモリを優先するか."""
        return True
    
    @property
    def optimal_chunk_size(self) -> int:
        """最適なチャンクサイズ."""
        return 10000
    
    @property
    def supports_vectorization(self) -> bool:
        """ベクトル化をサポートするか."""
        return True
    
    @property
    def cache_line_size(self) -> int:
        """キャッシュラインサイズ."""
        return 64
```

## 🔄 similarity-pyを活用した継続的品質管理

### リファクタリングワークフロー

#### 定期的な重複検出
```bash
# 基本的な重複チェック
similarity-py \
  --threshold 0.80 \
  --min-lines 5 \
  src/ quantforge/

# 詳細チェック（実験的機能含む）
similarity-py \
  --threshold 0.75 \
  --experimental-overlap \
  --print \
  src/ quantforge/ > similarity-report.md
```

#### リファクタリング判断基準

| 類似度 | アクション | 理由 |
|--------|-----------|------|
| > 95% | 即座にリファクタリング | ほぼ完全な重複 |
| 85-95% | 分析して判断 | 意図的な類似の可能性 |
| 75-85% | 監視対象 | パターンの類似 |
| < 75% | 対応不要 | 独立した実装 |

### 重複パターンの解消戦略

#### パターン1: 類似した計算ロジック
```python
# Before: 重複した実装
def calculate_metric_a(data: list[float]) -> float:
    return sum(data) / len(data)

def calculate_metric_b(data: list[float]) -> float:
    return sum(data) / len(data)  # 同じロジック

# After: 関数の統一または抽象化
from typing import Protocol

class Metric(Protocol):
    """メトリクス計算プロトコル."""
    
    def calculate(self, data: NDArray[np.float64]) -> float:
        """メトリクスを計算."""
        ...

def calculate_metric(
    data: NDArray[np.float64],
    metric_type: type[Metric]
) -> float:
    """汎用メトリクス計算."""
    return metric_type().calculate(data)
```

#### パターン2: 繰り返されるバリデーション
```python
# Before: 各関数で重複
def validate_price(price: float) -> None:
    if price < 0:
        raise ValueError("Price must be non-negative")

def validate_strike(strike: float) -> None:
    if strike < 0:
        raise ValueError("Strike must be non-negative")

# After: 汎用バリデーター
from typing import TypeVar, Generic

T = TypeVar('T', bound=float)

class PositiveValidator(Generic[T]):
    """正値検証クラス."""
    
    def __init__(self, name: str):
        self.name = name
    
    def validate(self, value: T) -> T:
        if value < 0:
            raise ValueError(f"{self.name} must be non-negative")
        return value

# 使用例
price_validator = PositiveValidator[float]("Price")
strike_validator = PositiveValidator[float]("Strike")
```

## 🧪 汎用テスト戦略

### テストの階層構造
```python
# tests/test_module.py
import pytest
import numpy as np
from hypothesis import given, strategies as st
from numpy.testing import assert_allclose

class TestUnit:
    """ユニットテスト：個別機能の検証."""
    
    def test_single_operation(self):
        """単一演算のテスト."""
        result = compute([1.0, 2.0, 3.0])
        assert_allclose(result, [2.0, 4.0, 6.0])

class TestProperty:
    """プロパティベーステスト：不変条件の検証."""
    
    @given(
        data=st.lists(
            st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
            min_size=1,
            max_size=1000
        )
    )
    def test_invariants(self, data: list[float]):
        """不変条件の検証."""
        array = np.array(data)
        result = compute(array)
        
        # 形状の保持
        assert result.shape == array.shape
        
        # 数値の妥当性
        assert np.isfinite(result).all()

class TestPerformance:
    """パフォーマンステスト：性能要件の検証."""
    
    @pytest.mark.benchmark
    def test_performance_requirements(self, benchmark):
        """性能要件のベンチマーク."""
        data = np.random.randn(100000)
        result = benchmark(compute, data)
        assert result is not None

class TestIntegration:
    """統合テスト：Python-Rust連携の検証."""
    
    def test_rust_interop(self):
        """Rust実装との整合性確認."""
        data = np.array([1.0, 2.0, 3.0])
        
        # Python実装
        py_result = compute_python(data)
        
        # Rust実装（PyO3経由）
        # rust_result = compute_rust(data)
        
        # assert_allclose(py_result, rust_result, rtol=1e-3)
```

### ゴールデンマスターテスト
```python
# tests/test_golden_master.py
import json
import numpy as np
from pathlib import Path
import pytest

class TestGoldenMaster:
    """既存動作の保証テスト."""
    
    @pytest.fixture
    def golden_data(self):
        """ゴールデンマスターデータの読み込み."""
        path = Path("tests/golden_master.json")
        if not path.exists():
            pytest.skip("Golden master data not found")
        
        with open(path) as f:
            return json.load(f)
    
    def test_compatibility(self, golden_data):
        """既存実装との互換性確認."""
        for test_case in golden_data["test_cases"]:
            input_data = np.array(test_case["input"])
            expected = np.array(test_case["expected"])
            
            result = compute(input_data)
            np.testing.assert_allclose(
                result, expected, 
                rtol=1e-3,
                err_msg=f"Failed for input: {input_data}"
            )
```

## 🔧 新機能追加時のチェックリスト

### 実装前
- [ ] 既存の類似実装を`similarity-py`で確認
- [ ] 再利用可能なコンポーネントの特定
- [ ] パフォーマンス要件の明確化
- [ ] エラーケースの洗い出し

### 実装中
- [ ] 完全な型アノテーションの追加
- [ ] NumPyベクトル化の検討
- [ ] 並列化戦略の選択
- [ ] ゼロコピー実装の検討
- [ ] エラーハンドリングの統一

### 実装後
- [ ] `similarity-py`による重複チェック
- [ ] `uv run ruff format .`でフォーマット
- [ ] `uv run ruff check .`でリントチェック
- [ ] `uv run mypy .`で型チェック
- [ ] `uv run pytest --cov`でテスト実行
- [ ] ドキュメントの作成

## ⚠️ 一般的な制約事項

- **数値精度**: 相対誤差 < 1e-3（金融計算では1e-3）
- **Python互換性**: 3.9以上（型ヒントのため）
- **NumPy統合**: ゼロコピーを基本とする
- **スレッド安全性**: GILの考慮
- **メモリ効率**: 入力データの2倍以内

## 🎯 品質指標

- [ ] コード重複率: 5%未満（similarity-py測定）
- [ ] テストカバレッジ: 95%以上
- [ ] 型カバレッジ: 100%（mypy strict）
- [ ] ruffエラー: 0件
- [ ] ドキュメント: 全public APIに対して100%

## 📝 リファクタリング実施例

```bash
# Step 1: 現状分析
similarity-py --threshold 0.80 src/ quantforge/ > before.md

# Step 2: 品質チェック
uv run ruff check .
uv run mypy .

# Step 3: リファクタリング実施
# - 共通パターンの抽出
# - プロトコル/ABCによる統一
# - 型アノテーションの完全化

# Step 4: 品質確認
uv run ruff format .
uv run ruff check .
uv run mypy .

# Step 5: 効果測定
similarity-py --threshold 0.80 src/ quantforge/ > after.md
diff before.md after.md

# Step 6: テスト実行
uv run pytest --cov=quantforge --cov-report=term-missing
```

このリファクタリング指示書は、既存のプロジェクトツールを最大限活用し、Pythonコードの品質を極限まで高めるための汎用的な内容となっています。
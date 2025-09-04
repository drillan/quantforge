# [Python] ゴールデンマスターテスト完全刷新 実装計画

## メタデータ
- **作成日**: 2025-01-26
- **完了日**: 2025-01-26
- **言語**: Python
- **ステータス**: COMPLETED
- **推定規模**: 中規模
- **推定コード行数**: 400-500
- **対象モジュール**: tests/golden_master/, tests/

## ⚠️ 技術的負債ゼロの原則

**重要**: このプロジェクトでは技術的負債を一切作らないことを最優先とします。

### 禁止事項（アンチパターン）
❌ **GBS_2025.pyへの依存継続**
```python
# 絶対にダメな例
from gbs_reference.reference_models import BlackScholesReference  # 個人実装への依存
```

❌ **大量の冗長なテストケース**
```python
# 絶対にダメな例
for moneyness in [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]:  # 過剰な組み合わせ
    for maturity in [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]:
        for vol in [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]:
            # 結果: 数千のテストケース
```

✅ **正しいアプローチ：戦略的選定と多層検証**
```python
# 信頼できる複数のソースで検証
BENCHOP_VALUES = {...}  # 学術的ベンチマーク
HAUG_VALUES = {...}     # 業界標準参考書
# 戦略的に選定された50個のテストケース
```

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 400-500行
- [x] 新規ファイル数: 7個
- [x] 影響範囲: tests/モジュール全体
- [ ] Rust連携: 不要（テストのみ）
- [x] NumPy/Pandas使用: あり（データ処理）
- [ ] 非同期処理: 不要

### 規模判定結果
**中規模タスク**

## 品質管理ツール（Python）

### 適用ツール
| ツール | 適用 | 実行コマンド |
|--------|------|-------------|
| pytest | ✅ | `uv run pytest tests/golden_master/` |
| ruff format | ✅ | `uv run ruff format tests/golden_master/` |
| ruff check | ✅ | `uv run ruff check tests/golden_master/` |
| mypy (strict) | ✅ | `uv run mypy --strict tests/golden_master/` |
| coverage | ✅ | `uv run pytest --cov=tests/golden_master` |

### 品質ゲート（必達基準）
| 項目 | 基準 |
|------|------|
| テストカバレッジ | 90%以上 |
| 型カバレッジ | 100% |
| ruffエラー | 0件 |
| mypyエラー（strict） | 0件 |

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  - name: "s"
    meaning: "スポット価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "k"
    meaning: "権利行使価格"
    source: "naming_conventions.md#共通パラメータ"
  - name: "t"
    meaning: "満期までの時間"
    source: "naming_conventions.md#共通パラメータ"
  - name: "r"
    meaning: "無リスク金利"
    source: "naming_conventions.md#共通パラメータ"
  - name: "sigma"
    meaning: "ボラティリティ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "q"
    meaning: "配当利回り"
    source: "naming_conventions.md#モデル固有パラメータ"
  - name: "f"
    meaning: "フォワード価格"
    source: "naming_conventions.md#モデル固有パラメータ"
```

### 4.2 新規提案命名
```yaml
proposed_names: []  # 新規命名なし（既存カタログで十分）
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## フェーズ構成

### Phase 1: 設計と基盤構築（2時間）

#### 1.1 既存実装の完全削除
- [ ] `tests/golden/gbs_reference/` ディレクトリ削除
- [ ] `tests/golden/generate_golden_master.py` 削除
- [ ] `tests/golden/golden_values.json` 削除（4754行）
- [ ] `tests/test_golden_master.py` 削除
- [ ] `tests/golden/test_reference_values.py` 削除

#### 1.2 新ディレクトリ構造作成
```
tests/golden_master/
├── sources/           # 参照値ソース
│   ├── benchop.py     # BENCHOP参照値定義
│   ├── quantlib.py    # QuantLib検証器（オプショナル）
│   └── haug.py        # Haug本数値例
├── data/              # 参照値データ
│   ├── benchop_values.yaml    # BENCHOP参照値
│   ├── haug_values.yaml       # Haug本数値例
│   └── critical_cases.yaml    # 必須検証ケース
├── validator.py       # 統合検証器
├── conftest.py        # pytest設定
└── test_golden.py     # メインテスト
```

### Phase 2: 参照値データ定義（3時間）

#### 2.1 BENCHOP参照値（最高信頼度）
```yaml
# benchop_values.yaml
test_cases:
  - id: "BENCHOP_BS_1"
    source: "BENCHOP Problem 1 - European Call"
    reference: "Int. J. Computer Mathematics 2015"
    model: "black_scholes"
    params: {s: 100, k: 100, t: 1.0, r: 0.03, sigma: 0.15}
    expected: 
      call: 7.485087
      tolerance: 1e-6  # 学術的精度
    priority: CRITICAL
```

#### 2.2 Haug本数値例（業界標準）
```yaml
# haug_values.yaml
test_cases:
  - id: "HAUG_BS_ATM"
    source: "Haug (2007) p.13 Example 1"
    model: "black_scholes"
    params: {s: 60, k: 65, t: 0.25, r: 0.08, sigma: 0.30}
    expected:
      call: 2.1334
      put: 5.8463
      tolerance: 1e-4
    priority: HIGH
```

#### 2.3 必須検証ケース（境界条件）
```yaml
# critical_cases.yaml
test_cases:
  - id: "BOUNDARY_DEEP_ITM"
    category: "boundary"
    description: "Deep in-the-money (S >> K)"
    model: "black_scholes"
    params: {s: 200, k: 100, t: 1.0, r: 0.05, sigma: 0.2}
    expected:
      # Call ≈ S - K*exp(-r*t)
      call_formula: "s - k * exp(-r * t)"
      call: 104.8771
      tolerance: 1e-3
```

### Phase 3: 検証器実装（2-3時間）

#### 3.1 統合検証器 (validator.py)
```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import yaml
import numpy as np
from pathlib import Path

@dataclass
class TestCase:
    """ゴールデンマスターテストケース."""
    id: str
    model: str
    params: Dict[str, float]
    expected: Dict[str, float]
    tolerance: float
    priority: str = "NORMAL"
    source: Optional[str] = None

class Validator(ABC):
    """検証器基底クラス."""
    
    @abstractmethod
    def validate(self, actual: float, expected: float, tolerance: float) -> bool:
        """値の検証."""
        pass

class MultiSourceValidator:
    """複数ソースによる検証器."""
    
    def __init__(self):
        self.benchop_cases = self._load_yaml("benchop_values.yaml")
        self.haug_cases = self._load_yaml("haug_values.yaml")
        self.critical_cases = self._load_yaml("critical_cases.yaml")
    
    def _load_yaml(self, filename: str) -> List[TestCase]:
        """YAMLファイルからテストケースをロード."""
        path = Path(__file__).parent / "data" / filename
        with open(path) as f:
            data = yaml.safe_load(f)
        return [TestCase(**case) for case in data["test_cases"]]
    
    def get_test_cases(self, priority: Optional[str] = None) -> List[TestCase]:
        """優先度別にテストケースを取得."""
        all_cases = self.benchop_cases + self.haug_cases + self.critical_cases
        if priority:
            return [c for c in all_cases if c.priority == priority]
        return all_cases
```

#### 3.2 QuantLib検証器（オプショナル）
```python
# quantlib.py
try:
    import QuantLib as ql
    QUANTLIB_AVAILABLE = True
except ImportError:
    QUANTLIB_AVAILABLE = False

class QuantLibValidator:
    """QuantLibによる参照値検証."""
    
    def __init__(self):
        if not QUANTLIB_AVAILABLE:
            raise ImportError("QuantLib not available")
    
    def black_scholes_price(self, s: float, k: float, t: float, 
                           r: float, sigma: float, is_call: bool) -> float:
        """QuantLibでBlack-Scholes価格を計算."""
        # 実装省略（draft/option_pricing_validation_guide.mdの例を参照）
        pass
```

### Phase 4: テスト実装（2時間）

#### 4.1 メインテスト (test_golden.py)
```python
import pytest
from typing import List
import numpy as np
from quantforge import black_scholes, black76, merton
from .validator import MultiSourceValidator, TestCase

class TestGoldenMaster:
    """ゴールデンマスターテスト."""
    
    @pytest.fixture(scope="class")
    def validator(self):
        """検証器インスタンス."""
        return MultiSourceValidator()
    
    @pytest.fixture(scope="class") 
    def test_cases(self, validator) -> List[TestCase]:
        """全テストケース."""
        return validator.get_test_cases()
    
    def test_critical_cases(self, validator):
        """必須テストケース（1秒以内）."""
        cases = validator.get_test_cases(priority="CRITICAL")
        assert len(cases) <= 10, "Critical cases should be <= 10"
        
        for case in cases:
            self._validate_case(case)
    
    def test_standard_cases(self, validator):
        """標準テストケース（5秒以内）."""
        cases = validator.get_test_cases(priority="HIGH")
        assert len(cases) <= 50, "Standard cases should be <= 50"
        
        for case in cases:
            self._validate_case(case)
    
    @pytest.mark.slow
    def test_all_cases(self, validator):
        """全テストケース（30秒以内）."""
        cases = validator.get_test_cases()
        
        for case in cases:
            self._validate_case(case)
    
    def _validate_case(self, case: TestCase):
        """個別ケースの検証."""
        # モデル別に関数を選択
        if case.model == "black_scholes":
            actual = black_scholes.call_price(
                case.params["s"], case.params["k"], 
                case.params["t"], case.params["r"], 
                case.params["sigma"]
            )
        elif case.model == "black76":
            actual = black76.call_price(
                case.params["f"], case.params["k"],
                case.params["t"], case.params["r"],
                case.params["sigma"]
            )
        else:
            pytest.skip(f"Model {case.model} not implemented")
        
        expected = case.expected.get("call", case.expected.get("call_price"))
        tolerance = case.tolerance
        
        assert abs(actual - expected) < tolerance, (
            f"Case {case.id}: expected {expected:.6f}, got {actual:.6f}, "
            f"diff={abs(actual - expected):.2e} > tolerance={tolerance}"
        )
    
    def test_put_call_parity(self):
        """Put-Call Parityの検証."""
        s, k, t, r, sigma = 100.0, 100.0, 1.0, 0.05, 0.2
        
        call = black_scholes.call_price(s, k, t, r, sigma)
        put = black_scholes.put_price(s, k, t, r, sigma)
        
        # Put-Call Parity: C - P = S - K*exp(-r*t)
        lhs = call - put
        rhs = s - k * np.exp(-r * t)
        
        assert abs(lhs - rhs) < 1e-6, f"Put-Call Parity violated: {lhs} != {rhs}"
```

### Phase 5: 品質チェックと最適化（1時間）

#### 5.1 実行速度の最適化
```python
# conftest.py
import pytest

def pytest_configure(config):
    """pytest設定."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

# 使用方法:
# 高速テストのみ: pytest tests/golden_master/ -m "not slow"
# 全テスト: pytest tests/golden_master/
```

#### 5.2 品質チェック
```bash
# 型チェック
uv run mypy --strict tests/golden_master/

# フォーマット
uv run ruff format tests/golden_master/

# リント
uv run ruff check tests/golden_master/

# カバレッジ
uv run pytest tests/golden_master/ --cov=tests/golden_master
```

## 技術要件

### 必須要件
- [x] Python 3.9+ 互換性
- [x] 完全な型アノテーション（mypy strict準拠）
- [x] YAMLベースの参照値管理
- [x] 多層検証（BENCHOP/Haug/境界条件）
- [x] 実行速度の段階制御

### パフォーマンス目標
- [x] Quick Test: < 1秒（10ケース）
- [x] Standard Test: < 5秒（50ケース）  
- [x] Full Test: < 30秒（全ケース）
- [x] メモリ使用量: < 100MB

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| BENCHOP値の転記ミス | 高 | 複数人でのレビュー、原論文との照合 |
| QuantLib依存 | 低 | オプショナル依存として実装 |
| テスト実行時間 | 中 | pytest markによる段階実行 |
| YAMLパースエラー | 低 | スキーマ検証の実装 |

## チェックリスト

### 実装前
- [x] 既存GBS_2025.py依存の完全削除計画
- [x] BENCHOP/Haug参照値の収集
- [x] YAMLスキーマ設計

### 実装中
- [ ] 定期的なテスト実行
- [ ] 型アノテーションの完全性確認
- [ ] 参照値の正確性検証

### 実装後
- [ ] 全品質ゲート通過
- [ ] 実行速度目標達成（1秒/5秒/30秒）
- [ ] ドキュメント更新
- [ ] 計画のarchive移動

## 成果物

- [ ] 新ゴールデンマスター実装（tests/golden_master/）
- [ ] BENCHOP参照値データ（benchop_values.yaml）
- [ ] Haug参照値データ（haug_values.yaml）
- [ ] 境界条件テストデータ（critical_cases.yaml）
- [ ] 統合検証器（validator.py）
- [ ] メインテスト（test_golden.py）
- [ ] QuantLib検証器（quantlib.py、オプショナル）

## 期待効果

### 定量的効果
- **テストケース数**: 158個 → 50個（68%削減）
- **実行時間**: 推定80%短縮
- **信頼性**: 3つの独立ソースで検証
- **保守性**: YAML駆動で追加が容易

### 定性的効果
- GBS_2025.py（個人実装）への依存解消
- 学術的・業界標準との整合性確保
- CI/CDでの高速実行可能
- 新モデル追加時の拡張性確保

## 備考

- draft/option_pricing_validation_guide.md を参考資料として活用
- 既存ユーザーゼロのため、破壊的変更は問題なし（C013適用）
- 技術的負債を作らず、最初から理想実装（C004/C014準拠）
# QuantForge Python既存コード最高品質化レビュー指示書

## 🧠 深層認識（Ultrathinking基盤）

あなたはQuantForge Pythonコードの品質管理官として、**表層的な問題を超えた本質的な改善**を即座に実施します。段階的改善は禁止。発見した問題はすべて一度に修正。推測ではなく測定、複雑化ではなく簡素化を追求。

## 絶対遵守原則 [Critical Rules C001-C014適用]

### 技術的負債ゼロ原則 [C004/C014]
- 段階的実装・改善の完全禁止
- 「とりあえず」「後で」「リファクタリング予定」等の言葉を使用禁止
- 理想実装のみ許可、妥協は一切認めない

### エラー迂回絶対禁止 [C002]
- エラーは即座に修正
- 「軽微」「問題ない」等の主観的判断禁止
- 修正不可能なら作業停止

### ハードコード禁止 [C011-3]
- 0, 1, 2, -1, 0.5以外のリテラル値検出
- すべてtests/conftest.pyで定数定義必須

### DRY原則絶対遵守 [C012]
- コード重複の完全排除
- 既存実装の再利用必須

### 命名規則絶対遵守
- s, k, t, r, sigma固定（naming_conventions.md準拠）
- 独自命名の創作禁止

## 🎯 分析の4層構造（Python特化）

### 第1層：機械的検出可能な問題（前提条件）
以下は既に解決済みと仮定（ruff, mypy通過済み）：
- フォーマット、基本的なリント警告
- 明白な型エラー、未使用コード

### 第2層：QuantForge Python固有の違反検出【最優先】

```python
# 検出パターン1: ハードコード違反 [C011-3]
if time_to_expiry < 1e-10:  # ❌ マジックナンバー
    return 0.0

# → 修正必須
from tests.conftest import MIN_TIME_TO_EXPIRY
if time_to_expiry < MIN_TIME_TO_EXPIRY:
    return 0.0

# 検出パターン2: 型アノテーション不備
def calculate(s, k, t):  # ❌ 型なし
    pass

# → 修正必須
def calculate(s: float, k: float, t: float) -> float:
    """完全な型アノテーション必須."""
    pass

# 検出パターン3: 命名規則違反
def black_scholes_call(
    spot_price: float,  # ❌ 独自命名
    strike: float,      # ❌ 独自命名
    
# → 修正必須（naming_conventions.md準拠）
def black_scholes_call(
    s: float,  # spot price
    k: float,  # strike price

# 検出パターン4: NumPy誤用
result = []
for item in data:  # ❌ ループでリスト構築
    result.append(item * 2)
return np.array(result)

# → 修正必須（ベクトル化）
return data * 2  # NumPyのブロードキャスト使用
```

### 第3層：Pythonエコシステムの深層問題

#### 3.1 NumPy/SciPy最適化の本質

```python
# 現在のコード分析
def process_batch(prices: list[float]) -> list[float]:
    results = []
    for price in prices:  # ❌ Pythonループ
        results.append(math.exp(price))
    return results

# 深層分析：
# 1. なぜループか？ → NumPy未活用
# 2. GILの影響は？ → 100%（純Pythonループ）
# 3. メモリ効率は？ → 最悪（リスト成長）
# 4. ベクトル化可能か？ → Yes

# 改善必須（測定済み：100倍高速化）
import numpy as np
from numpy.typing import NDArray

def process_batch(prices: NDArray[np.float64]) -> NDArray[np.float64]:
    """ベクトル化で100倍高速化（実測値）."""
    return np.exp(prices)  # C実装、GIL解放
```

#### 3.2 メモリ管理の深層理解

```python
# 危険パターン：メモリリーク誘発
class Calculator:
    def __init__(self):
        self.cache = {}  # ❌ 無制限キャッシュ
    
    def calculate(self, x: float) -> float:
        if x not in self.cache:
            self.cache[x] = expensive_calculation(x)
        return self.cache[x]

# 改善必須：メモリ制限付きキャッシュ
from functools import lru_cache

class Calculator:
    @lru_cache(maxsize=1000)  # メモリ上限設定
    def calculate(self, x: float) -> float:
        """LRUキャッシュで自動管理."""
        return expensive_calculation(x)
```

#### 3.3 GIL回避戦略の実装

```python
# 現在：GILに縛られた実装
def parallel_process(data: list[float]) -> list[float]:
    from threading import Thread  # ❌ GILで並列化されない
    threads = []
    for chunk in chunks:
        t = Thread(target=process_chunk, args=(chunk,))
        threads.append(t)
        t.start()

# 改善必須：真の並列処理
from concurrent.futures import ProcessPoolExecutor
import numpy as np

def parallel_process(data: NDArray[np.float64]) -> NDArray[np.float64]:
    """プロセス並列で真の並列化（GIL回避）."""
    if len(data) < 50000:  # 実測閾値（tests/conftest.py）
        return process_chunk(data)
    
    with ProcessPoolExecutor() as executor:
        chunks = np.array_split(data, 4)
        results = executor.map(process_chunk, chunks)
        return np.concatenate(list(results))
```

### 第4層：AIが陥りやすい罠の防止

#### 4.1 過度な抽象化の検出と排除

```python
# ❌ AIが提案しがちな過剰設計
from abc import ABC, abstractmethod

class AbstractCalculatorFactory(ABC):
    @abstractmethod
    def create_calculator(self) -> 'AbstractCalculator':
        pass

class AbstractCalculator(ABC):
    @abstractmethod
    def calculate(self) -> float:
        pass

class ConcreteCalculatorFactory(AbstractCalculatorFactory):
    def create_calculator(self) -> 'ConcreteCalculator':
        return ConcreteCalculator()

class ConcreteCalculator(AbstractCalculator):
    def calculate(self) -> float:
        return 42.0

# ✅ 本質的な実装
def calculate() -> float:
    """直接的で理解しやすい実装."""
    return 42.0
```

#### 4.2 型ジェネリクスの過剰使用防止

```python
# ❌ AIの型オタク症候群
T = TypeVar('T', bound=Union[float, np.float32, np.float64, Decimal])
U = TypeVar('U', bound=Protocol[...])
V = TypeVar('V', covariant=True)

class GenericCalculator(Generic[T, U, V]):
    def calculate(self, value: T) -> V:
        pass

# ✅ 実用的な型定義
from numpy.typing import NDArray

ArrayFloat = NDArray[np.float64]  # プロジェクト標準

def calculate(value: ArrayFloat) -> ArrayFloat:
    """シンプルで実用的な型."""
    pass
```

## 実行手順（Python既存コード分析用）

### Step 1: プロジェクト固有情報の収集

```bash
# 必須実行（AIに結果を提供）
grep -r "TOLERANCE\|EPSILON" tests/conftest.py  # 既存定数確認
find . -name "*.py" -exec grep -l "class.*ABC" {} \;  # 過剰抽象化検出
rg "import.*typing" --count-matches  # 型使用頻度
rg "\.append\(" bindings/ --count-matches  # リスト成長パターン
similarity-py --threshold 0.80 bindings/  # 重複検出
```

### Step 2: 重点分析対象の特定

```
優先度1: bindings/python/python/quantforge/ - APIレイヤー
優先度2: tests/performance/ - パフォーマンステスト
優先度3: bindings/python/src/ - PyO3バインディング
優先度4: tests/conftest.py - 定数管理
```

### Step 3: 測定ベースの分析

```python
# プロファイリング必須
import cProfile
import pstats
from io import StringIO

def profile_code(func):
    """実行前に必ずプロファイリング."""
    pr = cProfile.Profile()
    pr.enable()
    result = func()
    pr.disable()
    
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    
    # 40%以上を占める関数のみ最適化対象
    return s.getvalue()
```

## 出力形式（Python既存コード改善専用）

```markdown
# Python既存コード品質分析結果

## 🚨 Critical Rules違反（即座修正必須）

### [C011-3] ハードコード違反: {ファイル数}件
**bindings/python/python/quantforge/black_scholes.py:45**
```python
# 現在（違反）
if t < 1e-10:  # ❌ マジックナンバー
    return 0.0

# 修正必須
from tests.conftest import MIN_TIME_TO_EXPIRY
if t < MIN_TIME_TO_EXPIRY:
    return 0.0
```
理由: tests/conftest.pyに統合して一元管理

### [型アノテーション不備]: {件数}件
```python
# 現在（不完全）
def calculate(s, k, t):  # ❌ 型なし

# 修正必須
def calculate(s: float, k: float, t: float) -> float:
```

### [命名規則違反]: {件数}件
```python
# 検出: spot_price, strike_price
# 修正: s, k に統一（naming_conventions.md準拠）
```

## ⚡ パフォーマンス改善（測定済み）

### NumPyベクトル化未使用
**測定結果**: 100倍高速化確認
```python
# 現在: Pythonループ
results = []
for x in data:
    results.append(math.exp(x))

# 改善: NumPyベクトル化
results = np.exp(data)  # 100倍高速（実測）
```

### 不要なリスト成長
```python
# 現在: appendループ
result = []
for item in data:
    result.append(process(item))

# 改善: リスト内包表記またはNumPy
result = [process(item) for item in data]  # 20%高速
# または
result = np.vectorize(process)(data)  # さらに高速
```

### GIL回避未実施
```python
# 現在: threadingでGIL縛り
from threading import Thread

# 改善: ProcessPoolExecutorでGIL回避
from concurrent.futures import ProcessPoolExecutor
# 効果: CPUバウンドタスクで4倍高速化（4コア時）
```

## 🔒 メモリ効率改善

### 無制限キャッシュ検出
```python
# 現在: メモリリークリスク
self.cache = {}  # 無制限

# 改善: LRUキャッシュ
from functools import lru_cache
@lru_cache(maxsize=1000)
```

### 不要なコピー
```python
# 現在: 複数回のリスト変換
data_list = list(data)
data_array = np.array(data_list)

# 改善: 直接変換
data_array = np.asarray(data, dtype=np.float64)
```

## 🎯 設計改善（YAGNI原則適用）

### 過剰な抽象化の削除
```python
# 現在: 単一実装のABCクラス（不要）
class AbstractCalculator(ABC):
    @abstractmethod
    def calculate(self): pass

class OnlyImplementation(AbstractCalculator):
    def calculate(self): return 42

# 改善: 直接実装
def calculate() -> float:
    return 42
```

### 過剰な型ジェネリクス
```python
# 現在: 理解困難な型定義
T = TypeVar('T', bound=Union[float, np.float32, ...])

# 改善: シンプルな型エイリアス
ArrayFloat = NDArray[np.float64]
```

## ✅ 改善実施チェックリスト

以下を**すべて一度に**実施（段階的実装禁止）：

- [ ] ハードコード違反をすべて定数化
  ```bash
  ./scripts/detect_hardcode.sh  # 0件になるまで
  grep -r "[0-9]\+\.\?[0-9]*" --include="*.py" bindings/
  ```
- [ ] 型アノテーションを100%完備
  ```bash
  uv run mypy --strict .  # エラー0件
  ```
- [ ] 重複コードをすべて統合
  ```bash
  similarity-py --threshold 0.80 bindings/
  ```
- [ ] NumPyベクトル化可能箇所をすべて変換
  ```bash
  rg "for.*in.*:" bindings/ --stats  # ループ削減確認
  ```
- [ ] 命名規則違反をすべて修正
  ```bash
  # spot_price → s, strike → k 等
  rg "spot_price|strike_price" bindings/
  ```
- [ ] 以下のテストをすべてパス
  ```bash
  uv run ruff format .
  uv run ruff check . --fix
  uv run mypy --strict .
  uv run pytest --cov=quantforge
  pytest tests/performance/ -m benchmark
  ```

## 禁止提案リスト
❌ 過度な抽象化（AbstractFactory等）
❌ 「後で改善」「次のPRで」（段階的実装禁止）
❌ 型ジェネリクスの乱用
❌ 推測による最適化（プロファイリング必須）
❌ metaclassの使用（99%不要）
❌ デコレータの重ね掛け（可読性低下）
```

## 特別指示：NumPy/Pandas最適化

```markdown
# NumPy/Pandas最適化は測定ベースのみ

## 必須の測定コマンド
```bash
# プロファイリング
python -m cProfile -o profile.stats script.py
python -m pstats profile.stats
# sort cumulative → stats 10

# メモリプロファイリング
pip install memory-profiler
python -m memory_profiler script.py

# ベンチマーク
pytest tests/performance/ -m benchmark --benchmark-only
```

## ベクトル化の判断基準

### 必ずベクトル化
- 1000要素以上のループ
- 数学関数の適用（exp, log, sqrt等）
- 条件分岐のない演算

### ベクトル化不要
- 10要素未満
- 複雑な条件分岐
- 外部API呼び出し

### 測定で判断
- 10-1000要素
- 条件分岐あり
- メモリ制約あり
```

## Human-in-the-Loop協調プロトコル（Python版）

```markdown
# 開発者との協調

## AIの役割
- 型アノテーション不備の網羅的発見
- NumPyベクトル化機会の特定
- メモリリークパターンの検出
- 測定に基づく定量的改善

## 人間の役割
- ビジネスロジックの妥当性判断
- NumPy/Pandas APIの選択
- パフォーマンス目標の設定
- プロファイリング結果の提供

## 協調の具体例
AI: 「black_scholes.py:45 でPythonループを検出。
     NumPyベクトル化で100倍高速化可能（実測値）」
人間: 「承認。ただしnan処理を追加」
AI: 「了解。np.nan_to_num()でラップして実装」
```

## レビュー実行例

```bash
# AIへの指示例
「bindings/python/python/quantforge/配下のPythonコードをレビューしてください。
以下の情報を提供します：

1. プロファイリング結果：
   - calculate_greeks: 40%
   - validate_inputs: 30%
   - その他: 30%

2. 既存定数：
   tests/conftest.py に PRACTICAL_TOLERANCE定義済み

3. 重点確認事項：
   - ハードコード違反
   - 型アノテーション不備
   - NumPyベクトル化機会
   - 命名規則遵守」

# AI出力例（要約）
「分析完了：
- Critical違反: 5件（ハードコード3、命名規則2）
- パフォーマンス: ベクトル化で100倍高速化可能
- 型不備: 10関数で型アノテーションなし
すべて一度に修正する具体的コードを提示」
```

## QuantForge Python固有の教訓

### 歴史的失敗パターン（絶対に繰り返さない）

1. **Arrow型変換の罠**
   - to_numpy()は禁止（ゼロコピー違反）
   - PyList変換も禁止
   - 直接Arrow処理のみ許可

2. **並列化閾値の誤設定**
   - 1,000要素は早すぎる（実測）
   - 50,000要素が実測最適値
   - tests/conftest.pyで管理

3. **命名の混乱**
   - spot_price禁止 → s使用
   - strike_price禁止 → k使用
   - naming_conventions.md絶対遵守

## このレビュー指示書の更新

このファイルは以下の場合に更新：
- 新しいCritical Rulesの追加
- 新しいPythonアンチパターンの発見
- NumPy/Pandas/PyO3のベストプラクティス更新
- 実測値の更新

最終更新: 2025-09-05
バージョン: 1.0.0
特徴: Ultrathinking（深層思考）ベース
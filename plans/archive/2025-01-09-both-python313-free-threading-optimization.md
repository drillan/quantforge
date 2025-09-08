# [Both] Python 3.13 Free Threading最適化 実装計画

## メタデータ
- **作成日**: 2025-01-09
- **言語**: Both (Rust + Python)
- **ステータス**: DRAFT
- **推定規模**: 大
- **推定コード行数**: 1000+
- **対象モジュール**: 
  - pyproject.toml（完全書き換え）
  - Cargo.toml (workspace + bindings)
  - bindings/python/src/*.rs
  - tests/performance/*.py

## タスク規模判定

### 判定基準
- [x] 推定コード行数: 1000+ 行
- [x] 新規ファイル数: 10+ 個（新テスト、ベンチマーク）
- [x] 影響範囲: 全体（ビルドシステム、全モジュール）
- [x] PyO3バインディング: 必要（Free Threading対応）
- [ ] SIMD最適化: 不要（Free Threadingに集中）
- [x] 並列化: 必要（Free Threading最大活用）

### 規模判定結果
**大規模タスク**

## 命名定義セクション

### 4.1 使用する既存命名
```yaml
existing_names:
  # 変更なし - 既存のAPIパラメータ名を維持
  - name: "s, k, t, r, sigma"
    meaning: "Black-Scholesパラメータ"
    source: "naming_conventions.md#共通パラメータ"
  - name: "spots, strikes, times, rates, sigmas"
    meaning: "バッチ処理配列パラメータ"
    source: "naming_conventions.md#バッチ処理"
```

### 4.2 新規提案命名
```yaml
proposed_names:
  - name: "PARALLEL_THRESHOLD_NO_GIL"
    meaning: "Free Threading時の並列化閾値"
    justification: "GIL有無で最適値が大きく異なるため"
    references: "内部ベンチマーク結果"
    status: "pending_approval"
  - name: "free_threading_enabled"
    meaning: "Free Threadingビルド検出フラグ"
    justification: "実行時の動的最適化切替用"
    references: "Python 3.13 docs"
    status: "pending_approval"
```

### 4.3 命名の一貫性チェックリスト
- [x] 既存モデルとの整合性確認
- [x] naming_conventions.mdとの一致確認
- [x] ドキュメントでの使用方法定義
- [x] APIパラメータは省略形を使用
- [x] エラーメッセージでもAPI名を使用

## Python 3.13.7 最新機能

### 主要な新機能（2025年8月14日リリース）
1. **Free Threading（実験的）**
   - GIL無効化による真の並列実行
   - `--disable-gil`ビルドオプション
   - 実行時の`-X gil=0`フラグ

2. **JITコンパイラ（実験的）**
   - デフォルト無効、明示的有効化が必要
   - ホットパスの自動最適化

3. **改善されたインタラクティブインタープリタ**
   - マルチライン編集
   - カラー出力サポート
   - カラー化された例外トレースバック

4. **型システムの改善**
   - 型パラメータのデフォルト値サポート
   - `typing.TypeIs`による型絞り込み
   - 非推奨アノテーション

## 実装方針

### 破壊的変更の前提
- **既存ユーザーゼロ** → 後方互換性完全無視
- **pyproject.toml完全書き換え** → Python 3.13.7専用
- **実験ブランチ** → `experiment/python313-max-performance`
- **判定基準明確** → 速ければ採用、遅ければ破棄

## フェーズ構成

### Phase 1: 環境構築とブランチ作成（Day 1）

#### 1.1 実験ブランチ作成
```bash
git checkout -b experiment/python313-max-performance
```

#### 1.2 UV でPython 3.13.7環境構築
```bash
# UV自体を最新版に更新
curl -LsSf https://astral.sh/uv/install.sh | sh

# Python 3.13.7（最新版）をインストール
uv python install 3.13.7

# プロジェクトでPython 3.13.7を使用
uv python pin 3.13.7

# Free Threading版のPython 3.13tもインストール（利用可能な場合）
# 注: Free Threading版は別途ビルドが必要な場合があります
uv python install 3.13t
```

#### 1.3 ベースラインベンチマーク
```bash
# 現在のPython 3.12での性能測定
uv run pytest tests/performance/ -m benchmark --benchmark-json=baseline_py312.json
```

### Phase 2: Python 3.13専用化（Day 2）

#### 2.1 pyproject.toml完全書き換え
```toml
# pyproject.toml - Python 3.13.7専用に完全書き換え
[build-system]
requires = ["maturin>=1.7,<2.0"]
build-backend = "maturin"

[project]
name = "quantforge"
dynamic = ["version"]
description = "Ultra-high-performance option pricing with Python 3.13.7 Free Threading"
readme = "README.md"
license = {file = "LICENSE"}
requires-python = "==3.13.*"  # Python 3.13のみ
dependencies = [
    "numpy>=2.0",  # Python 3.13対応版
    "psutil>=7.0.0",
    "pyarrow>=18.0.0",  # 最新版
    "arro3-core>=0.4.0",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Rust",
    "Topic :: Office/Business :: Financial :: Investment",
    "Operating System :: OS Independent",
]
keywords = ["quantitative-finance", "options", "black-scholes", "free-threading", "gil-free", "high-performance"]

[project.urls]
Homepage = "https://github.com/drillan/quantforge"
Repository = "https://github.com/drillan/quantforge.git"
Issues = "https://github.com/drillan/quantforge/issues"

[dependency-groups]
dev = [
    "maturin>=1.9.3",
    "mypy>=1.17.1",
    "pytest>=8.4.1",
    "pytest-benchmark>=5.1.0",
    "pytest-cov>=6.0.0",
    "pytest-xdist>=3.6.1",
    "pytest-timeout>=2.3.1",
    "pytest-mock>=3.14.0",
    "hypothesis>=6.100.0",
    "ruff>=0.12.10",
    "scipy>=1.16.1",
    "types-pyyaml>=6.0.12.20250822",
    "scipy-stubs>=1.16.1.1",
    "types-psutil>=7.0.0.20250822",
    "pyyaml>=6.0.2",
]

test = [
    "pytest>=8.4.1",
    "pytest-benchmark>=5.1.0",
    "scipy>=1.16.1",
    "pyarrow>=18.0.0",
]

[tool.uv]
python = "3.13.7"
preview = true  # UV最新機能を使用

[tool.ruff]
target-version = "py313"  # Python 3.13専用
line-length = 120
indent-width = 4
exclude = [
    "playground/",
    ".internal/",
]

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade (Python 3.13対応)
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
    "PERF", # Performance linting
]

[tool.maturin]
features = ["pyo3/extension-module"]
module-name = "quantforge.quantforge"
manifest-path = "bindings/python/Cargo.toml"
python-source = "bindings/python/python"

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = [".", "benchmarks"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "-p no:warnings",  # Free Threading警告を抑制
]
markers = [
    "benchmark: marks tests as benchmark tests",
    "free_threading: marks tests requiring Free Threading",
]

[tool.mypy]
python_version = "3.13"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
no_implicit_optional = true
strict_equality = true
exclude = [
    "playground/",
    ".internal/",
]
```

#### 2.2 Cargo.toml更新（Python 3.13専用）
```toml
# Cargo.toml
[workspace.dependencies]
# PyO3をPython 3.13専用に最適化
pyo3 = { version = "0.25.1", features = [
    "extension-module",
    "gil-refs",  # Free Threading対応
    # abi3削除 - Python 3.13専用バイナリ
]}
pyo3-arrow = "0.11.0"
numpy = "0.25"

# Arrow最新版
arrow = { version = "56.0", features = ["ffi", "pyarrow"] }
arrow-array = "56.0"
arrow-buffer = "56.0"
```

#### 2.3 Free Threading検出コード
```rust
// bindings/python/src/lib.rs
use pyo3::prelude::*;

/// Free Threading検出
#[cfg(Py_GIL_DISABLED)]
const FREE_THREADING: bool = true;
#[cfg(not(Py_GIL_DISABLED))]
const FREE_THREADING: bool = false;

/// 動的な並列化閾値
pub fn get_parallel_threshold() -> usize {
    if FREE_THREADING {
        1_000  // GILなし: 積極的な並列化
    } else {
        50_000 // GIL有り: 保守的な閾値
    }
}

#[pyfunction]
fn is_free_threading() -> bool {
    FREE_THREADING
}

#[pymodule]
fn quantforge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(is_free_threading, m)?)?;
    // ... 他の関数
    Ok(())
}
```

### Phase 3: Free Threading最適化（Day 3-4）

#### 3.1 並列処理の再設計
```rust
// bindings/python/src/models.rs
use rayon::prelude::*;

#[cfg(Py_GIL_DISABLED)]
pub fn parallel_batch_process_no_gil<'py>(
    py: Python<'py>,
    spots: PyArray,
    strikes: PyArray,
    times: PyArray,
    rates: PyArray,
    sigmas: PyArray,
) -> PyResult<PyObject> {
    // GILなしで真の並列処理
    py.allow_threads(|| {
        // 各配列を並列で検証
        let validations = rayon::join5(
            || validate_positive_array(&spots),
            || validate_positive_array(&strikes),
            || validate_positive_array(&times),
            || validate_rate_array(&rates),
            || validate_volatility_array(&sigmas),
        );
        
        // エラーチェック
        let (s, k, t, r, sig) = validations;
        
        // メイン計算も完全並列
        compute_prices_parallel(s?, k?, t?, r?, sig?)
    })
}
```

#### 3.2 Arrow処理の最適化
```rust
// bindings/python/src/arrow_common.rs
#[cfg(Py_GIL_DISABLED)]
pub fn arrow_parallel_optimized(
    arrays: Vec<PyArray>,
    threshold: usize,
) -> PyResult<Vec<PyArray>> {
    // Free Threading環境での最適化
    if arrays.len() > threshold {
        // 大量データは並列処理
        arrays.par_iter()
            .map(|arr| process_arrow_array(arr))
            .collect::<Result<Vec<_>, _>>()
    } else {
        // 少量データはシーケンシャル
        arrays.iter()
            .map(|arr| process_arrow_array(arr))
            .collect()
    }
}
```

#### 3.3 UV環境でのテスト実行
```bash
# UV環境でのテスト準備
uv sync --group dev

# 通常のPython 3.13.7でテスト
uv run pytest tests/

# Free Threading版でテスト（利用可能な場合）
UV_PYTHON=3.13t uv run python -X gil=0 -m pytest tests/
```

### Phase 4: ベンチマーク計測（Day 5）

#### 4.1 測定スクリプト
```python
# tests/performance/test_free_threading_benchmark.py
import sys
import pytest
import numpy as np
from quantforge import black_scholes, is_free_threading

@pytest.fixture(scope="session")
def report_environment():
    """環境情報をレポート"""
    print(f"\nPython Version: {sys.version}")
    print(f"Free Threading: {is_free_threading()}")
    print(f"NumPy Version: {np.__version__}")

@pytest.mark.benchmark
def test_single_calculation(benchmark):
    """単一計算: 目標 < 35ns維持"""
    result = benchmark(
        black_scholes.call_price,
        100.0, 100.0, 1.0, 0.05, 0.2
    )
    assert result > 0

@pytest.mark.benchmark
@pytest.mark.parametrize("size", [1_000, 10_000, 100_000, 1_000_000])
def test_batch_performance(benchmark, size):
    """バッチ処理: サイズ別性能測定"""
    spots = np.random.uniform(80, 120, size)
    strikes = np.full(size, 100.0)
    times = np.full(size, 1.0)
    rates = np.full(size, 0.05)
    sigmas = np.random.uniform(0.1, 0.3, size)
    
    result = benchmark(
        black_scholes.call_price_batch,
        spots, strikes, times, rates, sigmas
    )
    assert len(result) == size

@pytest.mark.benchmark
@pytest.mark.free_threading
def test_parallel_scaling(benchmark):
    """並列スケーリング: Free Threading効果測定"""
    size = 1_000_000
    # 大量データで並列効果を測定
    spots = np.random.uniform(80, 120, size)
    
    result = benchmark(
        black_scholes.call_price_batch,
        spots, 100.0, 1.0, 0.05, 0.2
    )
    assert len(result) == size

@pytest.mark.benchmark
def test_arrow_performance(benchmark):
    """Arrow処理: ゼロコピー + Free Threading"""
    import pyarrow as pa
    
    size = 100_000
    spots = pa.array(np.random.uniform(80, 120, size))
    
    result = benchmark(
        black_scholes.arrow_call_price,
        spots, 100.0, 1.0, 0.05, 0.2
    )
    assert len(result) == size
```

#### 4.2 UV環境での比較実行
```bash
# ベースライン（現在のPython 3.12）
uv python pin 3.12
uv sync
uv run pytest tests/performance/ -m benchmark \
    --benchmark-json=baseline_py312.json

# Python 3.13.7通常ビルド
uv python pin 3.13.7
uv sync
uv run pytest tests/performance/ -m benchmark \
    --benchmark-json=py313_normal.json

# Python 3.13.7 Free Threading（利用可能な場合）
UV_PYTHON=3.13t uv run python -X gil=0 -m pytest \
    tests/performance/ -m "benchmark and free_threading" \
    --benchmark-json=py313_free_threading.json

# 比較レポート生成
uv run python .internal/benchmark_automation/compare_results.py \
    baseline_py312.json \
    py313_normal.json \
    py313_free_threading.json \
    --output=performance_report.md
```

### Phase 5: 判定と決定（Day 6）

#### 5.1 採用判定基準

| 項目 | 基準値 | 測定結果 | 判定 |
|------|--------|----------|------|
| 単一計算 | < 40ns | ?ns | ? |
| 10K batch vs NumPy | > 1.5x | ?x | ? |
| 100K batch vs NumPy | > 2.0x | ?x | ? |
| 1M batch vs NumPy | > 3.0x | ?x | ? |
| メモリ使用量増加 | < 2x | ?x | ? |
| 全テスト合格 | 100% | ?% | ? |

#### 5.2 実行コマンド
```bash
# 性能向上が確認された場合
if [[ $PERFORMANCE_IMPROVED == true ]]; then
    git checkout main
    git merge --no-ff experiment/python313-max-performance
    echo "✅ Python 3.13.7 Free Threading採用完了"
    
    # リリースビルド
    uv run maturin build --release
    
    # バージョン更新
    echo "0.1.0" > VERSION
    git add -A
    git commit -m "feat: migrate to Python 3.13.7 with Free Threading support
    
    - Python 3.13.7専用化（後方互換性削除）
    - Free Threading実験的サポート
    - 並列処理性能の大幅改善
    - UV環境管理への完全移行"
    
# 性能向上なしの場合
else
    git checkout main
    git branch -D experiment/python313-max-performance
    echo "❌ Python 3.13移行は性能向上なしのため破棄"
    echo "Python 3.12環境を維持します"
fi
```

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Free Threadingの不安定性 | 高 | 徹底的なストレステスト実施 |
| UV環境での互換性問題 | 低 | UV最新版使用、事前検証 |
| 依存ライブラリ非対応 | 中 | numpy 2.0+, pyarrow 18.0+使用 |
| シングルスレッド性能劣化 | 高 | 40%劣化まで許容、それ以上なら破棄 |
| JITコンパイラの不具合 | 中 | デフォルト無効、段階的有効化 |

## チェックリスト

### 実装前
- [ ] UV最新版インストール
- [ ] Python 3.13.7インストール（uv python install 3.13.7）
- [ ] ベースラインベンチマーク記録
- [ ] 依存ライブラリのPython 3.13対応確認

### 実装中
- [ ] pyproject.toml完全書き換え
- [ ] Free Threading検出コード実装
- [ ] 並列化閾値の動的切替実装
- [ ] Arrow並列処理最適化
- [ ] UV環境での全テスト合格

### 実装後
- [ ] ベンチマーク全項目測定
- [ ] 性能比較レポート作成
- [ ] 判定基準に基づく採否決定
- [ ] mainブランチへのマージ or 破棄
- [ ] 計画のarchive移動

## 成果物

- [ ] Python 3.13.7専用pyproject.toml
- [ ] Free Threading対応Rustコード
- [ ] UV環境構築手順書
- [ ] 性能比較レポート（markdown）
- [ ] 採用/破棄の判定記録

## 備考

- Python 3.13.7は2025年8月14日リリースの最新版
- Free Threadingは実験的機能だが、成功すれば革新的な性能向上
- JITコンパイラも実験的だが、将来的な最適化の可能性
- UV使用により環境構築が大幅に簡素化
- pyproject.toml完全書き換えで最適な設定を実現
- 失敗してもmainブランチは無傷で、学習価値は高い

## 参考資料

- [Python 3.13.7 Release Notes](https://www.python.org/downloads/release/python-3137/)
- [What's New In Python 3.13](https://docs.python.org/3/whatsnew/3.13.html)
- [PEP 703 – Making the Global Interpreter Lock Optional](https://peps.python.org/pep-0703/)
- [UV Documentation](https://github.com/astral-sh/uv)
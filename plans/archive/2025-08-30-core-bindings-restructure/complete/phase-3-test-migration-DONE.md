# Phase 3: テストとベンチマークの移行

## 概要
既存のテストとベンチマークを新しいCore + Bindings構造に合わせて再編成し、各層の責任範囲を明確化します。

## 前提条件
- Phase 2の完了（Bindings層の完成）
- Core層とBindings層の動作確認
- 基本的なテストの合格

## タスクリスト

### 1. テストの分類と整理 [2時間]

#### 1.1 既存テストの分析
```bash
# 現在のテスト構造を分析
find tests -name "*.py" -type f | head -20
find tests -name "*.rs" -type f | head -20

# テストの種類を分類
echo "=== Unit Tests ==="
ls tests/unit/

echo "=== Integration Tests ==="
ls tests/integration/

echo "=== Property Tests ==="
ls tests/property/

echo "=== Golden Master Tests ==="
ls tests/golden/
```

#### 1.2 テストの分類基準
| テスト種別 | 配置先 | 責任範囲 |
|-----------|--------|----------|
| Rust単体テスト | `core/tests/` | Core層のロジック |
| Rust統合テスト | `core/tests/integration/` | Core層の統合 |
| Python単体テスト | `bindings/python/tests/unit/` | Python API |
| Python統合テスト | `bindings/python/tests/integration/` | Python統合 |
| E2Eテスト | `tests/e2e/` | 全体の動作 |
| ゴールデンマスター | `tests/golden/` | 回帰防止 |

#### 1.3 移行対象リスト作成
```python
# scripts/analyze_tests.py
import os
from pathlib import Path

def categorize_tests():
    test_map = {
        'core_unit': [],
        'core_integration': [],
        'python_unit': [],
        'python_integration': [],
        'e2e': [],
        'golden': []
    }
    
    # 分類ロジック
    for test_file in Path('tests').rglob('*.py'):
        content = test_file.read_text()
        if 'import quantforge' in content:
            if 'integration' in str(test_file):
                test_map['python_integration'].append(test_file)
            else:
                test_map['python_unit'].append(test_file)
    
    return test_map
```

### 2. Core層テストの移行 [3時間]

#### 2.1 Rust単体テスト移行
```rust
// core/tests/test_black_scholes.rs
#[cfg(test)]
mod tests {
    use quantforge_core::models::black_scholes::*;
    use approx::assert_relative_eq;
    
    #[test]
    fn test_call_price_atm() {
        let params = BlackScholesParams {
            spot: 100.0,
            strike: 100.0,
            time: 1.0,
            rate: 0.05,
            volatility: 0.2,
        };
        let price = params.call_price();
        assert_relative_eq!(price, 10.450583572185565, epsilon = 1e-10);
    }
    
    #[test]
    fn test_put_call_parity() {
        let params = BlackScholesParams {
            spot: 100.0,
            strike: 100.0,
            time: 1.0,
            rate: 0.05,
            volatility: 0.2,
        };
        let call = params.call_price();
        let put = params.put_price();
        let parity = call - put;
        let expected = params.spot - params.strike * (-params.rate * params.time).exp();
        assert_relative_eq!(parity, expected, epsilon = 1e-10);
    }
}
```

#### 2.2 プロパティベーステスト
```rust
// core/tests/property_tests.rs
use proptest::prelude::*;
use quantforge_core::models::black_scholes::*;

proptest! {
    #[test]
    fn test_call_price_bounds(
        spot in 1.0..1000.0,
        strike in 1.0..1000.0,
        time in 0.01..10.0,
        rate in -0.1..0.3,
        vol in 0.01..2.0
    ) {
        let params = BlackScholesParams {
            spot, strike, time, rate, volatility: vol
        };
        let call = params.call_price();
        
        // Lower bound: max(S - K*exp(-r*t), 0)
        let intrinsic = (spot - strike * (-rate * time).exp()).max(0.0);
        assert!(call >= intrinsic - 1e-10);
        
        // Upper bound: S
        assert!(call <= spot + 1e-10);
    }
    
    #[test]
    fn test_greeks_consistency(
        spot in 50.0..150.0,
        strike in 50.0..150.0,
        time in 0.1..2.0,
        rate in 0.0..0.1,
        vol in 0.1..0.5
    ) {
        let params = BlackScholesParams {
            spot, strike, time, rate, volatility: vol
        };
        let greeks = params.calculate_greeks(true);
        
        // Delta should be between 0 and 1 for calls
        assert!(greeks.delta >= 0.0 && greeks.delta <= 1.0);
        
        // Gamma should be positive
        assert!(greeks.gamma >= 0.0);
    }
}
```

#### 2.3 パフォーマンステスト
```rust
// core/tests/performance.rs
use criterion::{black_box, Criterion};
use quantforge_core::models::black_scholes::*;

fn benchmark_single_price(c: &mut Criterion) {
    let params = BlackScholesParams {
        spot: 100.0,
        strike: 100.0,
        time: 1.0,
        rate: 0.05,
        volatility: 0.2,
    };
    
    c.bench_function("black_scholes_call_single", |b| {
        b.iter(|| {
            black_box(params.call_price())
        });
    });
}

fn benchmark_batch_processing(c: &mut Criterion) {
    let params_vec: Vec<BlackScholesParams> = (0..10000)
        .map(|i| BlackScholesParams {
            spot: 90.0 + (i as f64) * 0.002,
            strike: 100.0,
            time: 1.0,
            rate: 0.05,
            volatility: 0.2,
        })
        .collect();
    
    c.bench_function("black_scholes_batch_10k", |b| {
        b.iter(|| {
            black_box(call_price_batch(&params_vec))
        });
    });
}
```

### 3. Python層テストの移行 [3時間]

#### 3.1 単体テスト
```python
# bindings/python/tests/unit/test_api.py
import pytest
import numpy as np
from quantforge import models

class TestBlackScholesAPI:
    """Test Black-Scholes Python API."""
    
    def test_call_price_scalar(self):
        """Test scalar call price calculation."""
        price = models.call_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)
        assert abs(price - 10.450583572185565) < 1e-10
    
    def test_put_price_scalar(self):
        """Test scalar put price calculation."""
        price = models.put_price(100, 100, 1, 0.05, 0.2)
        assert isinstance(price, float)
        assert price > 0
    
    def test_greeks_return_type(self):
        """Test Greeks return dictionary."""
        greeks = models.greeks(100, 100, 1, 0.05, 0.2)
        assert isinstance(greeks, dict)
        assert all(k in greeks for k in ['delta', 'gamma', 'vega', 'theta', 'rho'])

class TestBatchProcessing:
    """Test batch processing functionality."""
    
    def test_call_price_batch_numpy(self):
        """Test batch processing with NumPy arrays."""
        spots = np.array([90, 100, 110], dtype=np.float64)
        prices = models.call_price_batch(spots, 100, 1, 0.05, 0.2)
        
        assert isinstance(prices, np.ndarray)
        assert len(prices) == 3
        assert all(prices > 0)
    
    def test_broadcasting(self):
        """Test NumPy-style broadcasting."""
        spots = np.linspace(80, 120, 100)
        strikes = 100.0  # Scalar
        
        prices = models.call_price_batch(spots, strikes, 1, 0.05, 0.2)
        assert len(prices) == 100
```

#### 3.2 統合テスト
```python
# bindings/python/tests/integration/test_models.py
import pytest
import numpy as np
from quantforge import models
import json
from pathlib import Path

class TestModelsIntegration:
    """Integration tests for all models."""
    
    @pytest.fixture
    def golden_data(self):
        """Load golden master data."""
        path = Path(__file__).parent.parent.parent / 'tests/golden/golden_values.json'
        with open(path) as f:
            return json.load(f)
    
    def test_black_scholes_consistency(self, golden_data):
        """Test Black-Scholes against golden master."""
        for case in golden_data['test_cases']:
            if case['category'] == 'black_scholes':
                inputs = case['inputs']
                expected = case['outputs']['call_price']
                
                actual = models.call_price(
                    inputs['s'], inputs['k'], inputs['t'],
                    inputs['r'], inputs['v']
                )
                
                assert abs(actual - expected) < golden_data['tolerance']
    
    def test_cross_model_consistency(self):
        """Test consistency between models."""
        # Black-Scholes with q=0 should equal Merton
        bs_price = models.call_price(100, 100, 1, 0.05, 0.2)
        merton_price = models.merton.call_price(100, 100, 1, 0.05, 0.0, 0.2)
        
        assert abs(bs_price - merton_price) < 1e-10
```

#### 3.3 パフォーマンステスト
```python
# bindings/python/tests/performance/test_benchmarks.py
import time
import numpy as np
import pytest
from quantforge import models

class TestPerformance:
    """Performance benchmarks."""
    
    def test_single_calculation_speed(self):
        """Test single calculation performance."""
        n_iterations = 10000
        
        start = time.perf_counter()
        for _ in range(n_iterations):
            _ = models.call_price(100, 100, 1, 0.05, 0.2)
        elapsed = time.perf_counter() - start
        
        per_call = elapsed / n_iterations * 1e9  # nanoseconds
        assert per_call < 1000  # Should be < 1 microsecond
    
    def test_batch_processing_speed(self):
        """Test batch processing performance."""
        sizes = [1000, 10000, 100000, 1000000]
        
        for size in sizes:
            spots = np.random.uniform(50, 150, size)
            
            start = time.perf_counter()
            _ = models.call_price_batch(spots, 100, 1, 0.05, 0.2)
            elapsed = time.perf_counter() - start
            
            throughput = size / elapsed
            print(f"Size {size}: {throughput:.0f} ops/sec")
            
            # Performance requirement: > 1M ops/sec
            assert throughput > 1_000_000
    
    def test_gil_release(self):
        """Test that GIL is properly released."""
        import threading
        import queue
        
        def worker(q, n):
            spots = np.random.uniform(50, 150, n)
            start = time.perf_counter()
            _ = models.call_price_batch(spots, 100, 1, 0.05, 0.2)
            q.put(time.perf_counter() - start)
        
        # Run in parallel
        q = queue.Queue()
        threads = []
        n = 100000
        n_threads = 4
        
        start = time.perf_counter()
        for _ in range(n_threads):
            t = threading.Thread(target=worker, args=(q, n))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        total_time = time.perf_counter() - start
        
        # Should be faster than sequential
        sequential_time = sum(q.get() for _ in range(n_threads))
        speedup = sequential_time / total_time
        
        assert speedup > 2.0  # At least 2x speedup with 4 threads
```

### 4. ベンチマークの統合 [2時間]

#### 4.1 Rustベンチマーク移行
```toml
# core/Cargo.toml
[[bench]]
name = "core_benchmarks"
harness = false

[dev-dependencies]
criterion = { version = "0.5", features = ["html_reports"] }
```

```rust
// core/benches/core_benchmarks.rs
use criterion::{criterion_group, criterion_main, Criterion, BenchmarkId};
use quantforge_core::models::black_scholes::*;

fn bench_single_models(c: &mut Criterion) {
    let mut group = c.benchmark_group("single_calculation");
    
    let params = BlackScholesParams {
        spot: 100.0, strike: 100.0, time: 1.0,
        rate: 0.05, volatility: 0.2
    };
    
    group.bench_function("black_scholes_call", |b| {
        b.iter(|| params.call_price())
    });
    
    group.bench_function("black_scholes_greeks", |b| {
        b.iter(|| params.calculate_greeks(true))
    });
    
    group.finish();
}

fn bench_batch_sizes(c: &mut Criterion) {
    let mut group = c.benchmark_group("batch_processing");
    
    for size in [100, 1000, 10000, 100000].iter() {
        let params: Vec<_> = (0..*size)
            .map(|i| BlackScholesParams {
                spot: 90.0 + (i as f64) * 0.0002,
                strike: 100.0,
                time: 1.0,
                rate: 0.05,
                volatility: 0.2,
            })
            .collect();
        
        group.bench_with_input(
            BenchmarkId::from_parameter(size),
            &params,
            |b, p| b.iter(|| call_price_batch(p))
        );
    }
    
    group.finish();
}

criterion_group!(benches, bench_single_models, bench_batch_sizes);
criterion_main!(benches);
```

#### 4.2 層別ベンチマーク構造の実装

##### 4.2.1 Core層ベンチマーク
```rust
// core/benches/algorithm_bench.rs
//! 純粋なアルゴリズム性能測定（PyO3依存なし）

use criterion::{black_box, criterion_group, criterion_main, Criterion};
use quantforge_core::models::{BlackScholesParams, Black76Params};

fn bench_pure_algorithms(c: &mut Criterion) {
    let mut group = c.benchmark_group("core_algorithms");
    
    // Black-Scholesアルゴリズム単体
    let bs_params = BlackScholesParams {
        spot: 100.0, strike: 100.0, time: 1.0,
        rate: 0.05, volatility: 0.2,
    };
    
    group.bench_function("black_scholes_call", |b| {
        b.iter(|| black_box(bs_params.call_price()))
    });
    
    // 並列処理効率測定
    let batch_params: Vec<_> = (0..100_000)
        .map(|i| BlackScholesParams {
            spot: 90.0 + (i as f64) * 0.0002,
            strike: 100.0, time: 1.0,
            rate: 0.05, volatility: 0.2,
        })
        .collect();
    
    group.bench_function("parallel_100k", |b| {
        b.iter(|| black_box(call_price_batch(&batch_params)))
    });
    
    group.finish();
}

criterion_group!(benches, bench_pure_algorithms);
criterion_main!(benches);
```

##### 4.2.2 Bindings層ベンチマーク
```python
# bindings/python/tests/benchmarks/ffi_overhead.py
"""FFI層特有のオーバーヘッド測定."""

import time
import numpy as np
import pytest
from quantforge import models

class FFIBenchmark:
    """FFI層のパフォーマンス測定."""
    
    def measure_ffi_call_overhead(self):
        """FFI呼び出しコストの測定."""
        # 単一呼び出しのオーバーヘッド
        iterations = 100_000
        
        start = time.perf_counter()
        for _ in range(iterations):
            models.call_price(100, 100, 1, 0.05, 0.2)
        ffi_time = time.perf_counter() - start
        
        return {
            'call_overhead_ns': (ffi_time / iterations) * 1e9,
            'calls_per_second': iterations / ffi_time
        }
    
    def measure_zero_copy_efficiency(self):
        """NumPy配列のゼロコピー検証."""
        sizes = [100, 1_000, 10_000, 100_000, 1_000_000]
        results = {}
        
        for size in sizes:
            # NumPy配列準備
            data = np.random.uniform(50, 150, size)
            
            # メモリコピーなしでFFI通過
            start = time.perf_counter()
            result = models.call_price_batch(
                spots=data, strikes=100.0, times=1.0,
                rates=0.05, sigmas=0.2
            )
            elapsed = time.perf_counter() - start
            
            results[f'size_{size}'] = {
                'time_ms': elapsed * 1000,
                'throughput_ops': size / elapsed,
                'overhead_per_element_ns': (elapsed / size) * 1e9
            }
        
        return results
```

##### 4.2.3 統合層ベンチマーク
```python
# tests/performance/integration_benchmark.py
"""エンドツーエンド統合ベンチマーク."""

import json
import time
from pathlib import Path
import numpy as np
from quantforge import models

# 既存資産の移動と活用
from .baseline_manager import BaselineManager
from .performance_guard import PerformanceGuard

class IntegrationBenchmark:
    """統合層のパフォーマンス検証."""
    
    def __init__(self):
        # 既存の管理システムを活用
        self.baseline = BaselineManager()
        self.guard = PerformanceGuard()
        self.results_dir = Path('benchmark_results/integration')
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_full_workflow_benchmark(self):
        """実際のユースケースでの性能測定."""
        results = {
            'version': '2.0.0',
            'layer': 'integration',
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'benchmarks': {}
        }
        
        # ワークフロー1: オプション価格計算パイプライン
        workflow_start = time.perf_counter()
        
        # 市場データ準備
        spots = np.random.uniform(90, 110, 10_000)
        strikes = np.linspace(80, 120, 41)
        
        # 価格計算
        for spot in spots[:100]:  # サンプリング
            prices = models.call_price_batch(
                spots=spot, strikes=strikes,
                times=1.0, rates=0.05, sigmas=0.2
            )
            
            # Greeks計算
            greeks = models.greeks_batch(
                spots=spot, strikes=strikes,
                times=1.0, rates=0.05, sigmas=0.2
            )
        
        workflow_time = time.perf_counter() - workflow_start
        
        results['benchmarks']['full_workflow'] = {
            'time_seconds': workflow_time,
            'options_calculated': 100 * 41,
            'throughput': (100 * 41) / workflow_time
        }
        
        # 新形式でのベンチマーク結果保存
        self._save_hierarchical_results(results)
        
        # 既存のguardシステムで回帰検出
        return self.guard.detect_regression(results)
    
    def _save_hierarchical_results(self, results):
        """階層的な新形式での結果保存."""
        # 最新結果
        latest_path = self.results_dir / 'latest.json'
        with open(latest_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        # 履歴保存
        history_dir = self.results_dir / 'history' / 
            time.strftime('%Y-%m-%d')
        history_dir.mkdir(parents=True, exist_ok=True)
        
        run_id = time.strftime('run_%H%M%S.json')
        with open(history_dir / run_id, 'w') as f:
            json.dump(results, f, indent=2)
```

##### 4.2.4 ベンチマーク記録形式の更新
```python
# tests/performance/benchmark_schema.py
"""新しい階層的ベンチマーク記録形式の定義."""

from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import json
from pathlib import Path

@dataclass
class BenchmarkEnvironment:
    """ベンチマーク環境情報."""
    system: Dict[str, Any]  # プラットフォーム、CPU、メモリ
    build: Dict[str, Any]   # Rust、最適化フラグ、LTO設定
    runtime: Dict[str, Any] # Python、PyO3、NumPyバージョン

@dataclass
class BenchmarkResult:
    """ベンチマーク結果（新形式）."""
    version: str = "2.0.0"
    layer: str = ""  # core | bindings | integration
    timestamp: str = ""
    run_id: str = ""
    environment: BenchmarkEnvironment = None
    benchmarks: Dict[str, Any] = None
    comparisons: Dict[str, Any] = None
    quality_metrics: Dict[str, Any] = None
    
    def save(self, base_dir: Path):
        """層別ディレクトリ構造での保存."""
        layer_dir = base_dir / self.layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        
        # 最新結果
        with open(layer_dir / 'latest.json', 'w') as f:
            json.dump(asdict(self), f, indent=2)
        
        # 履歴
        history_dir = layer_dir / 'history' / 
            self.timestamp[:10]  # YYYY-MM-DD
        history_dir.mkdir(parents=True, exist_ok=True)
        
        with open(history_dir / f'{self.run_id}.json', 'w') as f:
            json.dump(asdict(self), f, indent=2)
```

### 5. E2Eテストの作成 [2時間]

#### 5.1 エンドツーエンドシナリオ
```python
# tests/e2e/test_full_workflow.py
"""End-to-end tests for complete workflows."""

import pytest
import numpy as np
from quantforge import models
import tempfile
import json

class TestE2EWorkflows:
    """Test complete user workflows."""
    
    def test_option_pricing_workflow(self):
        """Test complete option pricing workflow."""
        # 1. Single pricing
        spot = 100.0
        strike = 105.0
        time = 0.25
        rate = 0.05
        vol = 0.2
        
        call_price = models.call_price(spot, strike, time, rate, vol)
        put_price = models.put_price(spot, strike, time, rate, vol)
        
        # 2. Greeks calculation
        greeks = models.greeks(spot, strike, time, rate, vol)
        
        # 3. Implied volatility
        iv = models.implied_volatility(
            call_price, spot, strike, time, rate, is_call=True
        )
        
        assert abs(iv - vol) < 1e-6
        
        # 4. Batch processing
        spots = np.linspace(90, 110, 21)
        prices = models.call_price_batch(spots, strike, time, rate, vol)
        
        assert len(prices) == 21
        assert all(p >= 0 for p in prices)
    
    def test_cross_model_workflow(self):
        """Test workflow across different models."""
        params = {
            's': 100, 'k': 100, 't': 1, 'r': 0.05, 'sigma': 0.2
        }
        
        # Compare different models
        bs_call = models.call_price(**params)
        b76_call = models.black76.call_price(f=100, **{k: v for k, v in params.items() if k != 's'})
        merton_call = models.merton.call_price(**params, q=0.0)
        
        # Should be close but not identical
        assert abs(bs_call - merton_call) < 1e-10
    
    def test_data_pipeline(self):
        """Test data processing pipeline."""
        # Load market data
        market_data = {
            'spots': np.random.uniform(90, 110, 1000),
            'strikes': np.random.uniform(95, 105, 1000),
            'times': np.random.uniform(0.1, 2.0, 1000),
            'rates': 0.05,
            'vols': np.random.uniform(0.1, 0.4, 1000)
        }
        
        # Calculate prices
        prices = models.call_price_batch(**market_data)
        
        # Calculate Greeks
        greeks = models.greeks_batch(**market_data)
        
        # Validate results
        assert len(prices) == 1000
        assert all(0 <= greeks['delta'][i] <= 1 for i in range(1000))
```

### 6. CI/CDパイプライン更新 [2時間]

#### 6.1 GitHub Actions ワークフロー更新
```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  core-tests:
    name: Core Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          components: rustfmt, clippy
      
      - name: Cache cargo
        uses: actions/cache@v3
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            core/target
          key: ${{ runner.os }}-cargo-core-${{ hashFiles('**/Cargo.lock') }}
      
      - name: Build Core
        run: cargo build --release
        working-directory: core
      
      - name: Test Core
        run: cargo test --all
        working-directory: core
      
      - name: Clippy
        run: cargo clippy -- -D warnings
        working-directory: core
      
      - name: Format Check
        run: cargo fmt -- --check
        working-directory: core

  python-tests:
    name: Python Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12', '3.13']
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install maturin pytest numpy
      
      - name: Build Python bindings
        run: maturin develop --release
        working-directory: bindings/python
      
      - name: Run Python tests
        run: pytest tests/ -v
        working-directory: bindings/python
      
      - name: Type checking
        run: |
          pip install mypy
          mypy quantforge/
        working-directory: bindings/python

  integration-tests:
    name: Integration Tests
    needs: [core-tests, python-tests]
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Full Build
        run: |
          cargo build --workspace --release
          cd bindings/python && maturin build --release
      
      - name: Integration Tests
        run: pytest tests/integration/ -v

  benchmarks:
    name: Benchmarks
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      
      - name: Run Core Benchmarks
        run: |
          cargo bench --all | tee benchmark_results.txt
        working-directory: core
      
      - name: Run Performance Guard
        run: |
          pip install uv
          uv sync
          uv run python benchmarks/performance_guard.py
      
      - name: Check for Regression
        run: |
          uv run python benchmarks/baseline_manager.py --check-regression
      
      - name: Upload Benchmark Results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: core/benchmark_results.txt
```

#### 6.2 ビルドワークフロー更新
```yaml
# .github/workflows/build.yml
name: Build and Release

on:
  release:
    types: [created]

jobs:
  build-wheels:
    name: Build wheels on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          override: true
      
      - name: Build wheels
        run: |
          pip install maturin
          cd bindings/python
          maturin build --release --strip
      
      - name: Upload wheels
        uses: actions/upload-artifact@v3
        with:
          name: wheels
          path: bindings/python/target/wheels/
```

#### 6.3 ローカル検証スクリプト
```bash
#!/bin/bash
# scripts/validate_ci.sh

echo "=== Validating CI/CD Configuration ==="

# Validate YAML syntax
for workflow in .github/workflows/*.yml; do
    echo "Checking $workflow..."
    python -c "import yaml; yaml.safe_load(open('$workflow'))" || exit 1
done

# Test workflow locally with act
if command -v act &> /dev/null; then
    echo "Running workflows locally with act..."
    act -n  # Dry run
else
    echo "Install 'act' to test workflows locally: https://github.com/nektos/act"
fi

echo "=== CI/CD Validation Complete ==="
```

### 7. テスト実行とレポート [1時間]

#### 6.1 統合テストランナー
```bash
#!/bin/bash
# scripts/run_all_tests.sh

echo "=== Running Core Tests ==="
cd core
cargo test --all
cargo test --all -- --ignored  # Run slow tests
cd ..

echo "=== Running Python Tests ==="
cd bindings/python
pytest tests/ -v --cov=quantforge --cov-report=html
cd ..

echo "=== Running E2E Tests ==="
pytest tests/e2e/ -v

echo "=== Running Benchmarks ==="
cd core
cargo bench
cd ..

cd bindings/python
python -m benchmarks.suite
cd ..

echo "=== Generating Report ==="
python scripts/generate_test_report.py
```

#### 6.2 テストレポート生成
```python
# scripts/generate_test_report.py
"""Generate comprehensive test report."""

import json
from pathlib import Path
from datetime import datetime

def generate_report():
    report = {
        'timestamp': datetime.now().isoformat(),
        'core': load_rust_results(),
        'python': load_python_results(),
        'e2e': load_e2e_results(),
        'coverage': load_coverage_data(),
        'benchmarks': load_benchmark_results()
    }
    
    # Generate markdown report
    with open('TEST_REPORT.md', 'w') as f:
        f.write(format_markdown_report(report))
    
    # Generate JSON report
    with open('test_results.json', 'w') as f:
        json.dump(report, f, indent=2)

def format_markdown_report(report):
    """Format report as markdown."""
    return f"""
# Test Report - {report['timestamp']}

## Summary
- Core Tests: {report['core']['passed']}/{report['core']['total']}
- Python Tests: {report['python']['passed']}/{report['python']['total']}
- E2E Tests: {report['e2e']['passed']}/{report['e2e']['total']}
- Coverage: {report['coverage']['overall']:.1f}%

## Performance
- Single Call: {report['benchmarks']['single_call']:.0f} ns
- Batch 1M: {report['benchmarks']['batch_1m']:.2f} ms
- Throughput: {report['benchmarks']['throughput']:.0f} ops/sec
"""
```

## 完了条件

### 必須チェックリスト
- [x] 全テストの移行完了
- [x] 各層の責任範囲明確化
- [x] テストカバレッジ90%以上
- [x] ベンチマーク統合完了
- [x] E2Eテスト作成
- [x] CI/CDパイプライン更新完了
- [x] GitHub Actions動作確認

### 品質基準
- [x] Core層テスト: 全合格
- [x] Python層テスト: 全合格 (American model含む)
- [x] E2Eテスト: 全合格
- [x] パフォーマンス: ベースライン維持

## 成果物

### テスト構造
```
core/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── property/
├── benches/

bindings/python/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── benchmarks/

tests/
├── e2e/
└── golden/
```

### レポート
- `TEST_REPORT.md`: 統合テストレポート
- `coverage/`: カバレッジレポート
- `criterion/`: ベンチマークレポート

## リスクと対策

| リスク | 対策 |
|--------|------|
| テスト漏れ | カバレッジ測定で検出 |
| 性能劣化 | 継続的ベンチマーク |
| 環境依存 | CI/CDで複数環境テスト |

## Phase 4への引き継ぎ

### 提供物
1. 完全なテストスイート
2. ベンチマーク結果
3. カバレッジレポート

### 確認事項
- 全テスト合格
- パフォーマンス基準達成
- ドキュメント完備
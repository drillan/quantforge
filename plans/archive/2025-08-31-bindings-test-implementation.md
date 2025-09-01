# 専用Bindingsテスト実装計画

## 🚨 現状の問題

### 深刻なテストギャップ
- **Bindingsテスト**: 0件（専用テストディレクトリなし）
- **型変換テスト**: 0件（ArrayLike、BroadcastIterator未テスト）
- **FFI境界テスト**: 0件（Rust-Python間のエラーハンドリング未検証）
- **メモリ安全性**: 未検証（参照カウント、GIL管理）

### リスク評価
| リスクレベル | 項目 | 影響 |
|------------|------|------|
| **Critical** | 型変換の正確性 | 誤った計算結果 |
| **Critical** | メモリリーク | プロダクション環境でのクラッシュ |
| **High** | Broadcasting誤動作 | NumPy非互換 |
| **High** | エラー変換失敗 | 不適切なエラーメッセージ |
| **Medium** | パフォーマンス劣化 | FFIオーバーヘッド増大 |

## 🎯 テスト戦略

### 3層テストアーキテクチャ

```
┌─────────────────────────────────────┐
│     E2E Tests (Python)              │ <- ユーザー視点の統合テスト
├─────────────────────────────────────┤
│   Binding Layer Tests               │ <- FFI境界の専用テスト
│  ┌─────────────┬─────────────┐     │
│  │ Python側    │  Rust側      │     │
│  │ (pytest)    │ (#[test])    │     │
│  └─────────────┴─────────────┘     │
├─────────────────────────────────────┤
│     Core Tests (Rust)               │ <- 純粋なビジネスロジック
└─────────────────────────────────────┘
```

## 📝 実装計画

### Phase 1: テスト基盤構築 [4時間]

#### 1.1 ディレクトリ構造作成
```bash
bindings/python/
├── tests/                      # Python側テスト
│   ├── __init__.py
│   ├── conftest.py            # pytest設定
│   ├── test_type_conversion.py
│   ├── test_broadcasting.py
│   ├── test_error_handling.py
│   ├── test_memory_safety.py
│   ├── test_performance.py
│   └── fixtures/              # テストデータ
├── src/
│   ├── tests/                 # Rust側単体テスト
│   │   ├── mod.rs
│   │   ├── test_converters.rs
│   │   └── test_ffi_safety.rs
│   └── benches/               # ベンチマーク
│       └── ffi_overhead.rs
```

#### 1.2 テストユーティリティ作成
```python
# bindings/python/tests/conftest.py
import pytest
import numpy as np
import gc
import tracemalloc
from typing import Any, Callable
import quantforge

@pytest.fixture
def memory_tracker():
    """メモリリーク検出フィクスチャ"""
    tracemalloc.start()
    gc.collect()
    snapshot_before = tracemalloc.take_snapshot()
    
    yield
    
    gc.collect()
    snapshot_after = tracemalloc.take_snapshot()
    top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    
    # メモリリークチェック
    for stat in top_stats[:10]:
        if stat.size_diff > 1024 * 1024:  # 1MB以上の増加
            pytest.fail(f"Memory leak detected: {stat}")

@pytest.fixture
def gil_checker():
    """GIL解放確認フィクスチャ"""
    import threading
    import time
    
    class GILChecker:
        def __init__(self):
            self.gil_released = False
            
        def check_gil_release(self, func: Callable, *args, **kwargs):
            """関数実行中にGILが解放されるか確認"""
            def worker():
                # GILが解放されていればこのスレッドが実行される
                self.gil_released = True
            
            thread = threading.Thread(target=worker)
            thread.start()
            
            # 計算実行
            result = func(*args, **kwargs)
            
            thread.join(timeout=0.1)
            return result, self.gil_released
    
    return GILChecker()

@pytest.fixture
def test_arrays():
    """標準テスト配列セット"""
    return {
        'small': np.random.randn(10),
        'medium': np.random.randn(1000),
        'large': np.random.randn(1_000_000),
        'empty': np.array([]),
        'scalar': np.array([42.0]),
        'nan': np.array([np.nan, 1.0, 2.0]),
        'inf': np.array([np.inf, -np.inf, 1.0]),
        'non_contiguous': np.random.randn(10, 10)[::2, ::2].flatten(),
    }
```

### Phase 2: 型変換テスト実装 [6時間]

#### 2.1 ArrayLike変換テスト
```python
# bindings/python/tests/test_type_conversion.py
import pytest
import numpy as np
from quantforge import black_scholes

class TestArrayLikeConversion:
    """ArrayLike型変換の包括的テスト"""
    
    def test_scalar_input(self):
        """スカラー入力の処理"""
        # 単一のfloat
        result = black_scholes.call_price_batch(
            100.0, 100.0, 1.0, 0.05, 0.2
        )
        assert isinstance(result, np.ndarray)
        assert result.shape == (1,) or result.shape == ()
        
    def test_list_input(self):
        """Pythonリスト入力"""
        spots = [100.0, 105.0, 110.0]
        result = black_scholes.call_price_batch(
            spots, 100.0, 1.0, 0.05, 0.2
        )
        assert len(result) == 3
        
    def test_numpy_array_input(self):
        """NumPy配列入力"""
        spots = np.array([100.0, 105.0, 110.0])
        result = black_scholes.call_price_batch(
            spots, 100.0, 1.0, 0.05, 0.2
        )
        assert len(result) == 3
        
    def test_mixed_types(self):
        """混合型入力（int、float、array）"""
        result = black_scholes.call_price_batch(
            100,  # int
            100.0,  # float
            [1.0, 2.0],  # list
            np.array([0.05]),  # numpy
            0.2  # float
        )
        assert len(result) == 2
        
    def test_non_contiguous_array(self):
        """非連続配列の処理"""
        # スライスで非連続配列を作成
        arr = np.arange(20).reshape(4, 5)[::2, ::2].flatten()
        assert not arr.flags['C_CONTIGUOUS']
        
        # 非連続配列でも動作すること
        result = black_scholes.call_price_batch(
            arr, 100.0, 1.0, 0.05, 0.2
        )
        assert len(result) == len(arr)
        
    def test_empty_array(self):
        """空配列の処理"""
        empty = np.array([])
        result = black_scholes.call_price_batch(
            empty, 100.0, 1.0, 0.05, 0.2
        )
        assert len(result) == 0
        
    def test_single_element_array(self):
        """単一要素配列"""
        single = np.array([100.0])
        result = black_scholes.call_price_batch(
            single, 100.0, 1.0, 0.05, 0.2
        )
        assert len(result) == 1
```

#### 2.2 Broadcasting動作テスト
```python
# bindings/python/tests/test_broadcasting.py
import pytest
import numpy as np
from quantforge import black_scholes

class TestBroadcasting:
    """NumPy互換のbroadcasting動作テスト"""
    
    def test_scalar_broadcast(self):
        """スカラーのブロードキャスト"""
        spots = np.array([100, 105, 110])
        # スカラーが3要素に拡張される
        result = black_scholes.call_price_batch(
            spots, 100.0, 1.0, 0.05, 0.2  # 他は全てスカラー
        )
        assert len(result) == 3
        
    def test_array_broadcast(self):
        """配列間のブロードキャスト"""
        spots = np.array([100, 105, 110])
        strikes = np.array([95, 100, 105])
        # 両方とも3要素
        result = black_scholes.call_price_batch(
            spots, strikes, 1.0, 0.05, 0.2
        )
        assert len(result) == 3
        
    def test_shape_mismatch_error(self):
        """形状不一致エラー"""
        spots = np.array([100, 105])  # 2要素
        strikes = np.array([95, 100, 105])  # 3要素
        
        with pytest.raises(ValueError, match="Shape mismatch|broadcast"):
            black_scholes.call_price_batch(
                spots, strikes, 1.0, 0.05, 0.2
            )
            
    def test_complex_broadcast(self):
        """複雑なブロードキャストパターン"""
        # 1要素配列は任意のサイズにブロードキャスト可能
        spots = np.array([100])  # 1要素
        strikes = np.array([95, 100, 105])  # 3要素
        
        result = black_scholes.call_price_batch(
            spots, strikes, 1.0, 0.05, 0.2
        )
        assert len(result) == 3
        
    def test_broadcast_with_empty(self):
        """空配列とのブロードキャスト"""
        empty = np.array([])
        spots = np.array([100, 105, 110])
        
        result = black_scholes.call_price_batch(
            empty, spots, 1.0, 0.05, 0.2
        )
        assert len(result) == 0  # 空配列が結果を支配
```

### Phase 3: エラーハンドリングテスト [4時間]

#### 3.1 Rust側エラー変換テスト
```rust
// bindings/python/src/tests/test_converters.rs
#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::prelude::*;
    use numpy::PyArray1;
    
    #[test]
    fn test_error_conversion() {
        // QuantForgeError -> PyErr変換テスト
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            // InvalidInput -> PyValueError
            let err = QuantForgeError::InvalidInput("test error".to_string());
            let py_err: PyErr = err.into();
            assert!(py_err.is_instance_of::<pyo3::exceptions::PyValueError>(py));
            
            // NumericalError -> PyValueError
            let err = QuantForgeError::NumericalError("convergence failed".to_string());
            let py_err: PyErr = err.into();
            assert!(py_err.is_instance_of::<pyo3::exceptions::PyValueError>(py));
        });
    }
    
    #[test]
    fn test_array_validation() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            // NaN検証
            let arr = PyArray1::from_vec_bound(py, vec![1.0, f64::NAN, 3.0]);
            let result = validate_array(arr.readonly());
            assert!(result.is_err());
            assert!(result.unwrap_err().to_string().contains("NaN"));
            
            // Inf検証
            let arr = PyArray1::from_vec_bound(py, vec![1.0, f64::INFINITY, 3.0]);
            let result = validate_array(arr.readonly());
            assert!(result.is_err());
            assert!(result.unwrap_err().to_string().contains("infinite"));
        });
    }
}
```

#### 3.2 Python側エラーハンドリングテスト
```python
# bindings/python/tests/test_error_handling.py
import pytest
import numpy as np
from quantforge import black_scholes

class TestErrorHandling:
    """エラーハンドリングとバリデーション"""
    
    def test_negative_spot_price(self):
        """負のスポット価格"""
        with pytest.raises(ValueError, match="spot.*positive|s must be positive"):
            black_scholes.call_price(-100, 100, 1, 0.05, 0.2)
            
    def test_negative_strike(self):
        """負の権利行使価格"""
        with pytest.raises(ValueError, match="strike.*positive|k must be positive"):
            black_scholes.call_price(100, -100, 1, 0.05, 0.2)
            
    def test_negative_time(self):
        """負の満期時間"""
        with pytest.raises(ValueError, match="time.*positive|t must be positive"):
            black_scholes.call_price(100, 100, -1, 0.05, 0.2)
            
    def test_negative_volatility(self):
        """負のボラティリティ"""
        with pytest.raises(ValueError, match="volatility.*positive|sigma must be positive"):
            black_scholes.call_price(100, 100, 1, 0.05, -0.2)
            
    def test_nan_input(self):
        """NaN入力の処理"""
        with pytest.raises(ValueError, match="NaN|invalid"):
            black_scholes.call_price(np.nan, 100, 1, 0.05, 0.2)
            
    def test_inf_input(self):
        """無限大入力の処理"""
        with pytest.raises(ValueError, match="infinite|invalid"):
            black_scholes.call_price(np.inf, 100, 1, 0.05, 0.2)
            
    def test_batch_partial_invalid(self):
        """バッチ処理での部分的な無効値"""
        spots = np.array([100, np.nan, 110])
        with pytest.raises(ValueError, match="NaN|invalid"):
            black_scholes.call_price_batch(spots, 100, 1, 0.05, 0.2)
            
    def test_type_error(self):
        """型エラー"""
        with pytest.raises(TypeError):
            black_scholes.call_price("invalid", 100, 1, 0.05, 0.2)
            
    def test_implied_volatility_convergence(self):
        """IV計算の収束エラー"""
        # 不可能な価格でのIV計算
        with pytest.raises(ValueError, match="converge|bounds"):
            black_scholes.implied_volatility(
                0.001,  # 極端に低い価格
                100, 100, 1, 0.05, True
            )
```

### Phase 4: メモリ安全性テスト [6時間]

#### 4.1 参照カウントテスト
```python
# bindings/python/tests/test_memory_safety.py
import pytest
import numpy as np
import gc
import sys
import weakref
from quantforge import black_scholes

class TestMemorySafety:
    """メモリ安全性とリーク検出"""
    
    def test_reference_counting(self):
        """参照カウントの正確性"""
        # 配列を作成
        arr = np.array([100.0, 105.0, 110.0])
        initial_refcount = sys.getrefcount(arr)
        
        # Bindingsを通して処理
        result = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
        
        # 参照カウントが増えていないこと
        assert sys.getrefcount(arr) == initial_refcount
        
    def test_memory_leak_detection(self, memory_tracker):
        """メモリリーク検出"""
        # 大量のデータで繰り返し実行
        for _ in range(100):
            arr = np.random.randn(10000)
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            
        # memory_trackerフィクスチャが自動的にリークをチェック
        
    def test_gc_interaction(self):
        """ガベージコレクションとの相互作用"""
        # 弱参照を作成
        arr = np.array([100.0])
        weak_ref = weakref.ref(arr)
        
        # 処理実行
        result = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
        
        # 元の配列を削除
        del arr
        gc.collect()
        
        # 結果は独立して存在
        assert result is not None
        assert len(result) == 1
        
        # 元の配列はGC可能
        assert weak_ref() is None
        
    def test_zero_copy_verification(self):
        """ゼロコピー最適化の検証"""
        # 大きな配列でメモリ使用量を監視
        import tracemalloc
        
        arr = np.random.randn(1_000_000)
        
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        # ゼロコピーであればメモリ増加は最小限
        _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
        
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # メモリ増加が入力サイズの2倍未満（ゼロコピーの証明）
        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
        assert total_increase < arr.nbytes * 2
        
    def test_thread_safety(self):
        """スレッドセーフティ"""
        import threading
        import queue
        
        errors = queue.Queue()
        
        def worker():
            try:
                for _ in range(100):
                    arr = np.random.randn(100)
                    _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            except Exception as e:
                errors.put(e)
        
        # 複数スレッドで同時実行
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        # エラーがないこと
        assert errors.empty()
```

#### 4.2 GIL管理テスト
```python
# bindings/python/tests/test_gil_management.py
import pytest
import numpy as np
import threading
import time
from quantforge import black_scholes

class TestGILManagement:
    """GIL（Global Interpreter Lock）管理"""
    
    def test_gil_release_during_computation(self, gil_checker):
        """計算中のGIL解放確認"""
        arr = np.random.randn(1_000_000)
        
        result, gil_released = gil_checker.check_gil_release(
            black_scholes.call_price_batch,
            arr, 100, 1, 0.05, 0.2
        )
        
        assert gil_released, "GIL was not released during computation"
        
    def test_parallel_execution(self):
        """並列実行の可能性"""
        import concurrent.futures
        import time
        
        def compute_batch():
            arr = np.random.randn(100_000)
            start = time.perf_counter()
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            return time.perf_counter() - start
        
        # シングルスレッド実行
        single_times = [compute_batch() for _ in range(4)]
        single_total = sum(single_times)
        
        # マルチスレッド実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            start = time.perf_counter()
            list(executor.map(lambda _: compute_batch(), range(4)))
            multi_total = time.perf_counter() - start
        
        # GILが解放されていれば並列実行が速い
        speedup = single_total / multi_total
        assert speedup > 1.5, f"Expected speedup > 1.5, got {speedup:.2f}"
```

### Phase 5: パフォーマンステスト [4時間]

#### 5.1 FFIオーバーヘッド測定
```python
# bindings/python/tests/test_performance.py
import pytest
import numpy as np
import time
from quantforge import black_scholes

class TestFFIPerformance:
    """FFI（Foreign Function Interface）パフォーマンス"""
    
    @pytest.mark.benchmark
    def test_ffi_overhead_single_call(self, benchmark):
        """単一呼び出しのオーバーヘッド"""
        result = benchmark(
            black_scholes.call_price,
            100, 100, 1, 0.05, 0.2
        )
        assert result > 0
        
    @pytest.mark.benchmark
    def test_ffi_overhead_batch(self, benchmark):
        """バッチ処理のオーバーヘッド"""
        arr = np.random.uniform(80, 120, 1000)
        
        result = benchmark(
            black_scholes.call_price_batch,
            arr, 100, 1, 0.05, 0.2
        )
        assert len(result) == 1000
        
    def test_array_size_scaling(self):
        """配列サイズとパフォーマンスのスケーリング"""
        sizes = [10, 100, 1000, 10000, 100000]
        times = []
        
        for size in sizes:
            arr = np.random.uniform(80, 120, size)
            
            start = time.perf_counter()
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            elapsed = time.perf_counter() - start
            
            times.append(elapsed)
            
        # 線形スケーリングの確認（O(n)）
        for i in range(1, len(sizes)):
            ratio = times[i] / times[0]
            size_ratio = sizes[i] / sizes[0]
            # 2倍の許容範囲内で線形
            assert ratio < size_ratio * 2
            
    def test_memory_bandwidth(self):
        """メモリ帯域幅の測定"""
        size = 10_000_000  # 10M要素（80MB）
        arr = np.random.randn(size)
        
        start = time.perf_counter()
        result = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
        elapsed = time.perf_counter() - start
        
        # スループット計算（GB/s）
        bytes_processed = size * 8 * 2  # 入力+出力
        throughput_gbps = (bytes_processed / elapsed) / 1e9
        
        print(f"Memory throughput: {throughput_gbps:.2f} GB/s")
        assert throughput_gbps > 1.0  # 最低1GB/s
```

#### 5.2 最適化検証
```rust
// bindings/python/src/benches/ffi_overhead.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};
use pyo3::prelude::*;
use numpy::PyArray1;

fn benchmark_array_conversion(c: &mut Criterion) {
    pyo3::prepare_freethreaded_python();
    
    c.bench_function("array_to_slice_1k", |b| {
        Python::with_gil(|py| {
            let arr = PyArray1::<f64>::zeros_bound(py, 1000, false);
            b.iter(|| {
                let slice = black_box(arr.readonly().as_slice().unwrap());
                black_box(slice.len());
            });
        });
    });
    
    c.bench_function("broadcast_iterator_1k", |b| {
        Python::with_gil(|py| {
            let arr1 = PyArray1::<f64>::zeros_bound(py, 1000, false);
            let arr2 = PyArray1::<f64>::zeros_bound(py, 1, false);
            
            b.iter(|| {
                let inputs = vec![
                    &ArrayLike::Array(arr1.readonly()),
                    &ArrayLike::Array(arr2.readonly()),
                ];
                let iter = BroadcastIterator::new(inputs).unwrap();
                black_box(iter.len());
            });
        });
    });
}

criterion_group!(benches, benchmark_array_conversion);
criterion_main!(benches);
```

### Phase 6: 統合テストスイート [3時間]

#### 6.1 End-to-Endテスト
```python
# bindings/python/tests/test_integration.py
import pytest
import numpy as np
from quantforge import black_scholes, black76, merton

class TestBindingsIntegration:
    """Bindings層の統合テスト"""
    
    def test_all_models_consistency(self):
        """全モデルでの一貫性"""
        # 同じパラメータで全モデルをテスト
        s, k, t, r, sigma = 100, 100, 1, 0.05, 0.2
        
        # Black-Scholes
        bs_price = black_scholes.call_price(s, k, t, r, sigma)
        
        # Merton (q=0でBlack-Scholesと一致)
        merton_price = merton.call_price(s, k, t, r, 0, sigma)
        
        assert np.isclose(bs_price, merton_price, rtol=1e-10)
        
    def test_cross_validation_with_numpy(self):
        """NumPyでの再計算と比較"""
        from scipy.stats import norm
        
        s, k, t, r, sigma = 100, 100, 1, 0.05, 0.2
        
        # NumPyで計算
        d1 = (np.log(s/k) + (r + 0.5*sigma**2)*t) / (sigma*np.sqrt(t))
        d2 = d1 - sigma*np.sqrt(t)
        numpy_price = s*norm.cdf(d1) - k*np.exp(-r*t)*norm.cdf(d2)
        
        # Bindingsで計算
        binding_price = black_scholes.call_price(s, k, t, r, sigma)
        
        assert np.isclose(numpy_price, binding_price, rtol=1e-10)
        
    def test_stress_test(self):
        """ストレステスト（大量データ、境界値）"""
        # 極端な値でのテスト
        extreme_cases = [
            (1e-10, 100, 1, 0.05, 0.2),  # 極小スポット
            (1e10, 100, 1, 0.05, 0.2),   # 極大スポット
            (100, 100, 1e-10, 0.05, 0.2), # 極小時間
            (100, 100, 100, 0.05, 0.2),   # 極大時間
            (100, 100, 1, -0.5, 0.2),     # 負の金利
            (100, 100, 1, 0.05, 1e-10),   # 極小ボラティリティ
            (100, 100, 1, 0.05, 10),      # 極大ボラティリティ
        ]
        
        for params in extreme_cases:
            try:
                price = black_scholes.call_price(*params)
                # 価格は非負
                assert price >= 0
                # 価格は有限
                assert np.isfinite(price)
            except ValueError:
                # バリデーションエラーは許容
                pass
```

#### 6.2 回帰テスト
```python
# bindings/python/tests/test_regression.py
import pytest
import numpy as np
import json
from pathlib import Path
from quantforge import black_scholes

class TestRegression:
    """回帰テスト（過去のバグ再発防止）"""
    
    @pytest.fixture
    def golden_values(self):
        """ゴールデンマスター値"""
        return {
            "bs_call_atm": 10.450583572185565,
            "bs_put_atm": 5.573526022256971,
            "bs_call_itm": 15.851368584517094,
            "bs_call_otm": 5.876622794074693,
        }
    
    def test_golden_master_values(self, golden_values):
        """ゴールデンマスター値との比較"""
        # ATM Call
        price = black_scholes.call_price(100, 100, 1, 0.05, 0.2)
        assert np.isclose(price, golden_values["bs_call_atm"], rtol=1e-10)
        
        # ATM Put
        price = black_scholes.put_price(100, 100, 1, 0.05, 0.2)
        assert np.isclose(price, golden_values["bs_put_atm"], rtol=1e-10)
        
    def test_known_issues(self):
        """既知の問題の再発防止"""
        # Issue #1: 空配列でのSegmentation Fault
        empty = np.array([])
        result = black_scholes.call_price_batch(empty, 100, 1, 0.05, 0.2)
        assert len(result) == 0
        
        # Issue #2: NaN伝播
        arr_with_nan = np.array([100, np.nan, 110])
        with pytest.raises(ValueError):
            black_scholes.call_price_batch(arr_with_nan, 100, 1, 0.05, 0.2)
            
        # Issue #3: メモリリーク（大量の小バッチ）
        import tracemalloc
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        for _ in range(10000):
            arr = np.array([100.0])
            _ = black_scholes.call_price_batch(arr, 100, 1, 0.05, 0.2)
            
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        # メモリ増加が1MB未満
        total_increase = sum(stat.size_diff for stat in stats if stat.size_diff > 0)
        assert total_increase < 1024 * 1024
```

### Phase 7: CI/CD統合 [2時間]

#### 7.1 テスト実行スクリプト
```bash
#!/bin/bash
# scripts/test_bindings.sh

set -e

echo "=== Bindings Layer Test Suite ==="

# Rust側テスト
echo "Running Rust tests..."
cd bindings/python
cargo test --lib --features test

# Python側テスト
echo "Running Python tests..."
maturin develop --release
pytest tests/ -v --tb=short

# パフォーマンステスト
echo "Running performance tests..."
pytest tests/test_performance.py -v --benchmark-only

# メモリプロファイリング
echo "Running memory profiling..."
python -m pytest tests/test_memory_safety.py -v --memprof

# カバレッジレポート
echo "Generating coverage report..."
pytest tests/ --cov=quantforge --cov-report=html

echo "=== All tests passed! ==="
```

#### 7.2 GitHub Actions設定
```yaml
# .github/workflows/bindings_tests.yml
name: Bindings Layer Tests

on:
  push:
    paths:
      - 'bindings/**'
      - 'core/**'
  pull_request:
    paths:
      - 'bindings/**'
      - 'core/**'

jobs:
  test-bindings:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.12', '3.13']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          override: true
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          pip install uv maturin
          uv sync --group dev
      
      - name: Build bindings
        run: |
          cd bindings/python
          maturin develop --release
      
      - name: Run Rust tests
        run: |
          cd bindings/python
          cargo test --lib
      
      - name: Run Python tests
        run: |
          cd bindings/python
          pytest tests/ -v
      
      - name: Memory safety check
        if: matrix.os == 'ubuntu-latest'
        run: |
          cd bindings/python
          valgrind --leak-check=full python -m pytest tests/test_memory_safety.py
      
      - name: Performance regression check
        run: |
          cd bindings/python
          python scripts/check_performance_regression.py
```

## 📋 実装チェックリスト

### Phase 1: 基盤構築
- [ ] テストディレクトリ作成
- [ ] conftest.pyセットアップ
- [ ] メモリトラッカー実装
- [ ] GILチェッカー実装

### Phase 2: 型変換テスト
- [ ] ArrayLike変換テスト
- [ ] スカラー/配列入力テスト
- [ ] 非連続配列テスト
- [ ] 空配列処理テスト

### Phase 3: Broadcasting
- [ ] 基本broadcast動作
- [ ] 形状不一致エラー
- [ ] 複雑なbroadcastパターン

### Phase 4: エラーハンドリング
- [ ] Rust側エラー変換
- [ ] Python側バリデーション
- [ ] NaN/Inf処理
- [ ] 型エラー処理

### Phase 5: メモリ安全性
- [ ] 参照カウント検証
- [ ] メモリリーク検出
- [ ] GC相互作用テスト
- [ ] ゼロコピー検証

### Phase 6: パフォーマンス
- [ ] FFIオーバーヘッド測定
- [ ] スケーリング検証
- [ ] GIL解放確認
- [ ] 並列実行テスト

### Phase 7: CI/CD
- [ ] テストスクリプト作成
- [ ] GitHub Actions設定
- [ ] カバレッジレポート
- [ ] 回帰テストスイート

## 🎯 完了条件

1. **カバレッジ**: Bindings層のコードカバレッジ > 95%
2. **パフォーマンス**: FFIオーバーヘッド < 5%
3. **メモリ安全性**: Valgrindでリークゼロ
4. **互換性**: NumPy broadcasting完全互換
5. **CI/CD**: 全プラットフォームで自動テスト合格

## 📈 期待される効果

- **品質向上**: バグの早期発見率90%向上
- **信頼性**: メモリ関連クラッシュゼロ
- **性能保証**: パフォーマンス劣化の即座検出
- **開発効率**: リファクタリング時の安心感

## ⏰ タイムライン

- **Phase 1**: 4時間（基盤構築）
- **Phase 2-3**: 10時間（型変換とBroadcasting）
- **Phase 4-5**: 10時間（エラーとメモリ安全性）
- **Phase 6**: 4時間（パフォーマンス）
- **Phase 7**: 3時間（統合とCI/CD）
- **合計**: 31時間（約4日）

## 🚨 リスクと対策

| リスク | 対策 |
|--------|------|
| テスト実行時間増大 | 並列実行、階層的テスト |
| プラットフォーム依存 | マトリックステスト |
| 偽陽性（flaky tests） | リトライ機構、決定的テスト |
| メンテナンスコスト | 自動生成、共通化 |

## 📚 参考資料

- [PyO3 Testing Guide](https://pyo3.rs/main/debugging)
- [NumPy Testing Guidelines](https://numpy.org/doc/stable/reference/testing.html)
- [Rust FFI Testing Best Practices](https://doc.rust-lang.org/nomicon/ffi.html)
- [Python Memory Profiling](https://docs.python.org/3/library/tracemalloc.html)
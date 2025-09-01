# American Options実装計画

## エグゼクティブサマリー

American Optionsモデルの完全実装計画。Bjerksund-Stensland 2002アルゴリズムを使用し、Core層の既存実装を完成させ、Pythonバインディングを追加し、パフォーマンス最適化を適用する。実装期間は3日間を想定。

## 現状分析

### ✅ 実装済み（Core層）

#### 1. 価格計算アルゴリズム
```rust
// core/src/models/american/pricing.rs
- american_call_price()  // Bjerksund-Stensland 2002実装
- american_put_price()   // Put-Call変換による実装
- bjerksund_stensland_2002()  // メインアルゴリズム
- phi()  // 補助関数φ
- psi()  // 補助関数ψ（将来拡張用）
- cbnd() // 累積二変量正規分布
```

#### 2. 早期行使境界計算
```rust
// core/src/models/american/boundary.rs
- calculate_beta()      // βパラメータ
- calculate_b_infinity()  // 漸近行使境界
- calculate_b_zero()    // 即時行使境界
```

#### 3. Greeks計算
```rust
// core/src/models/american/greeks.rs
- calculate_american_greeks()  // 有限差分法
- delta, gamma, vega, theta, rho
```

### ❌ 未実装

1. **Pythonバインディング**: bindings/python/src/models/american.rs不在
2. **バッチ処理**: 並列処理・最適化未実装
3. **Implied Volatility**: Newton-Raphson法未実装
4. **モジュール統合**: lib.rsに未登録
5. **テスト実行**: importエラーで動作不可

## 実装計画

### Phase 1: Core層の完成と強化（Day 1）

#### 1.1 数値安定性の向上

```rust
// 改善項目
1. エッジケース処理の強化
   - 極端なmoneyness（S/K > 1000 or < 0.001）
   - 満期直前（T < 1e-6）
   - ゼロボラティリティ（σ < 1e-6）

2. 数値精度の改善
   - exp_m1()の活用
   - 対数変換での計算
   - キャンセレーション回避

3. エラーハンドリング
   - NaN/Inf検出と回復
   - 適切なフォールバック
```

#### 1.2 Implied Volatility実装

```rust
impl American {
    pub fn implied_volatility_american(
        price: f64,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        is_call: bool,
    ) -> QuantForgeResult<f64> {
        // Newton-Raphson法
        // 初期推定値: Brenner-Subrahmanyam近似
        let initial_vol = ((2.0 * PI / t).sqrt() * (price / s))
            .min(MAX_VOLATILITY)
            .max(MIN_VOLATILITY);
        
        newton_raphson(f, df, initial_vol, tolerance, max_iterations)
    }
}
```

#### 1.3 バッチ処理トレイト実装

```rust
impl American {
    pub fn call_price_batch(
        &self,
        spots: &[f64],
        strikes: &[f64],
        times: &[f64],
        rates: &[f64],
        dividend_yields: &[f64],
        sigmas: &[f64],
    ) -> Vec<QuantForgeResult<f64>> {
        let len = spots.len();
        
        if len <= MICRO_BATCH_THRESHOLD {
            self.process_micro_batch_american(...)
        } else if len < PARALLEL_THRESHOLD_SMALL {
            self.process_small_batch_american(...)
        } else {
            self.process_parallel_american(...)
        }
    }
}
```

### Phase 2: Pythonバインディング実装（Day 2）

#### 2.1 モジュール作成

```rust
// bindings/python/src/models/american.rs

use numpy::PyArray1;
use pyo3::prelude::*;
use quantforge_core::models::american::American;

/// American option pricing module
pub fn create_module(py: Python<'_>) -> PyResult<Bound<'_, PyModule>> {
    let m = PyModule::new_bound(py, "american")?;
    
    // Single calculations
    m.add_function(wrap_pyfunction!(call_price, &m)?)?;
    m.add_function(wrap_pyfunction!(put_price, &m)?)?;
    m.add_function(wrap_pyfunction!(implied_volatility, &m)?)?;
    m.add_function(wrap_pyfunction!(greeks, &m)?)?;
    
    // Batch calculations
    m.add_function(wrap_pyfunction!(call_price_batch, &m)?)?;
    m.add_function(wrap_pyfunction!(put_price_batch, &m)?)?;
    m.add_function(wrap_pyfunction!(implied_volatility_batch, &m)?)?;
    m.add_function(wrap_pyfunction!(greeks_batch, &m)?)?;
    
    // Early exercise boundary
    m.add_function(wrap_pyfunction!(exercise_boundary, &m)?)?;
    
    Ok(m)
}
```

#### 2.2 単一計算実装

```rust
#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma))]
fn call_price(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> PyResult<f64> {
    American::call_price_american(s, k, t, r, q, sigma)
        .map_err(to_py_err)
}

#[pyfunction]
#[pyo3(signature = (s, k, t, r, q, sigma, is_call=true))]
fn greeks<'py>(
    py: Python<'py>,
    s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64,
    is_call: bool,
) -> PyResult<Bound<'py, PyDict>> {
    let greeks = American::greeks_american(s, k, t, r, q, sigma, is_call)
        .map_err(to_py_err)?;
    
    let dict = PyDict::new_bound(py);
    dict.set_item("delta", greeks.delta)?;
    dict.set_item("gamma", greeks.gamma)?;
    dict.set_item("vega", greeks.vega)?;
    dict.set_item("theta", greeks.theta)?;
    dict.set_item("rho", greeks.rho)?;
    dict.set_item("dividend_rho", greeks.dividend_rho)?;
    
    Ok(dict)
}
```

#### 2.3 バッチ処理実装

```rust
#[pyfunction]
#[pyo3(signature = (spots, strikes, times, rates, dividend_yields, sigmas))]
fn call_price_batch<'py>(
    py: Python<'py>,
    spots: ArrayLike<'py>,
    strikes: ArrayLike<'py>,
    times: ArrayLike<'py>,
    rates: ArrayLike<'py>,
    dividend_yields: ArrayLike<'py>,
    sigmas: ArrayLike<'py>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // Broadcasting処理
    let inputs = vec![&spots, &strikes, &times, &rates, &dividend_yields, &sigmas];
    let iter = BroadcastIterator::new(inputs)
        .map_err(pyo3::exceptions::PyValueError::new_err)?;
    
    // データ収集
    let input_data: Vec<Vec<f64>> = iter.collect();
    let len = input_data.len();
    
    // 配列準備
    let mut spots_vec = Vec::with_capacity(len);
    let mut strikes_vec = Vec::with_capacity(len);
    let mut times_vec = Vec::with_capacity(len);
    let mut rates_vec = Vec::with_capacity(len);
    let mut dividend_yields_vec = Vec::with_capacity(len);
    let mut sigmas_vec = Vec::with_capacity(len);
    
    for values in input_data {
        spots_vec.push(values[0]);
        strikes_vec.push(values[1]);
        times_vec.push(values[2]);
        rates_vec.push(values[3]);
        dividend_yields_vec.push(values[4]);
        sigmas_vec.push(values[5]);
    }
    
    // GILリリースして計算
    let results = py.allow_threads(move || {
        let model = American;
        let batch_results = model.call_price_batch(
            &spots_vec, &strikes_vec, &times_vec,
            &rates_vec, &dividend_yields_vec, &sigmas_vec,
        );
        
        batch_results.into_iter()
            .map(|r| r.unwrap_or(f64::NAN))
            .collect::<Vec<f64>>()
    });
    
    Ok(PyArray1::from_vec_bound(py, results))
}
```

### Phase 3: 最適化とパフォーマンス（Day 2.5）

#### 3.1 小バッチ最適化

```rust
fn process_micro_batch_american(&self, /* params */) -> Vec<QuantForgeResult<f64>> {
    let len = spots.len();
    let mut results = Vec::with_capacity(len);
    
    // 4要素ループアンローリング
    let chunks = len / 4;
    for i in 0..chunks {
        let base = i * 4;
        
        // 並列計算（コンパイラ最適化）
        let p0 = American::call_price_american(
            spots[base], strikes[base], times[base],
            rates[base], dividend_yields[base], sigmas[base]
        );
        let p1 = American::call_price_american(
            spots[base+1], strikes[base+1], times[base+1],
            rates[base+1], dividend_yields[base+1], sigmas[base+1]
        );
        // ... p2, p3
        
        results.push(p0);
        results.push(p1);
        results.push(p2);
        results.push(p3);
    }
    
    // 残り要素処理
    for i in (chunks * 4)..len {
        results.push(American::call_price_american(/* params */));
    }
    
    results
}
```

#### 3.2 並列処理実装

```rust
fn process_parallel_american(&self, /* params */) -> Vec<QuantForgeResult<f64>> {
    use rayon::prelude::*;
    
    let chunk_size = if spots.len() < PARALLEL_THRESHOLD_MEDIUM {
        CHUNK_SIZE_L1
    } else {
        CHUNK_SIZE_L2
    };
    
    spots.par_chunks(chunk_size)
        .zip(strikes.par_chunks(chunk_size))
        .zip(times.par_chunks(chunk_size))
        .zip(rates.par_chunks(chunk_size))
        .zip(dividend_yields.par_chunks(chunk_size))
        .zip(sigmas.par_chunks(chunk_size))
        .flat_map(|(((((s_chunk, k_chunk), t_chunk), r_chunk), q_chunk), sigma_chunk)| {
            // チャンク内処理
            izip!(s_chunk, k_chunk, t_chunk, r_chunk, q_chunk, sigma_chunk)
                .map(|(s, k, t, r, q, sigma)| {
                    American::call_price_american(*s, *k, *t, *r, *q, *sigma)
                })
                .collect::<Vec<_>>()
        })
        .collect()
}
```

### Phase 4: テストと検証（Day 3）

#### 4.1 テスト復活

```python
# tests/unit/test_american.py修正
import quantforge as qf  # american直接インポートではなく

def test_call_price_atm():
    price = qf.american.call_price(
        s=100.0, k=100.0, t=1.0, r=0.05, q=0.0, sigma=0.2
    )
    assert price > 0
```

#### 4.2 ベンチマーク作成

```python
# benchmarks/test_american_performance.py

def benchmark_american():
    sizes = [100, 1000, 10000, 100000]
    
    for size in sizes:
        # QuantForge
        qf_time = measure_quantforge_american(size)
        
        # QuantLib比較（もし可能なら）
        ql_time = measure_quantlib_american(size)
        
        print(f"Size {size}: QF {qf_time:.3f}ms, QL {ql_time:.3f}ms")
```

#### 4.3 精度検証

```python
# tests/validation/test_american_accuracy.py

def test_against_reference_values():
    """既知の参照値との比較"""
    # Hull教科書の例題
    test_cases = [
        # (S, K, T, r, q, σ, expected_call, expected_put)
        (42, 40, 0.75, 0.04, 0.08, 0.35, 3.254, 3.745),
        (36, 40, 1.0, 0.06, 0.06, 0.20, 0.825, 4.472),
    ]
    
    for case in test_cases:
        call = qf.american.call_price(*case[:6])
        assert abs(call - case[6]) < 0.01
```

## パフォーマンス目標

### 単一計算
- Call/Put価格: < 100ns
- Greeks計算: < 500ns
- Implied Volatility: < 1μs

### バッチ処理
| バッチサイズ | 目標時間 | NumPy比 |
|------------|----------|---------|
| 100要素 | < 50μs | > 5x |
| 1,000要素 | < 500μs | > 4x |
| 10,000要素 | < 5ms | > 3x |
| 100,000要素 | < 50ms | > 2x |

## リスクと緩和策

### リスク1: Bjerksund-Stensland精度
- **問題**: 極端な条件下で精度低下
- **緩和**: European価格を下限として使用

### リスク2: 数値的不安定性
- **問題**: 深いITM/OTMでNaN発生
- **緩和**: 早期リターンとフォールバック実装

### リスク3: 性能目標未達
- **問題**: 複雑な計算で遅い
- **緩和**: キャッシュ活用、近似値テーブル

## 成功基準

1. **機能完全性**
   - [ ] 全API実装完了
   - [ ] Pythonからの利用可能
   - [ ] ドキュメント完備

2. **品質基準**
   - [ ] テストパス率 > 95%
   - [ ] 精度誤差 < 0.1%
   - [ ] エッジケース処理

3. **パフォーマンス**
   - [ ] 単一計算 < 100ns
   - [ ] 100要素 < 50μs
   - [ ] NumPy比 > 5倍

## タイムライン

### Day 1（8時間）
- 09:00-12:00: Core層の完成
- 13:00-17:00: Implied Volatility実装
- 17:00-18:00: バッチ処理準備

### Day 2（8時間）
- 09:00-12:00: Pythonバインディング基本実装
- 13:00-15:00: バッチ処理実装
- 15:00-17:00: 最適化実装
- 17:00-18:00: 初期テスト

### Day 3（4時間）
- 09:00-11:00: テスト修正と実行
- 11:00-12:00: ベンチマーク作成
- 12:00-13:00: ドキュメント作成

## まとめ

American Optionsの実装は、既存のBjerksund-Stensland 2002実装を基盤として、Pythonバインディングの追加と最適化により完成させる。3日間で完全実装を達成し、QuantForgeの機能を大幅に強化する。
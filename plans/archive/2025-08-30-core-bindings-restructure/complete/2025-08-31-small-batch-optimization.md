# 小バッチサイズ性能最適化計画

## 問題分析

### 現状のパフォーマンス問題

**100件バッチでの性能劣化**
- 旧実装: 12.29μs (NumPyの6.5倍速) ✅
- 新実装: 21.16μs (NumPyの3.78倍速) ⚠️
- **性能劣化: 1.72倍遅くなった**

### 根本原因

1. **並列化閾値の問題**
   ```rust
   pub const PARALLEL_THRESHOLD_SMALL: usize = 50_000;
   ```
   - 100件では並列化されない
   - しかし、並列化しても100件ではオーバーヘッドが大きい

2. **イテレータチェーンのオーバーヘッド**
   ```rust
   spots.iter()
       .zip(strikes.iter())
       .zip(times.iter())
       .zip(rates.iter())
       .zip(sigmas.iter())
       .map(|((((s, k), t), r), sigma)| ...)
   ```
   - 多重zipによるタプル構築のオーバーヘッド
   - 5つのイテレータの同期コスト

3. **Result型のオーバーヘッド**
   - 各計算で`QuantForgeResult<f64>`を返す
   - エラーチェックの分岐予測コスト

## 改善戦略

### Phase 1: マイクロバッチ最適化 (即効性: 高)

#### 1.1 専用の小バッチ処理パス

```rust
// core/src/models/black_scholes.rs

impl BlackScholes {
    /// 小バッチ専用の最適化実装
    #[inline(always)]
    fn process_micro_batch(
        &self,
        spots: &[f64],
        strikes: &[f64],
        times: &[f64],
        rates: &[f64],
        sigmas: &[f64],
    ) -> Vec<QuantForgeResult<f64>> {
        // 事前にキャパシティを確保
        let mut results = Vec::with_capacity(spots.len());
        
        // インデックスベースのループ（イテレータチェーンを避ける）
        for i in 0..spots.len() {
            // 直接アクセス（bounds checkは1回だけ）
            let result = unsafe {
                // SAFETY: ループ条件で範囲内が保証される
                self.call_price_unchecked(
                    *spots.get_unchecked(i),
                    *strikes.get_unchecked(i),
                    *times.get_unchecked(i),
                    *rates.get_unchecked(i),
                    *sigmas.get_unchecked(i),
                )
            };
            results.push(result);
        }
        
        results
    }
    
    /// Bounds checkなしの内部実装
    #[inline(always)]
    unsafe fn call_price_unchecked(
        &self,
        s: f64,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
    ) -> QuantForgeResult<f64> {
        // バリデーションをスキップした直接計算
        let sqrt_t = t.sqrt();
        let d1 = (s.ln() - k.ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
        let d2 = d1 - sigma * sqrt_t;
        
        let price = s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2);
        Ok(price)
    }
}
```

#### 1.2 ループアンローリング

```rust
fn process_micro_batch_unrolled(
    &self,
    spots: &[f64],
    strikes: &[f64],
    times: &[f64],
    rates: &[f64],
    sigmas: &[f64],
) -> Vec<QuantForgeResult<f64>> {
    let len = spots.len();
    let mut results = Vec::with_capacity(len);
    
    // 4要素ずつ処理（SIMD自動ベクトル化を促進）
    let chunks = len / 4;
    let remainder = len % 4;
    
    for i in 0..chunks {
        let base = i * 4;
        // コンパイラが自動ベクトル化しやすい形式
        let p0 = self.call_price(spots[base], strikes[base], times[base], rates[base], sigmas[base]);
        let p1 = self.call_price(spots[base+1], strikes[base+1], times[base+1], rates[base+1], sigmas[base+1]);
        let p2 = self.call_price(spots[base+2], strikes[base+2], times[base+2], rates[base+2], sigmas[base+2]);
        let p3 = self.call_price(spots[base+3], strikes[base+3], times[base+3], rates[base+3], sigmas[base+3]);
        
        results.push(p0);
        results.push(p1);
        results.push(p2);
        results.push(p3);
    }
    
    // 残りの要素を処理
    for i in (chunks * 4)..len {
        results.push(self.call_price(spots[i], strikes[i], times[i], rates[i], sigmas[i]));
    }
    
    results
}
```

### Phase 2: 適応的並列化 (効果: 中)

#### 2.1 動的閾値決定

```rust
// core/src/constants.rs

/// 適応的並列化の設定
pub struct AdaptiveParallelConfig {
    /// CPUコア数
    pub cpu_cores: usize,
    /// L1キャッシュサイズ
    pub l1_cache_size: usize,
    /// 測定されたFFIオーバーヘッド（ナノ秒）
    pub ffi_overhead_ns: f64,
}

impl AdaptiveParallelConfig {
    pub fn should_parallelize(&self, size: usize, element_cost_ns: f64) -> bool {
        // シーケンシャル処理のコスト
        let sequential_cost = size as f64 * element_cost_ns;
        
        // 並列化のオーバーヘッド（スレッド起動 + 同期）
        let parallel_overhead = 5000.0; // 5μs（実測値）
        
        // 並列化後の予想コスト
        let parallel_cost = (size as f64 / self.cpu_cores as f64) * element_cost_ns 
                          + parallel_overhead;
        
        // 並列化が有利な場合のみtrue
        parallel_cost < sequential_cost
    }
    
    pub fn optimal_chunk_size(&self, size: usize) -> usize {
        match size {
            0..=100 => size,  // チャンク分割しない
            101..=1000 => 64, // L1キャッシュに収まるサイズ
            1001..=10000 => 256,
            _ => 512,
        }
    }
}
```

#### 2.2 実行時プロファイリング

```rust
// core/src/profiling.rs

/// 実行時性能測定
pub struct RuntimeProfiler {
    /// 最近の実行時間を記録
    recent_timings: VecDeque<(usize, f64)>,
    /// 要素あたりのコスト推定値
    estimated_cost_per_element: f64,
}

impl RuntimeProfiler {
    pub fn update(&mut self, size: usize, elapsed_ns: f64) {
        self.recent_timings.push_back((size, elapsed_ns));
        if self.recent_timings.len() > 100 {
            self.recent_timings.pop_front();
        }
        
        // 線形回帰で要素あたりコストを推定
        self.estimated_cost_per_element = self.estimate_cost();
    }
    
    fn estimate_cost(&self) -> f64 {
        // 最小二乗法で線形回帰
        // y = ax + b where x = size, y = time
        // a = cost per element
        let n = self.recent_timings.len() as f64;
        if n < 2.0 { return 10.0; } // デフォルト値
        
        let sum_x: f64 = self.recent_timings.iter().map(|(s, _)| *s as f64).sum();
        let sum_y: f64 = self.recent_timings.iter().map(|(_, t)| *t).sum();
        let sum_xx: f64 = self.recent_timings.iter().map(|(s, _)| (*s as f64).powi(2)).sum();
        let sum_xy: f64 = self.recent_timings.iter().map(|(s, t)| *s as f64 * t).sum();
        
        let slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x.powi(2));
        slope.max(1.0) // 最小値を設定
    }
}
```

### Phase 3: Bindings層の最適化 (効果: 高)

#### 3.1 バッチサイズ別の処理分岐

```python
# bindings/python/src/black_scholes.rs

#[pyfunction]
#[pyo3(name = "call_price_batch")]
pub fn py_call_price_batch(
    spots: PyReadonlyArray1<f64>,
    strikes: PyReadonlyArray1<f64>,
    times: PyReadonlyArray1<f64>,
    rates: PyReadonlyArray1<f64>,
    sigmas: PyReadonlyArray1<f64>,
) -> PyResult<Py<PyArray1<f64>>> {
    let size = spots.len();
    
    Python::with_gil(|py| {
        // 小バッチ専用の最適化パス
        if size <= 200 {
            // GILを保持したまま高速処理
            let spots = spots.as_slice()?;
            let strikes = strikes.as_slice()?;
            let times = times.as_slice()?;
            let rates = rates.as_slice()?;
            let sigmas = sigmas.as_slice()?;
            
            // 専用の最適化実装を呼び出し
            let results = BlackScholes::default()
                .process_micro_batch(spots, strikes, times, rates, sigmas);
            
            // NumPy配列に直接書き込み
            let py_array = PyArray1::new(py, size);
            let mut array_view = unsafe { py_array.as_slice_mut()? };
            for (i, result) in results.iter().enumerate() {
                array_view[i] = result.unwrap_or(f64::NAN);
            }
            
            Ok(py_array.to_owned())
        } else {
            // 大バッチは従来通りGILをリリース
            py.allow_threads(|| {
                // 並列処理実装
                let results = BlackScholes::default()
                    .call_price_batch(spots.as_slice()?, 
                                    strikes.as_slice()?,
                                    times.as_slice()?,
                                    rates.as_slice()?,
                                    sigmas.as_slice()?);
                                    
                // 結果をNumPy配列に変換
                let py_array = PyArray1::from_vec(py, 
                    results.into_iter()
                           .map(|r| r.unwrap_or(f64::NAN))
                           .collect());
                Ok(py_array.to_owned())
            })
        }
    })
}
```

#### 3.2 プリアロケーション戦略

```rust
// 結果配列の事前確保
thread_local! {
    static RESULT_BUFFER: RefCell<Vec<f64>> = RefCell::new(Vec::with_capacity(1000));
}

fn process_with_preallocated_buffer(size: usize) -> Vec<f64> {
    RESULT_BUFFER.with(|buffer| {
        let mut buf = buffer.borrow_mut();
        buf.clear();
        buf.reserve(size);
        
        // 処理実行
        // ...
        
        buf.clone()
    })
}
```

### Phase 4: キャッシュ最適化 (効果: 中)

#### 4.1 データレイアウト最適化

```rust
/// Structure of Arrays (SoA) for better cache utilization
pub struct BatchData {
    spots: Vec<f64>,
    strikes: Vec<f64>,
    times: Vec<f64>,
    rates: Vec<f64>,
    sigmas: Vec<f64>,
}

impl BatchData {
    /// プリフェッチヒントを使用
    #[inline(always)]
    pub fn prefetch(&self, index: usize) {
        use std::intrinsics::prefetch_read_data;
        
        unsafe {
            // 次の8要素をプリフェッチ
            if index + 8 < self.spots.len() {
                prefetch_read_data(self.spots.as_ptr().add(index + 8), 3);
                prefetch_read_data(self.strikes.as_ptr().add(index + 8), 3);
                prefetch_read_data(self.times.as_ptr().add(index + 8), 3);
                prefetch_read_data(self.rates.as_ptr().add(index + 8), 3);
                prefetch_read_data(self.sigmas.as_ptr().add(index + 8), 3);
            }
        }
    }
}
```

## 期待される改善効果

### バッチサイズ100での目標

| 指標 | 現在 | 目標 | 改善率 |
|------|------|------|--------|
| 実行時間 | 21.16μs | 12μs | 43% |
| NumPy比 | 3.78x | 6.5x | 72% |
| スループット | 4.7M ops/s | 8.3M ops/s | 76% |

### サイズ別の最適化効果予測

| サイズ | 現在 | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|------|---------|---------|---------|---------|
| 100 | 21.16μs | 15μs (-29%) | 14μs (-34%) | 12μs (-43%) | 11μs (-48%) |
| 1,000 | 80.25μs | 75μs (-7%) | 70μs (-13%) | 65μs (-19%) | 60μs (-25%) |
| 10,000 | 942μs | 920μs (-2%) | 850μs (-10%) | 800μs (-15%) | 750μs (-20%) |

## 実装計画

### Week 1: Phase 1実装
- [ ] マイクロバッチ専用関数の実装
- [ ] ループアンローリングの実装
- [ ] ベンチマークでの効果測定

### Week 2: Phase 2実装
- [ ] 適応的並列化の実装
- [ ] 実行時プロファイラーの実装
- [ ] 動的閾値調整のテスト

### Week 3: Phase 3実装
- [ ] Bindings層の最適化
- [ ] プリアロケーション戦略
- [ ] Python側のベンチマーク

### Week 4: Phase 4実装とチューニング
- [ ] キャッシュ最適化
- [ ] プリフェッチヒント
- [ ] 最終的なパフォーマンステスト

## リスクと対策

### リスク1: unsafe使用による安全性
- **対策**: 厳密な境界チェックとfuzzテスト

### リスク2: プラットフォーム依存性
- **対策**: フィーチャーフラグによる条件付きコンパイル

### リスク3: 複雑性の増加
- **対策**: 明確なコメントとベンチマーク駆動開発

## 検証方法

### パフォーマンステスト
```bash
# Rustレベル
cargo bench --bench micro_batch

# Pythonレベル
python benchmarks/test_small_batch.py
```

### 正確性テスト
```bash
# プロパティベーステスト
cargo test --test property_tests

# Golden Master比較
python tests/test_accuracy.py
```

## 結論

小バッチ性能の改善は、以下の4つのフェーズで実現可能：

1. **即効性の高い最適化**: マイクロバッチ専用パスとループアンローリング
2. **スマートな並列化**: 適応的閾値と実行時プロファイリング
3. **FFI層の最適化**: バッチサイズ別処理とプリアロケーション
4. **キャッシュ効率化**: データレイアウトとプリフェッチ

これらの実装により、100件バッチでNumPyの6.5倍速という目標を達成できる見込み。
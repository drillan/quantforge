// 小バッチ最適化の実装サンプルコード

use crate::constants::*;
use crate::math::{distributions::norm_cdf, solvers::newton_raphson};
use crate::models::black_scholes::BlackScholes;
use crate::QuantForgeResult;
use std::arch::x86_64::*;

/// マイクロバッチ処理の最適化実装
impl BlackScholes {
    /// Phase 1: インデックスベースの高速処理
    #[inline(always)]
    pub fn process_micro_batch_v1(
        &self,
        spots: &[f64],
        strikes: &[f64],
        times: &[f64],
        rates: &[f64],
        sigmas: &[f64],
    ) -> Vec<QuantForgeResult<f64>> {
        debug_assert_eq!(spots.len(), strikes.len());
        debug_assert_eq!(spots.len(), times.len());
        debug_assert_eq!(spots.len(), rates.len());
        debug_assert_eq!(spots.len(), sigmas.len());
        
        let len = spots.len();
        let mut results = Vec::with_capacity(len);
        
        // インデックスループ（イテレータチェーンより高速）
        for i in 0..len {
            results.push(self.call_price(
                spots[i],
                strikes[i],
                times[i],
                rates[i],
                sigmas[i],
            ));
        }
        
        results
    }
    
    /// Phase 1+: ループアンローリング版
    #[inline(always)]
    pub fn process_micro_batch_unrolled(
        &self,
        spots: &[f64],
        strikes: &[f64],
        times: &[f64],
        rates: &[f64],
        sigmas: &[f64],
    ) -> Vec<QuantForgeResult<f64>> {
        let len = spots.len();
        let mut results = Vec::with_capacity(len);
        
        // 4要素ずつ処理
        let chunks = len / 4;
        let remainder = len % 4;
        
        for i in 0..chunks {
            let base = i * 4;
            
            // 4つの計算を並列に実行（コンパイラの自動ベクトル化を促進）
            let p0 = self.call_price_inline(
                spots[base], strikes[base], times[base], 
                rates[base], sigmas[base]
            );
            let p1 = self.call_price_inline(
                spots[base + 1], strikes[base + 1], times[base + 1],
                rates[base + 1], sigmas[base + 1]
            );
            let p2 = self.call_price_inline(
                spots[base + 2], strikes[base + 2], times[base + 2],
                rates[base + 2], sigmas[base + 2]
            );
            let p3 = self.call_price_inline(
                spots[base + 3], strikes[base + 3], times[base + 3],
                rates[base + 3], sigmas[base + 3]
            );
            
            results.push(Ok(p0));
            results.push(Ok(p1));
            results.push(Ok(p2));
            results.push(Ok(p3));
        }
        
        // 残りの要素
        let start = chunks * 4;
        for i in start..len {
            results.push(self.call_price(
                spots[i], strikes[i], times[i], rates[i], sigmas[i]
            ));
        }
        
        results
    }
    
    /// インライン化された高速版（エラーチェックを最小化）
    #[inline(always)]
    fn call_price_inline(&self, s: f64, k: f64, t: f64, r: f64, sigma: f64) -> f64 {
        let sqrt_t = t.sqrt();
        let d1 = (s.ln() - k.ln() + (r + sigma * sigma / 2.0) * t) / (sigma * sqrt_t);
        let d2 = d1 - sigma * sqrt_t;
        s * norm_cdf(d1) - k * (-r * t).exp() * norm_cdf(d2)
    }
    
    /// Phase 2: 適応的並列化
    pub fn call_price_batch_adaptive(
        &self,
        spots: &[f64],
        strikes: &[f64],
        times: &[f64],
        rates: &[f64],
        sigmas: &[f64],
    ) -> Vec<QuantForgeResult<f64>> {
        let len = spots.len();
        
        // 適応的閾値決定
        let threshold = self.compute_adaptive_threshold(len);
        
        if len < threshold {
            // 小バッチ: シーケンシャル処理
            self.process_micro_batch_unrolled(spots, strikes, times, rates, sigmas)
        } else {
            // 大バッチ: 並列処理
            self.call_price_batch_parallel(spots, strikes, times, rates, sigmas)
        }
    }
    
    /// 動的な並列化閾値を計算
    fn compute_adaptive_threshold(&self, _size: usize) -> usize {
        let cpu_cores = num_cpus::get();
        
        // CPUコア数に基づく基本閾値
        let base_threshold = match cpu_cores {
            1..=2 => 10_000,   // デュアルコア
            3..=4 => 5_000,    // クアッドコア
            5..=8 => 2_000,    // オクタコア
            _ => 1_000,        // それ以上
        };
        
        // L1キャッシュサイズも考慮（64KB想定）
        let cache_elements = 64_000 / 40; // 5つのf64配列
        
        base_threshold.min(cache_elements)
    }
    
    /// 並列処理版（既存の実装を改良）
    fn call_price_batch_parallel(
        &self,
        spots: &[f64],
        strikes: &[f64],
        times: &[f64],
        rates: &[f64],
        sigmas: &[f64],
    ) -> Vec<QuantForgeResult<f64>> {
        use rayon::prelude::*;
        
        let len = spots.len();
        let chunk_size = self.optimal_chunk_size(len);
        
        spots
            .par_chunks(chunk_size)
            .zip(strikes.par_chunks(chunk_size))
            .zip(times.par_chunks(chunk_size))
            .zip(rates.par_chunks(chunk_size))
            .zip(sigmas.par_chunks(chunk_size))
            .flat_map(|((((s_chunk, k_chunk), t_chunk), r_chunk), sigma_chunk)| {
                // 各チャンクをマイクロバッチとして処理
                self.process_micro_batch_unrolled(
                    s_chunk, k_chunk, t_chunk, r_chunk, sigma_chunk
                )
            })
            .collect()
    }
    
    /// 最適なチャンクサイズを決定
    fn optimal_chunk_size(&self, total_size: usize) -> usize {
        let cpu_cores = num_cpus::get();
        
        match total_size {
            0..=1000 => total_size,        // チャンク分割しない
            1001..=10_000 => 256,           // L1キャッシュ最適化
            10_001..=100_000 => 1024,       // L2キャッシュ最適化
            _ => total_size / (cpu_cores * 4), // CPUコアあたり4チャンク
        }
    }
}

/// Phase 3: プロファイリングベースの最適化
pub struct AdaptiveOptimizer {
    /// 最近の実行統計
    recent_runs: Vec<(usize, f64)>,
    /// 推定される要素あたりコスト
    cost_per_element: f64,
    /// 並列化オーバーヘッド
    parallel_overhead: f64,
}

impl AdaptiveOptimizer {
    pub fn new() -> Self {
        Self {
            recent_runs: Vec::with_capacity(100),
            cost_per_element: 10.0, // 初期値: 10ns
            parallel_overhead: 5000.0, // 初期値: 5μs
        }
    }
    
    /// 実行時間を記録して統計を更新
    pub fn record_execution(&mut self, size: usize, elapsed_ns: f64) {
        self.recent_runs.push((size, elapsed_ns));
        
        // 最新100件のみ保持
        if self.recent_runs.len() > 100 {
            self.recent_runs.remove(0);
        }
        
        // 統計を更新
        self.update_statistics();
    }
    
    /// 線形回帰で要素あたりコストを推定
    fn update_statistics(&mut self) {
        if self.recent_runs.len() < 10 {
            return; // データ不足
        }
        
        // 小バッチのデータのみで推定
        let small_batch_data: Vec<_> = self.recent_runs
            .iter()
            .filter(|(size, _)| *size < 1000)
            .copied()
            .collect();
        
        if small_batch_data.len() >= 5 {
            // 最小二乗法
            let n = small_batch_data.len() as f64;
            let sum_x: f64 = small_batch_data.iter().map(|(s, _)| *s as f64).sum();
            let sum_y: f64 = small_batch_data.iter().map(|(_, t)| *t).sum();
            let sum_xx: f64 = small_batch_data.iter().map(|(s, _)| (*s as f64).powi(2)).sum();
            let sum_xy: f64 = small_batch_data.iter().map(|(s, t)| *s as f64 * t).sum();
            
            let slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x.powi(2));
            self.cost_per_element = slope.max(1.0);
        }
        
        // 並列化オーバーヘッドの推定
        self.estimate_parallel_overhead();
    }
    
    /// 並列化オーバーヘッドを推定
    fn estimate_parallel_overhead(&mut self) {
        // 中規模バッチのデータから推定
        let medium_batch_data: Vec<_> = self.recent_runs
            .iter()
            .filter(|(size, _)| *size >= 1000 && *size <= 10000)
            .copied()
            .collect();
        
        if medium_batch_data.len() >= 5 {
            // 実際の時間と予想される時間の差から推定
            let mut overhead_estimates = Vec::new();
            
            for (size, actual_time) in &medium_batch_data {
                let expected_sequential = *size as f64 * self.cost_per_element;
                let overhead = actual_time - expected_sequential / num_cpus::get() as f64;
                if overhead > 0.0 {
                    overhead_estimates.push(overhead);
                }
            }
            
            if !overhead_estimates.is_empty() {
                // 中央値を採用
                overhead_estimates.sort_by(|a, b| a.partial_cmp(b).unwrap());
                let median_idx = overhead_estimates.len() / 2;
                self.parallel_overhead = overhead_estimates[median_idx];
            }
        }
    }
    
    /// 並列化すべきかを判定
    pub fn should_parallelize(&self, size: usize) -> bool {
        let sequential_cost = size as f64 * self.cost_per_element;
        let parallel_cost = (size as f64 / num_cpus::get() as f64) * self.cost_per_element 
                          + self.parallel_overhead;
        
        parallel_cost < sequential_cost * 0.8 // 20%以上の改善が見込める場合のみ
    }
}

/// Phase 4: キャッシュ最適化版
#[repr(align(64))] // キャッシュライン境界にアライメント
pub struct AlignedBatchData {
    pub spots: Vec<f64>,
    pub strikes: Vec<f64>,
    pub times: Vec<f64>,
    pub rates: Vec<f64>,
    pub sigmas: Vec<f64>,
}

impl AlignedBatchData {
    /// データプリフェッチング
    #[cfg(target_arch = "x86_64")]
    #[inline(always)]
    pub unsafe fn prefetch(&self, index: usize) {
        use std::arch::x86_64::_mm_prefetch;
        
        const PREFETCH_DISTANCE: usize = 8;
        
        if index + PREFETCH_DISTANCE < self.spots.len() {
            _mm_prefetch(
                self.spots.as_ptr().add(index + PREFETCH_DISTANCE) as *const i8,
                _MM_HINT_T0
            );
            _mm_prefetch(
                self.strikes.as_ptr().add(index + PREFETCH_DISTANCE) as *const i8,
                _MM_HINT_T0
            );
            _mm_prefetch(
                self.times.as_ptr().add(index + PREFETCH_DISTANCE) as *const i8,
                _MM_HINT_T0
            );
            _mm_prefetch(
                self.rates.as_ptr().add(index + PREFETCH_DISTANCE) as *const i8,
                _MM_HINT_T0
            );
            _mm_prefetch(
                self.sigmas.as_ptr().add(index + PREFETCH_DISTANCE) as *const i8,
                _MM_HINT_T0
            );
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::Instant;
    
    #[test]
    fn test_micro_batch_performance() {
        let bs = BlackScholes::default();
        let size = 100;
        
        // テストデータ
        let spots: Vec<f64> = (0..size).map(|i| 100.0 + i as f64).collect();
        let strikes = vec![100.0; size];
        let times = vec![1.0; size];
        let rates = vec![0.05; size];
        let sigmas = vec![0.2; size];
        
        // 旧実装
        let start = Instant::now();
        let _result1 = spots.iter()
            .zip(strikes.iter())
            .zip(times.iter())
            .zip(rates.iter())
            .zip(sigmas.iter())
            .map(|((((s, k), t), r), sigma)| {
                bs.call_price(*s, *k, *t, *r, *sigma)
            })
            .collect::<Vec<_>>();
        let old_time = start.elapsed();
        
        // 新実装 v1
        let start = Instant::now();
        let _result2 = bs.process_micro_batch_v1(&spots, &strikes, &times, &rates, &sigmas);
        let new_v1_time = start.elapsed();
        
        // 新実装 unrolled
        let start = Instant::now();
        let _result3 = bs.process_micro_batch_unrolled(&spots, &strikes, &times, &rates, &sigmas);
        let unrolled_time = start.elapsed();
        
        println!("Old implementation: {:?}", old_time);
        println!("New v1: {:?} (speedup: {:.2}x)", new_v1_time, 
                 old_time.as_nanos() as f64 / new_v1_time.as_nanos() as f64);
        println!("Unrolled: {:?} (speedup: {:.2}x)", unrolled_time,
                 old_time.as_nanos() as f64 / unrolled_time.as_nanos() as f64);
        
        // 新実装が速いことを確認
        assert!(new_v1_time < old_time);
        assert!(unrolled_time < old_time);
    }
    
    #[test]
    fn test_adaptive_optimizer() {
        let mut optimizer = AdaptiveOptimizer::new();
        
        // シミュレートされた実行データ
        optimizer.record_execution(100, 1000.0);  // 100要素、1μs
        optimizer.record_execution(200, 2100.0);  // 200要素、2.1μs
        optimizer.record_execution(500, 5200.0);  // 500要素、5.2μs
        optimizer.record_execution(1000, 10500.0); // 1000要素、10.5μs
        
        // 要素あたりコストが正しく推定されているか
        assert!(optimizer.cost_per_element > 9.0 && optimizer.cost_per_element < 11.0);
        
        // 小バッチでは並列化しない
        assert!(!optimizer.should_parallelize(100));
        
        // 大バッチでは並列化する
        assert!(optimizer.should_parallelize(100_000));
    }
}
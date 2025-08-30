//! 動的並列化戦略モジュール
//!
//! データサイズとシステム特性に基づいて最適な処理戦略を選択

use crate::constants::{
    CHUNK_SIZE_L1, CHUNK_SIZE_L2, CHUNK_SIZE_L3, MAX_PARALLELISM, MIN_WORK_PER_THREAD,
    PARALLEL_THRESHOLD_LARGE, PARALLEL_THRESHOLD_MEDIUM, PARALLEL_THRESHOLD_SMALL,
};
use rayon::prelude::*;
use std::cmp;

/// 処理モード
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ProcessingMode {
    /// シーケンシャル処理（小規模データ）
    Sequential,
    /// L1キャッシュ最適化（中小規模）
    CacheOptimizedL1,
    /// L2キャッシュ最適化（中規模）
    CacheOptimizedL2,
    /// フル並列化（大規模）
    FullParallel,
    /// ハイブリッド（超大規模）
    HybridParallel,
}

/// 並列化戦略
pub struct ParallelStrategy {
    num_threads: usize,
    mode: ProcessingMode,
    chunk_size: usize,
}

impl ParallelStrategy {
    /// データサイズに基づいて最適な戦略を選択
    pub fn select(data_size: usize) -> Self {
        let num_threads = rayon::current_num_threads();

        // 処理モードとチャンクサイズの選択
        let (mode, chunk_size) = match data_size {
            // 小規模: シーケンシャル処理
            0..=PARALLEL_THRESHOLD_SMALL => (ProcessingMode::Sequential, data_size),

            // 中小規模: L1キャッシュ最適化
            n if n <= PARALLEL_THRESHOLD_MEDIUM => {
                let chunk = Self::calculate_optimal_chunk(n, CHUNK_SIZE_L1, num_threads);
                (ProcessingMode::CacheOptimizedL1, chunk)
            }

            // 中規模: L2キャッシュ最適化
            n if n <= PARALLEL_THRESHOLD_LARGE => {
                let chunk = Self::calculate_optimal_chunk(n, CHUNK_SIZE_L2, num_threads);
                (ProcessingMode::CacheOptimizedL2, chunk)
            }

            // 大規模: フル並列化
            n if n <= PARALLEL_THRESHOLD_LARGE * 10 => {
                let chunk = Self::calculate_optimal_chunk(n, CHUNK_SIZE_L3, num_threads);
                (ProcessingMode::FullParallel, chunk)
            }

            // 超大規模: ハイブリッド戦略
            n => {
                let chunk = Self::calculate_optimal_chunk(n, CHUNK_SIZE_L3, num_threads);
                (ProcessingMode::HybridParallel, chunk)
            }
        };

        Self {
            num_threads,
            mode,
            chunk_size,
        }
    }

    /// 最適なチャンクサイズを計算
    fn calculate_optimal_chunk(data_size: usize, cache_chunk: usize, num_threads: usize) -> usize {
        // 各スレッドが処理する最小ワークロード
        let min_chunk = MIN_WORK_PER_THREAD;

        // キャッシュに収まる最大サイズ
        let cache_optimal = cmp::min(cache_chunk, data_size);

        // スレッド数を考慮した均等分割
        let thread_optimal = data_size.div_ceil(num_threads);

        // 最適なチャンクサイズを選択
        cmp::max(min_chunk, cmp::min(cache_optimal, thread_optimal))
    }

    /// 処理モードを取得
    pub fn mode(&self) -> ProcessingMode {
        self.mode
    }

    /// チャンクサイズを取得
    pub fn chunk_size(&self) -> usize {
        self.chunk_size
    }

    /// 並列度を取得
    pub fn parallelism(&self) -> usize {
        match self.mode {
            ProcessingMode::Sequential => 1,
            ProcessingMode::CacheOptimizedL1 => cmp::min(2, self.num_threads),
            ProcessingMode::CacheOptimizedL2 => cmp::min(4, self.num_threads),
            ProcessingMode::FullParallel => cmp::min(self.num_threads, MAX_PARALLELISM),
            ProcessingMode::HybridParallel => cmp::min(self.num_threads, MAX_PARALLELISM),
        }
    }

    /// 処理を実行（汎用バッチ処理）
    pub fn process_batch<T, F, R>(&self, data: &[T], f: F) -> Vec<R>
    where
        T: Sync,
        F: Fn(&T) -> R + Sync,
        R: Send,
    {
        match self.mode {
            ProcessingMode::Sequential => {
                // シーケンシャル処理
                data.iter().map(f).collect()
            }
            _ => {
                // 並列処理（チャンクサイズで制御）
                let chunk_size = self.chunk_size;
                data.par_chunks(chunk_size)
                    .flat_map(|chunk| chunk.iter().map(&f).collect::<Vec<_>>())
                    .collect()
            }
        }
    }

    /// 処理を実行（in-place変更）
    pub fn process_batch_mut<T, F>(&self, data: &mut [T], f: F)
    where
        T: Send,
        F: Fn(&mut T) + Sync,
    {
        match self.mode {
            ProcessingMode::Sequential => {
                // シーケンシャル処理
                data.iter_mut().for_each(f);
            }
            _ => {
                // 並列処理（チャンクサイズで制御）
                let chunk_size = self.chunk_size;
                data.par_chunks_mut(chunk_size)
                    .for_each(|chunk| chunk.iter_mut().for_each(&f));
            }
        }
    }

    /// 出力配列への処理（ゼロコピー）
    pub fn process_into<T, F>(&self, input: &[T], output: &mut [f64], f: F)
    where
        T: Sync,
        F: Fn(&T) -> f64 + Sync,
    {
        assert_eq!(
            input.len(),
            output.len(),
            "Input and output arrays must have the same length"
        );

        match self.mode {
            ProcessingMode::Sequential => {
                // シーケンシャル処理
                for (i, item) in input.iter().enumerate() {
                    output[i] = f(item);
                }
            }
            _ => {
                // 並列処理（チャンクサイズで制御）
                let chunk_size = self.chunk_size;
                input
                    .par_chunks(chunk_size)
                    .zip(output.par_chunks_mut(chunk_size))
                    .for_each(|(in_chunk, out_chunk)| {
                        for (i, item) in in_chunk.iter().enumerate() {
                            out_chunk[i] = f(item);
                        }
                    });
            }
        }
    }

    /// スレッドプールの制御付き処理
    pub fn process_with_pool_control<T, F, R>(&self, data: &[T], f: F) -> Vec<R>
    where
        T: Sync,
        F: Fn(&T) -> R + Sync + Send,
        R: Send,
    {
        // 並列度に基づいてスレッドプールを制限
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(self.parallelism())
            .build()
            .unwrap();

        pool.install(|| self.process_batch(data, f))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_strategy_selection() {
        // 小規模データ
        let strategy = ParallelStrategy::select(100);
        assert_eq!(strategy.mode(), ProcessingMode::Sequential);

        // 中規模データ
        let strategy = ParallelStrategy::select(50_000);
        assert!(matches!(
            strategy.mode(),
            ProcessingMode::CacheOptimizedL1 | ProcessingMode::CacheOptimizedL2
        ));

        // 大規模データ
        let strategy = ParallelStrategy::select(1_000_000);
        assert!(matches!(
            strategy.mode(),
            ProcessingMode::FullParallel | ProcessingMode::HybridParallel
        ));
    }

    #[test]
    fn test_chunk_size_calculation() {
        let strategy = ParallelStrategy::select(100_000);
        assert!(strategy.chunk_size() >= MIN_WORK_PER_THREAD);
        assert!(strategy.chunk_size() <= 100_000);
    }

    #[test]
    fn test_parallelism_limits() {
        let strategy = ParallelStrategy::select(10_000_000);
        assert!(strategy.parallelism() <= MAX_PARALLELISM);
        assert!(strategy.parallelism() >= 1);
    }

    #[test]
    fn test_process_batch() {
        let data: Vec<f64> = (0..1000).map(|i| i as f64).collect();
        let strategy = ParallelStrategy::select(data.len());

        let result = strategy.process_batch(&data, |&x| x * 2.0);
        assert_eq!(result.len(), data.len());

        for (i, &val) in result.iter().enumerate() {
            assert_eq!(val, data[i] * 2.0);
        }
    }

    #[test]
    fn test_process_into() {
        let input: Vec<f64> = (0..1000).map(|i| i as f64).collect();
        let mut output = vec![0.0; 1000];
        let strategy = ParallelStrategy::select(input.len());

        strategy.process_into(&input, &mut output, |&x| x * 2.0);

        for (i, &val) in output.iter().enumerate() {
            assert_eq!(val, input[i] * 2.0);
        }
    }
}

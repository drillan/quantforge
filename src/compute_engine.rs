/// Generic compute engine for numerical calculations with optimized execution strategies
/// This module provides a unified interface for batch processing with automatic
/// optimization selection based on data size and available hardware features.

use rayon::prelude::*;
use std::marker::PhantomData;

/// Threshold constants for execution strategy selection
pub mod thresholds {
    /// Below this size, use sequential execution
    pub const SEQUENTIAL_THRESHOLD: usize = 1_000;
    
    /// Below this size, use SIMD without parallelization
    pub const SIMD_ONLY_THRESHOLD: usize = 10_000;
    
    /// Above this size, use full parallel SIMD
    pub const FULL_PARALLEL_THRESHOLD: usize = 50_000;
    
    /// Optimal chunk size for cache efficiency
    pub const OPTIMAL_CHUNK_SIZE: usize = 1_024;
}

/// Execution strategy for batch computations
#[derive(Debug, Clone, Copy)]
pub enum ExecutionStrategy {
    /// Sequential execution for small datasets
    Sequential,
    /// SIMD execution without parallelization
    SimdOnly,
    /// Parallel execution with specified thread count
    Parallel(usize),
    /// Combined SIMD and parallel execution
    SimdParallel(usize),
}

/// Trait for types that can be computed in batches
pub trait BatchComputable: Send + Sync + Sized {
    type Input: Send + Sync;
    type Output: Send + Sync;
    type Error: Send + Sync;
    
    /// Compute single element
    fn compute_single(input: &Self::Input) -> Result<Self::Output, Self::Error>;
    
    /// Compute batch with optimal strategy
    fn compute_batch(inputs: &[Self::Input]) -> Vec<Result<Self::Output, Self::Error>> {
        let strategy = Self::select_strategy(inputs.len());
        Self::compute_with_strategy(inputs, strategy)
    }
    
    /// Select optimal execution strategy based on data size
    fn select_strategy(size: usize) -> ExecutionStrategy {
        match size {
            0..=1_000 => ExecutionStrategy::Sequential,
            1_001..=10_000 => ExecutionStrategy::SimdOnly,
            10_001..=50_000 => ExecutionStrategy::Parallel(4),
            _ => ExecutionStrategy::SimdParallel(num_cpus::get()),
        }
    }
    
    /// Execute computation with specified strategy
    fn compute_with_strategy(
        inputs: &[Self::Input],
        strategy: ExecutionStrategy,
    ) -> Vec<Result<Self::Output, Self::Error>> {
        match strategy {
            ExecutionStrategy::Sequential => {
                inputs.iter().map(Self::compute_single).collect()
            }
            ExecutionStrategy::SimdOnly => {
                // For now, fallback to sequential (SIMD would be added if needed)
                inputs.iter().map(Self::compute_single).collect()
            }
            ExecutionStrategy::Parallel(threads) => {
                let pool = rayon::ThreadPoolBuilder::new()
                    .num_threads(threads)
                    .build()
                    .unwrap_or_else(|_| rayon::current());
                
                pool.install(|| {
                    inputs.par_iter().map(Self::compute_single).collect()
                })
            }
            ExecutionStrategy::SimdParallel(threads) => {
                let pool = rayon::ThreadPoolBuilder::new()
                    .num_threads(threads)
                    .build()
                    .unwrap_or_else(|_| rayon::current());
                
                pool.install(|| {
                    inputs
                        .par_chunks(thresholds::OPTIMAL_CHUNK_SIZE)
                        .flat_map(|chunk| {
                            chunk.iter().map(Self::compute_single).collect::<Vec<_>>()
                        })
                        .collect()
                })
            }
        }
    }
}

/// Generic compute engine with type-safe batch processing
pub struct ComputeEngine<T: BatchComputable> {
    _phantom: PhantomData<T>,
}

impl<T: BatchComputable> ComputeEngine<T> {
    /// Create new compute engine
    pub fn new() -> Self {
        Self {
            _phantom: PhantomData,
        }
    }
    
    /// Process batch with automatic optimization
    pub fn process_batch(
        &self,
        inputs: &[T::Input],
    ) -> Vec<Result<T::Output, T::Error>> {
        T::compute_batch(inputs)
    }
    
    /// Process batch with custom strategy
    pub fn process_batch_with_strategy(
        &self,
        inputs: &[T::Input],
        strategy: ExecutionStrategy,
    ) -> Vec<Result<T::Output, T::Error>> {
        T::compute_with_strategy(inputs, strategy)
    }
    
    /// Get recommended strategy for given size
    pub fn recommend_strategy(&self, size: usize) -> ExecutionStrategy {
        T::select_strategy(size)
    }
}

/// Helper trait for vectorizable operations
pub trait Vectorizable: Sized + Send + Sync {
    /// Apply operation to slice with automatic vectorization hints
    #[inline(always)]
    fn apply_vectorized<F>(data: &[Self], operation: F) -> Vec<Self>
    where
        F: Fn(&Self) -> Self + Send + Sync,
        Self: Clone,
    {
        // Compiler hints for auto-vectorization
        let len = data.len();
        let mut result = Vec::with_capacity(len);
        
        // Process in chunks for better cache utilization
        for chunk in data.chunks(64) {
            for item in chunk {
                result.push(operation(item));
            }
        }
        
        result
    }
    
    /// Apply operation in place with vectorization hints
    #[inline(always)]
    fn apply_vectorized_inplace<F>(data: &mut [Self], operation: F)
    where
        F: Fn(&mut Self) + Send + Sync,
    {
        // Process in chunks for better cache utilization
        for chunk in data.chunks_mut(64) {
            for item in chunk {
                operation(item);
            }
        }
    }
}

// Implement Vectorizable for common numeric types
impl Vectorizable for f64 {}
impl Vectorizable for f32 {}
impl Vectorizable for i64 {}
impl Vectorizable for i32 {}

/// Macro for implementing BatchComputable for option pricing models
#[macro_export]
macro_rules! impl_batch_computable {
    (
        $name:ident,
        input: $input:ty,
        output: $output:ty,
        compute: $compute_fn:expr
    ) => {
        pub struct $name;
        
        impl BatchComputable for $name {
            type Input = $input;
            type Output = $output;
            type Error = String;
            
            fn compute_single(input: &Self::Input) -> Result<Self::Output, Self::Error> {
                $compute_fn(input).map_err(|e| e.to_string())
            }
        }
    };
}

/// Optimized parallel iterator for numerical computations
pub trait ParallelNumericExt: ParallelIterator {
    /// Map with automatic chunking for cache efficiency
    fn map_cached<F, R>(self, f: F) -> impl ParallelIterator<Item = R>
    where
        F: Fn(Self::Item) -> R + Send + Sync,
        R: Send,
        Self: Sized,
    {
        self.chunks(thresholds::OPTIMAL_CHUNK_SIZE)
            .flat_map(move |chunk| {
                chunk.into_iter().map(&f).collect::<Vec<_>>()
            })
    }
}

impl<T: ParallelIterator> ParallelNumericExt for T {}

/// Cache-aware matrix operations
pub mod matrix_ops {
    use super::*;
    
    /// Process 2D data with cache-aware tiling
    pub fn process_2d_tiled<T, F>(
        data: &[Vec<T>],
        tile_size: usize,
        operation: F,
    ) -> Vec<Vec<T>>
    where
        T: Clone + Send + Sync,
        F: Fn(&T) -> T + Send + Sync,
    {
        let rows = data.len();
        if rows == 0 {
            return Vec::new();
        }
        let cols = data[0].len();
        let mut result = vec![vec![data[0][0].clone(); cols]; rows];
        
        // Process in tiles for better cache utilization
        for row_tile in (0..rows).step_by(tile_size) {
            for col_tile in (0..cols).step_by(tile_size) {
                for i in row_tile..std::cmp::min(row_tile + tile_size, rows) {
                    for j in col_tile..std::cmp::min(col_tile + tile_size, cols) {
                        result[i][j] = operation(&data[i][j]);
                    }
                }
            }
        }
        
        result
    }
}

/// Error handling utilities
pub mod error_handling {
    use std::fmt;
    
    /// Unified error type for compute operations
    #[derive(Debug)]
    pub enum ComputeError {
        /// Input validation failed
        ValidationError(String),
        /// Numerical computation error
        NumericalError(String),
        /// Convergence failed
        ConvergenceError { iterations: u32, tolerance: f64 },
        /// Dimension mismatch
        DimensionMismatch { expected: usize, actual: usize },
        /// Value out of range
        OutOfRange { value: f64, min: f64, max: f64 },
    }
    
    impl fmt::Display for ComputeError {
        fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
            match self {
                ComputeError::ValidationError(msg) => write!(f, "Validation error: {}", msg),
                ComputeError::NumericalError(msg) => write!(f, "Numerical error: {}", msg),
                ComputeError::ConvergenceError { iterations, tolerance } => {
                    write!(f, "Failed to converge after {} iterations (tolerance: {})", iterations, tolerance)
                }
                ComputeError::DimensionMismatch { expected, actual } => {
                    write!(f, "Dimension mismatch: expected {}, got {}", expected, actual)
                }
                ComputeError::OutOfRange { value, min, max } => {
                    write!(f, "Value {} out of range [{}, {}]", value, min, max)
                }
            }
        }
    }
    
    impl std::error::Error for ComputeError {}
}

#[cfg(test)]
mod tests {
    use super::*;
    
    struct TestComputation;
    
    impl BatchComputable for TestComputation {
        type Input = f64;
        type Output = f64;
        type Error = String;
        
        fn compute_single(input: &Self::Input) -> Result<Self::Output, Self::Error> {
            Ok(input * 2.0)
        }
    }
    
    #[test]
    fn test_strategy_selection() {
        assert!(matches!(
            TestComputation::select_strategy(500),
            ExecutionStrategy::Sequential
        ));
        assert!(matches!(
            TestComputation::select_strategy(5_000),
            ExecutionStrategy::SimdOnly
        ));
        assert!(matches!(
            TestComputation::select_strategy(25_000),
            ExecutionStrategy::Parallel(_)
        ));
        assert!(matches!(
            TestComputation::select_strategy(100_000),
            ExecutionStrategy::SimdParallel(_)
        ));
    }
    
    #[test]
    fn test_compute_engine() {
        let engine = ComputeEngine::<TestComputation>::new();
        let inputs = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let results = engine.process_batch(&inputs);
        
        assert_eq!(results.len(), 5);
        assert_eq!(results[0].as_ref().unwrap(), &2.0);
        assert_eq!(results[4].as_ref().unwrap(), &10.0);
    }
    
    #[test]
    fn test_vectorizable_operations() {
        let data = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = f64::apply_vectorized(&data, |x| x * x);
        
        assert_eq!(result, vec![1.0, 4.0, 9.0, 16.0, 25.0]);
    }
}
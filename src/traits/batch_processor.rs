use numpy::{PyArray1, PyArrayMethods, PyReadonlyArray1};
use pyo3::prelude::*;

use crate::constants::{CHUNK_SIZE_L1, PARALLEL_THRESHOLD_MEDIUM, PARALLEL_THRESHOLD_SMALL};
use crate::error::{QuantForgeResult, ValidationBuilder};
use crate::optimization::ParallelStrategy;

/// Generic batch processing trait for option pricing models
/// This trait eliminates code duplication across Black-Scholes, Black76, and Merton models
pub trait BatchProcessor: Sync {
    type Params;
    type Output;

    /// Create parameters from input values
    fn create_params(&self, price: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params;

    /// Process single value
    fn process_single(&self, params: &Self::Params) -> Self::Output;

    /// Process batch with validation and zero-copy optimization (parallel version)
    #[allow(clippy::too_many_arguments)]
    fn process_batch_parallel<'py>(
        &self,
        py: Python<'py>,
        prices: PyReadonlyArray1<f64>,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        price_type: &str,
    ) -> PyResult<Bound<'py, PyArray1<f64>>>
    where
        Self::Output: Into<f64> + Send,
        Self::Params: Send + Sync,
        Self: Sync,
    {
        // Unified validation
        self.validate_common_params(k, t, sigma)
            .map_err(PyErr::from)?;

        let prices_slice = prices.as_slice()?;
        self.validate_price_array(prices_slice, price_type)
            .map_err(PyErr::from)?;

        // Zero-copy output allocation
        let len = prices_slice.len();
        // SAFETY: PyArray1::new_bound is safe under the following conditions:
        // 1. `py` is a valid GIL token obtained from the function parameter
        // 2. `len` is the validated size from the input array
        // 3. `false` flag ensures the array is properly initialized with zeros
        // 4. No other references to this memory exist yet (newly allocated)
        let output = unsafe { PyArray1::<f64>::new_bound(py, len, false) };

        // Process with GIL release for parallel execution
        // SAFETY: as_slice_mut() is safe under the following conditions:
        // 1. `output` is a newly created array owned by this function
        // 2. No other threads can access this array (GIL is held)
        // 3. No aliasing exists (this is the only mutable reference)
        // 4. The slice lifetime is bounded by the array's lifetime
        let output_slice = unsafe { output.as_slice_mut()? };

        // Dynamic strategy selection based on size
        match len {
            0..=PARALLEL_THRESHOLD_SMALL => {
                self.process_sequential(prices_slice, k, t, r, sigma, output_slice)
            }
            _ => {
                // For large datasets, use parallel processing with GIL release
                self.process_parallel_with_gil_release(
                    py,
                    prices_slice,
                    k,
                    t,
                    r,
                    sigma,
                    output_slice,
                )
            }
        }

        Ok(output)
    }

    /// Process batch with validation and zero-copy optimization (sequential version)
    #[allow(clippy::too_many_arguments)]
    fn process_batch<'py>(
        &self,
        py: Python<'py>,
        prices: PyReadonlyArray1<f64>,
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        price_type: &str,
    ) -> PyResult<Bound<'py, PyArray1<f64>>>
    where
        Self::Output: Into<f64>,
    {
        // Unified validation
        self.validate_common_params(k, t, sigma)
            .map_err(PyErr::from)?;

        let prices_slice = prices.as_slice()?;
        self.validate_price_array(prices_slice, price_type)
            .map_err(PyErr::from)?;

        // Zero-copy output allocation
        let len = prices_slice.len();
        // SAFETY: PyArray1::new_bound is safe under the following conditions:
        // 1. `py` is a valid GIL token obtained from the function parameter
        // 2. `len` is the validated size from the input array
        // 3. `false` flag ensures the array is properly initialized with zeros
        // 4. No other references to this memory exist yet (newly allocated)
        let output = unsafe { PyArray1::<f64>::new_bound(py, len, false) };

        // Process without GIL release for now (safety issue with mutable array)
        // SAFETY: as_slice_mut() is safe under the following conditions:
        // 1. `output` is a newly created array owned by this function
        // 2. No other threads can access this array (GIL is held)
        // 3. No aliasing exists (this is the only mutable reference)
        // 4. The slice lifetime is bounded by the array's lifetime
        let output_slice = unsafe { output.as_slice_mut()? };

        // Process sequentially (use process_batch_parallel for parallel processing)
        self.process_sequential(prices_slice, k, t, r, sigma, output_slice);

        Ok(output)
    }

    /// Sequential processing for small datasets
    fn process_sequential(
        &self,
        prices: &[f64],
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        output: &mut [f64],
    ) where
        Self::Output: Into<f64>,
    {
        for (i, &price) in prices.iter().enumerate() {
            let params = self.create_params(price, k, t, r, sigma);
            output[i] = self.process_single(&params).into();
        }
    }

    /// Parallel processing for large datasets with dynamic chunking
    fn process_parallel(
        &self,
        prices: &[f64],
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        output: &mut [f64],
    ) where
        Self::Output: Into<f64> + Send,
        Self::Params: Send + Sync,
    {
        // Use dynamic strategy to determine optimal chunk size
        let strategy = ParallelStrategy::select(prices.len());

        // Create parameter-output pairs for processing
        let mut params_vec: Vec<Self::Params> = Vec::with_capacity(prices.len());
        for &price in prices {
            params_vec.push(self.create_params(price, k, t, r, sigma));
        }

        // Process using the optimized strategy
        strategy.process_into(&params_vec, output, |params| {
            self.process_single(params).into()
        });
    }

    /// Parallel processing with GIL release for maximum performance
    #[allow(clippy::too_many_arguments)]
    fn process_parallel_with_gil_release(
        &self,
        py: Python<'_>,
        prices: &[f64],
        k: f64,
        t: f64,
        r: f64,
        sigma: f64,
        output: &mut [f64],
    ) where
        Self::Output: Into<f64> + Send,
        Self::Params: Send + Sync,
        Self: Sync,
    {
        // SAFETY: We can safely release the GIL here because:
        // 1. prices is a borrowed slice from a NumPy array (read-only)
        // 2. output is a mutable slice from a newly created array with no other references
        // 3. We don't access any Python objects during parallel processing
        // 4. All parameters (k, t, r, sigma) are primitive types
        // 5. The self reference is Sync, ensuring thread safety
        py.allow_threads(|| {
            // Process based on selected strategy
            if prices.len() <= PARALLEL_THRESHOLD_MEDIUM {
                // For small to medium datasets, use sequential processing
                self.process_sequential(prices, k, t, r, sigma, output);
            } else {
                // For large datasets, use optimized parallel processing
                self.process_parallel(prices, k, t, r, sigma, output);
            }
        });
    }

    /// Validate common parameters
    fn validate_common_params(&self, k: f64, t: f64, sigma: f64) -> QuantForgeResult<()> {
        ValidationBuilder::new()
            .check_positive(k, "strike")
            .check_finite(k, "strike")
            .check_positive(t, "time")
            .check_finite(t, "time")
            .check_positive(sigma, "volatility")
            .check_finite(sigma, "volatility")
            .build()
    }

    /// Validate price array
    fn validate_price_array(&self, prices: &[f64], price_type: &str) -> QuantForgeResult<()> {
        let mut builder = ValidationBuilder::new();
        builder.check_array_positive(prices, price_type);
        builder.check_array_finite(prices, price_type);
        builder.build()
    }
}

/// Batch processor with dividend yield support
pub trait BatchProcessorWithDividend: BatchProcessor {
    type ParamsWithDividend;

    /// Create parameters with dividend yield
    fn create_params_with_dividend(
        &self,
        price: f64,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
    ) -> Self::ParamsWithDividend;

    /// Process single value with dividend
    fn process_single_with_dividend(&self, params: &Self::ParamsWithDividend) -> Self::Output;

    /// Process batch with dividend yield
    #[allow(clippy::too_many_arguments)]
    fn process_batch_with_dividend<'py>(
        &self,
        py: Python<'py>,
        prices: PyReadonlyArray1<f64>,
        k: f64,
        t: f64,
        r: f64,
        q: f64,
        sigma: f64,
        price_type: &str,
    ) -> PyResult<Bound<'py, PyArray1<f64>>>
    where
        Self::Output: Into<f64> + Send,
        Self::ParamsWithDividend: Send,
    {
        self.validate_common_params(k, t, sigma)
            .map_err(PyErr::from)?;
        self.validate_dividend_params(q).map_err(PyErr::from)?;

        let prices_slice = prices.as_slice()?;
        self.validate_price_array(prices_slice, price_type)
            .map_err(PyErr::from)?;

        let len = prices_slice.len();
        // SAFETY: PyArray1::new_bound is safe under the following conditions:
        // 1. `py` is a valid GIL token obtained from the function parameter
        // 2. `len` is the validated size from the input array
        // 3. `false` flag ensures the array is properly initialized with zeros
        // 4. No other references to this memory exist yet (newly allocated)
        let output = unsafe { PyArray1::<f64>::new_bound(py, len, false) };

        // Process without GIL release for now (safety issue with mutable array)
        // SAFETY: as_slice_mut() is safe under the following conditions:
        // 1. `output` is a newly created array owned by this function
        // 2. No other threads can access this array (GIL is held)
        // 3. No aliasing exists (this is the only mutable reference)
        // 4. The slice lifetime is bounded by the array's lifetime
        let output_slice = unsafe { output.as_slice_mut()? };

        // Use consistent chunking strategy
        prices_slice
            .chunks(CHUNK_SIZE_L1)
            .zip(output_slice.chunks_mut(CHUNK_SIZE_L1))
            .for_each(|(price_chunk, out_chunk)| {
                for (i, &price) in price_chunk.iter().enumerate() {
                    let params = self.create_params_with_dividend(price, k, t, r, q, sigma);
                    out_chunk[i] = self.process_single_with_dividend(&params).into();
                }
            });

        Ok(output)
    }

    /// Validate dividend parameters
    fn validate_dividend_params(&self, q: f64) -> QuantForgeResult<()> {
        ValidationBuilder::new()
            .check_finite(q, "dividend_yield")
            .build()
    }
}

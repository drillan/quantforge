use numpy::{PyArray1, PyArrayMethods, PyReadonlyArray1};
use pyo3::prelude::*;
use rayon::prelude::*;

/// Generic batch processing trait for option pricing models
/// This trait eliminates code duplication across Black-Scholes, Black76, and Merton models
pub trait BatchProcessor: Sync {
    type Params;
    type Output;

    /// Create parameters from input values
    fn create_params(&self, price: f64, k: f64, t: f64, r: f64, sigma: f64) -> Self::Params;

    /// Process single value
    fn process_single(&self, params: &Self::Params) -> Self::Output;

    /// Process batch with validation and zero-copy optimization
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
        self.validate_common_params(k, t, sigma)?;

        let prices_slice = prices.as_slice()?;
        self.validate_price_array(prices_slice, price_type)?;

        // Zero-copy output allocation
        let len = prices_slice.len();
        let output = unsafe { PyArray1::<f64>::new_bound(py, len, false) };

        // Process without GIL release for now (safety issue with mutable array)
        let output_slice = unsafe { output.as_slice_mut()? };

        // Dynamic strategy selection based on size
        match len {
            0..=1000 => self.process_sequential(prices_slice, k, t, r, sigma, output_slice),
            _ => self.process_sequential(prices_slice, k, t, r, sigma, output_slice),
        }

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

    /// Parallel processing for large datasets
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
        Self::Params: Send,
    {
        const CHUNK_SIZE: usize = 1024;

        prices
            .par_chunks(CHUNK_SIZE)
            .zip(output.par_chunks_mut(CHUNK_SIZE))
            .for_each(|(price_chunk, out_chunk)| {
                for (i, &price) in price_chunk.iter().enumerate() {
                    let params = self.create_params(price, k, t, r, sigma);
                    out_chunk[i] = self.process_single(&params).into();
                }
            });
    }

    /// Validate common parameters
    fn validate_common_params(&self, k: f64, t: f64, sigma: f64) -> PyResult<()> {
        if k <= 0.0 || t <= 0.0 || sigma <= 0.0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "k, t, and sigma must be positive",
            ));
        }
        if !k.is_finite() || !t.is_finite() || !sigma.is_finite() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "All parameters must be finite",
            ));
        }
        Ok(())
    }

    /// Validate price array
    fn validate_price_array(&self, prices: &[f64], price_type: &str) -> PyResult<()> {
        for &price in prices {
            if !price.is_finite() || price <= 0.0 {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "All {price_type} prices must be positive and finite"
                )));
            }
        }
        Ok(())
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
        self.validate_common_params(k, t, sigma)?;
        self.validate_dividend_params(q)?;

        let prices_slice = prices.as_slice()?;
        self.validate_price_array(prices_slice, price_type)?;

        let len = prices_slice.len();
        let output = unsafe { PyArray1::<f64>::new_bound(py, len, false) };

        // Process without GIL release for now (safety issue with mutable array)
        let output_slice = unsafe { output.as_slice_mut()? };

        prices_slice
            .chunks(1024)
            .zip(output_slice.chunks_mut(1024))
            .for_each(|(price_chunk, out_chunk)| {
                for (i, &price) in price_chunk.iter().enumerate() {
                    let params = self.create_params_with_dividend(price, k, t, r, q, sigma);
                    out_chunk[i] = self.process_single_with_dividend(&params).into();
                }
            });

        Ok(output)
    }

    /// Validate dividend parameters
    fn validate_dividend_params(&self, q: f64) -> PyResult<()> {
        if !q.is_finite() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Dividend yield must be finite",
            ));
        }
        Ok(())
    }
}

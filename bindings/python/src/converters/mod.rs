//! Type conversion utilities between Python and Rust

use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

pub mod array;
pub mod broadcast;

pub use array::ArrayLike;
pub use broadcast::BroadcastIterator;

/// Helper to validate and extract array data with zero-copy when possible
#[allow(dead_code)]
pub fn extract_array_data<'py>(array: &'py PyReadonlyArray1<'py, f64>) -> PyResult<&'py [f64]> {
    array.as_slice().map_err(|e| {
        use pyo3::exceptions::PyValueError;
        PyValueError::new_err(format!("Array is not contiguous: {e}"))
    })
}

/// Create a new PyArray1 from Vec with zero-copy transfer
#[allow(dead_code)]
pub fn create_output_array<'py>(
    py: Python<'py>,
    data: Vec<f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    Ok(PyArray1::from_vec_bound(py, data))
}

/// Create a new uninitialized PyArray1 for output
///
/// SAFETY: The caller must ensure the array is fully initialized before returning to Python
#[allow(dead_code)]
pub unsafe fn create_uninitialized_array<'py>(
    py: Python<'py>,
    len: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    Ok(PyArray1::<f64>::new_bound(py, len, false))
}

//! Array-like type for flexible input handling

use numpy::{PyArray1, PyArrayMethods, PyReadonlyArray1};
use pyo3::prelude::*;

/// A flexible array-like input that can be scalar or array
pub enum ArrayLike<'py> {
    Scalar(f64),
    Array(PyReadonlyArray1<'py, f64>),
}

impl<'py> FromPyObject<'py> for ArrayLike<'py> {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        // First try to extract as a scalar
        if let Ok(scalar) = ob.extract::<f64>() {
            return Ok(ArrayLike::Scalar(scalar));
        }

        // Try to extract as a numpy array
        if let Ok(array) = ob.extract::<PyReadonlyArray1<'py, f64>>() {
            return Ok(ArrayLike::Array(array));
        }

        // Try to convert Python list to numpy array
        if let Ok(list) = ob.extract::<Vec<f64>>() {
            let py = ob.py();
            let array = PyArray1::from_vec_bound(py, list);
            let readonly = array.readonly();
            return Ok(ArrayLike::Array(readonly));
        }

        // Try integer scalar (convert to float)
        if let Ok(int_val) = ob.extract::<i64>() {
            return Ok(ArrayLike::Scalar(int_val as f64));
        }

        // Try boolean (convert to 0.0 or 1.0)
        if let Ok(bool_val) = ob.extract::<bool>() {
            return Ok(ArrayLike::Scalar(if bool_val { 1.0 } else { 0.0 }));
        }

        Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(format!(
            "Cannot convert {ob} to ArrayLike. Expected float, int, bool, list, or numpy array."
        )))
    }
}

impl<'py> ArrayLike<'py> {
    /// Get the length of the array (1 for scalar)
    pub fn len(&self) -> usize {
        match self {
            ArrayLike::Scalar(_) => 1,
            ArrayLike::Array(arr) => arr.len().unwrap_or(0),
        }
    }

    /// Check if empty
    #[allow(dead_code)]
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Convert to Vec
    pub fn to_vec(&self) -> PyResult<Vec<f64>> {
        match self {
            ArrayLike::Scalar(val) => Ok(vec![*val]),
            ArrayLike::Array(arr) => {
                // Handle both contiguous and non-contiguous arrays
                if let Ok(slice) = arr.as_slice() {
                    Ok(slice.to_vec())
                } else {
                    // Non-contiguous array - use to_vec() method
                    arr.to_vec().map_err(|e| {
                        pyo3::exceptions::PyValueError::new_err(format!(
                            "Failed to convert array: {e}"
                        ))
                    })
                }
            }
        }
    }

    /// Get as slice (only for array)
    #[allow(dead_code)]
    pub fn as_slice(&self) -> Option<&[f64]> {
        match self {
            ArrayLike::Scalar(_) => None,
            ArrayLike::Array(arr) => arr.as_slice().ok(),
        }
    }

    /// Get scalar value (only if scalar or single-element array)
    #[allow(dead_code)]
    pub fn as_scalar(&self) -> Option<f64> {
        match self {
            ArrayLike::Scalar(val) => Some(*val),
            ArrayLike::Array(arr) => {
                if arr.len().unwrap_or(0) == 1 {
                    arr.as_slice().ok().and_then(|s| s.first().copied())
                } else {
                    None
                }
            }
        }
    }
}

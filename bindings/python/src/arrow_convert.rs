//! NumPy ↔ Arrow conversion utilities for zero-copy operations

use arrow::array::{ArrayRef, Float64Array};
use arrow::error::ArrowError;
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;

/// Convert NumPy array to Arrow Float64Array
///
/// This performs a copy as Arrow requires owned data,
/// but the copy is optimized and happens without Python GIL
pub fn numpy_to_arrow(arr: PyReadonlyArray1<f64>) -> Result<Float64Array, ArrowError> {
    // Get the slice from NumPy array (zero-copy view)
    let slice = arr
        .as_slice()
        .map_err(|e| ArrowError::InvalidArgumentError(format!("Failed to get slice: {e}")))?;

    // Create Arrow array from slice (requires copy for ownership)
    Ok(Float64Array::from(slice.to_vec()))
}

/// Convert Arrow Float64Array to NumPy array
///
/// This creates a new NumPy array with the values from Arrow
pub fn arrow_to_numpy<'py>(py: Python<'py>, arr: &Float64Array) -> Bound<'py, PyArray1<f64>> {
    // Extract values from Arrow array
    let vec: Vec<f64> = (0..arr.len()).map(|i| arr.value(i)).collect();

    // Create NumPy array
    PyArray1::from_vec(py, vec)
}

/// Convert ArrayRef to NumPy array
///
/// Handles downcasting from ArrayRef to Float64Array
pub fn arrayref_to_numpy<'py>(
    py: Python<'py>,
    arr: ArrayRef,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let float_array = arr
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| pyo3::exceptions::PyTypeError::new_err("Expected Float64Array"))?;

    Ok(arrow_to_numpy(py, float_array))
}

/// Broadcast arrays to the same length
///
/// Handles scalar (length 1) broadcasting to match target length
pub fn broadcast_to_length(
    arr: PyReadonlyArray1<f64>,
    target_len: usize,
) -> Result<Float64Array, ArrowError> {
    let arr_len = arr.len().map_err(|e| {
        ArrowError::InvalidArgumentError(format!("Failed to get array length: {e}"))
    })?;

    if arr_len == 1 {
        // Scalar broadcast: repeat the single value
        let slice = arr
            .as_slice()
            .map_err(|e| ArrowError::InvalidArgumentError(format!("Failed to get slice: {e}")))?;
        let value = slice[0];
        Ok(Float64Array::from(vec![value; target_len]))
    } else if arr_len == target_len {
        // Same length: direct conversion
        numpy_to_arrow(arr)
    } else {
        // Shape mismatch
        Err(ArrowError::InvalidArgumentError(format!(
            "Cannot broadcast array of length {arr_len} to length {target_len}"
        )))
    }
}

/// Find the maximum length among multiple arrays for broadcasting
pub fn find_broadcast_length(arrays: &[&PyReadonlyArray1<f64>]) -> Result<usize, ArrowError> {
    let mut max_len = 1;

    for arr in arrays {
        let len = arr.len().map_err(|e| {
            ArrowError::InvalidArgumentError(format!("Failed to get array length: {e}"))
        })?;
        if len > 1 {
            if max_len > 1 && len != max_len {
                return Err(ArrowError::InvalidArgumentError(
                    "Shape mismatch: arrays have incompatible lengths for broadcasting".to_string(),
                ));
            }
            max_len = max_len.max(len);
        }
    }

    Ok(max_len)
}

/// Check if all arrays have the same length
///
/// Returns true if all arrays have identical length (not considering scalar broadcasting)
pub fn all_same_length(arrays: &[&PyReadonlyArray1<f64>]) -> bool {
    if arrays.is_empty() {
        return true;
    }

    let first_len = arrays[0].len().unwrap_or(0);
    arrays.iter().all(|arr| arr.len().unwrap_or(0) == first_len)
}

/// Convert NumPy array to Arrow Float64Array without broadcasting
///
/// Direct conversion for arrays that are already the correct length
/// This is faster than broadcast_to_length when no broadcasting is needed
pub fn numpy_to_arrow_direct(arr: PyReadonlyArray1<f64>) -> Result<Float64Array, ArrowError> {
    // Get the slice from NumPy array (zero-copy view)
    let slice = arr
        .as_slice()
        .map_err(|e| ArrowError::InvalidArgumentError(format!("Failed to get slice: {e}")))?;

    // Create Arrow array from slice (requires copy for ownership)
    Ok(Float64Array::from(slice.to_vec()))
}

/// Broadcast multiple arrays to the same length
pub fn broadcast_arrays(
    arrays: Vec<PyReadonlyArray1<f64>>,
) -> Result<Vec<Float64Array>, ArrowError> {
    // Find target length
    let refs: Vec<&PyReadonlyArray1<f64>> = arrays.iter().collect();
    let target_len = find_broadcast_length(&refs)?;

    // Broadcast each array
    let mut result = Vec::with_capacity(arrays.len());
    for arr in arrays {
        result.push(broadcast_to_length(arr, target_len)?);
    }

    Ok(result)
}

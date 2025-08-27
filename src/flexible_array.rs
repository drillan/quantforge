//! Flexible input type for PyO3 bindings
//!
//! This module provides a FlexibleArray type that can accept scalar values,
//! Python lists, or NumPy arrays, providing a unified interface for batch operations.

use crate::broadcast::ArrayLike;
use crate::error::QuantForgeError;
use numpy::PyReadonlyArray1;
use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;

/// A flexible input type that can accept various Python types
pub enum FlexibleArray<'py> {
    /// A single scalar value
    Scalar(f64),
    /// A Python list of values
    List(Vec<f64>),
    /// A NumPy array (zero-copy when possible)
    NumpyArray(PyReadonlyArray1<'py, f64>),
}

impl<'py> FromPyObject<'py> for FlexibleArray<'py> {
    fn extract_bound(ob: &Bound<'py, PyAny>) -> PyResult<Self> {
        // 1. Try to extract as a scalar float
        if let Ok(val) = ob.extract::<f64>() {
            return Ok(FlexibleArray::Scalar(val));
        }

        // 2. Try to extract as a NumPy array
        if let Ok(arr) = ob.extract::<PyReadonlyArray1<f64>>() {
            return Ok(FlexibleArray::NumpyArray(arr));
        }

        // 3. Try to extract as a Python list
        if let Ok(list) = ob.extract::<Vec<f64>>() {
            return Ok(FlexibleArray::List(list));
        }

        // 4. Try to extract as an integer and convert to float
        if let Ok(val) = ob.extract::<i64>() {
            return Ok(FlexibleArray::Scalar(val as f64));
        }

        Err(PyTypeError::new_err(
            "Expected float, int, list of numbers, or numpy array",
        ))
    }
}

impl<'py> FlexibleArray<'py> {
    /// Convert to ArrayLike for use with broadcasting operations
    pub fn to_array_like(&self) -> Result<ArrayLike<'_>, QuantForgeError> {
        match self {
            FlexibleArray::Scalar(val) => {
                if !val.is_finite() {
                    return Err(QuantForgeError::InvalidInput(
                        "All values must be finite".to_string(),
                    ));
                }
                Ok(ArrayLike::Scalar(*val))
            }
            FlexibleArray::List(vec) => {
                // Validate all values are finite
                for &val in vec.iter() {
                    if !val.is_finite() {
                        return Err(QuantForgeError::InvalidInput(
                            "All values must be finite".to_string(),
                        ));
                    }
                }
                Ok(ArrayLike::Array(vec))
            }
            FlexibleArray::NumpyArray(arr) => {
                let slice = arr.as_slice().map_err(|e| {
                    QuantForgeError::InvalidInput(format!("Failed to get array slice: {e}"))
                })?;

                // Validate all values are finite
                for &val in slice.iter() {
                    if !val.is_finite() {
                        return Err(QuantForgeError::InvalidInput(
                            "All values must be finite".to_string(),
                        ));
                    }
                }

                // Single element arrays are treated as scalars for broadcasting
                if slice.len() == 1 {
                    Ok(ArrayLike::Scalar(slice[0]))
                } else {
                    Ok(ArrayLike::Array(slice))
                }
            }
        }
    }

    /// Get the length of the array (1 for scalar)
    pub fn len(&self) -> usize {
        match self {
            FlexibleArray::Scalar(_) => 1,
            FlexibleArray::List(vec) => vec.len(),
            FlexibleArray::NumpyArray(arr) => arr.len().unwrap_or(0),
        }
    }

    /// Check if the array is empty (always false for scalar)
    pub fn is_empty(&self) -> bool {
        match self {
            FlexibleArray::Scalar(_) => false,
            FlexibleArray::List(vec) => vec.is_empty(),
            FlexibleArray::NumpyArray(arr) => arr.len().unwrap_or(0) == 0,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scalar_conversion() {
        let scalar = FlexibleArray::Scalar(100.0);
        let array_like = scalar.to_array_like().unwrap();
        match array_like {
            ArrayLike::Scalar(val) => assert_eq!(val, 100.0),
            _ => panic!("Expected scalar"),
        }
    }

    #[test]
    fn test_list_conversion() {
        let list = FlexibleArray::List(vec![95.0, 100.0, 105.0]);
        let array_like = list.to_array_like().unwrap();
        match array_like {
            ArrayLike::Array(arr) => assert_eq!(arr, &[95.0, 100.0, 105.0]),
            _ => panic!("Expected array"),
        }
    }

    #[test]
    fn test_invalid_values() {
        let scalar = FlexibleArray::Scalar(f64::NAN);
        assert!(scalar.to_array_like().is_err());

        let list = FlexibleArray::List(vec![1.0, f64::INFINITY, 3.0]);
        assert!(list.to_array_like().is_err());
    }
}

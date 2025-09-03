//! Utility functions for PyO3 bindings

use arrow::array::Float64Array;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3_arrow::PyArray;
use std::sync::Arc;

/// Convert PyAny to Arrow array (scalars become length-1 arrays for broadcasting)
///
/// # Arguments
/// * `py` - Python interpreter
/// * `value` - Python object (float, numpy array, or arrow array)
///
/// # Returns
/// * `PyArray` - Arrow array (original or converted)
///
/// # Errors
/// * Returns error if value cannot be converted to arrow array
pub fn pyany_to_arrow(_py: Python, value: &Bound<'_, PyAny>) -> PyResult<PyArray> {
    // 1. If already an Arrow array, check if it needs conversion to Float64
    if let Ok(array) = value.extract::<PyArray>() {
        let array_ref = array.as_ref();

        // Check if the array is already Float64
        if array_ref.data_type() == &arrow::datatypes::DataType::Float64 {
            return Ok(array);
        }

        // If it's Int64, convert to Float64
        if array_ref.data_type() == &arrow::datatypes::DataType::Int64 {
            use arrow::compute::cast;

            let casted = cast(array_ref, &arrow::datatypes::DataType::Float64).map_err(|e| {
                PyValueError::new_err(format!("Failed to cast array to Float64: {e}"))
            })?;
            let array_ref = casted;
            return Ok(PyArray::from_array_ref(array_ref));
        }

        // For other types, try to cast
        use arrow::compute::cast;
        let casted = cast(array_ref, &arrow::datatypes::DataType::Float64)
            .map_err(|e| PyValueError::new_err(format!("Failed to cast array to Float64: {e}")))?;
        let array_ref = casted;
        return Ok(PyArray::from_array_ref(array_ref));
    }

    // 2. Check if it has a tolist method (likely a NumPy array)
    if value.hasattr("tolist")? {
        // Convert NumPy array to Python list, then to Arrow array
        let py_list = value.call_method0("tolist")?;
        if let Ok(vec) = py_list.extract::<Vec<f64>>() {
            let arrow_array = Float64Array::from(vec);
            let array_ref = Arc::new(arrow_array);
            return Ok(PyArray::from_array_ref(array_ref));
        }
        // Try single value from 1-element array
        if let Ok(scalar) = py_list.extract::<f64>() {
            let arrow_array = Float64Array::from(vec![scalar]);
            let array_ref = Arc::new(arrow_array);
            return Ok(PyArray::from_array_ref(array_ref));
        }
    }

    // 3. If scalar (float), convert to length-1 array for broadcasting
    if let Ok(scalar) = value.extract::<f64>() {
        let arrow_array = Float64Array::from(vec![scalar]);
        let array_ref = Arc::new(arrow_array);
        return Ok(PyArray::from_array_ref(array_ref));
    }

    // 4. Otherwise, return clear error message
    Err(PyValueError::new_err(format!(
        "Expected float, numpy array, or arrow array, got {}",
        value.get_type().name()?
    )))
}

// Tests disabled due to PyO3 API compatibility issues
// The functionality is tested via Python integration tests

//! Error handling for Python bindings - Arrow-native version

use arrow::error::ArrowError;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use pyo3::prelude::*;

/// Convert ArrowError to Python exception
pub fn arrow_to_py_err(err: ArrowError) -> PyErr {
    match err {
        ArrowError::InvalidArgumentError(msg) => PyValueError::new_err(msg),
        ArrowError::ComputeError(msg) => PyRuntimeError::new_err(format!("Compute error: {msg}")),
        ArrowError::DivideByZero => PyValueError::new_err("Division by zero"),
        ArrowError::MemoryError(msg) => PyRuntimeError::new_err(format!("Memory error: {msg}")),
        ArrowError::IoError(msg, _) => PyRuntimeError::new_err(format!("IO error: {msg}")),
        ArrowError::ExternalError(e) => PyRuntimeError::new_err(format!("External error: {e}")),
        ArrowError::NotYetImplemented(msg) => pyo3::exceptions::PyNotImplementedError::new_err(msg),
        _ => PyRuntimeError::new_err(format!("Arrow error: {err}")),
    }
}

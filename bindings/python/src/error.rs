//! Error handling for Python bindings - Arrow-native version

use arrow::error::ArrowError;
use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use quantforge_core::error::QuantForgeError;

/// Convert QuantForgeError to appropriate Python exception
pub fn to_py_err(err: QuantForgeError) -> PyErr {
    match err {
        QuantForgeError::Arrow(arrow_err) => arrow_to_py_err(arrow_err),
        QuantForgeError::InvalidInput(msg) => PyValueError::new_err(msg),
        QuantForgeError::CalculationError(msg) => PyRuntimeError::new_err(msg),
        QuantForgeError::ConvergenceError(msg) => PyRuntimeError::new_err(msg),
        QuantForgeError::OutOfBounds(msg) => PyValueError::new_err(msg),
        QuantForgeError::ShapeMismatch { expected, got } => {
            PyTypeError::new_err(format!("Shape mismatch: expected {expected}, got {got}"))
        }
        QuantForgeError::InvalidParameter {
            name,
            value,
            reason,
        } => PyValueError::new_err(format!("Invalid parameter {name}: {value} ({reason})")),
        QuantForgeError::NumericalInstability => {
            PyRuntimeError::new_err("Numerical instability detected")
        }
        QuantForgeError::ConvergenceFailed(iters) => {
            PyRuntimeError::new_err(format!("Convergence failed after {iters} iterations"))
        }
        QuantForgeError::BracketingFailed => {
            PyRuntimeError::new_err("Failed to bracket root for solver")
        }
    }
}

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

/// Generic error conversion trait
pub trait ToPyErr {
    fn to_py_err(self) -> PyErr;
}

impl ToPyErr for QuantForgeError {
    fn to_py_err(self) -> PyErr {
        to_py_err(self)
    }
}

impl ToPyErr for ArrowError {
    fn to_py_err(self) -> PyErr {
        arrow_to_py_err(self)
    }
}

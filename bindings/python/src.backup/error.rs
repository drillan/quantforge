//! Error handling for Python bindings

use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use quantforge_core::error::QuantForgeError;

/// Convert QuantForgeError to appropriate Python exception
pub fn to_py_err(err: QuantForgeError) -> PyErr {
    match err {
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

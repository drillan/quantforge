//! Core error types with Arrow integration

use arrow::error::ArrowError;
use thiserror::Error;

/// Core error type for QuantForge
#[derive(Error, Debug)]
pub enum QuantForgeError {
    #[error("Arrow computation error: {0}")]
    Arrow(#[from] ArrowError),

    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Calculation error: {0}")]
    CalculationError(String),

    #[error("Convergence error: {0}")]
    ConvergenceError(String),

    #[error("Out of bounds: {0}")]
    OutOfBounds(String),

    #[error("Shape mismatch: expected {expected}, got {got}")]
    ShapeMismatch { expected: String, got: String },

    #[error("Invalid parameter: {name} = {value}, {reason}")]
    InvalidParameter {
        name: String,
        value: String,
        reason: String,
    },

    #[error("Numerical instability")]
    NumericalInstability,

    #[error("Convergence failed after {0} iterations")]
    ConvergenceFailed(usize),

    #[error("Bracketing failed")]
    BracketingFailed,
}

/// Result type alias for QuantForge operations
pub type QuantForgeResult<T> = Result<T, QuantForgeError>;

/// Validation builder for structured parameter validation
pub struct ValidationBuilder {
    errors: Vec<String>,
}

impl ValidationBuilder {
    pub fn new() -> Self {
        Self { errors: Vec::new() }
    }

    /// 汎用的な検証メソッド
    #[inline(always)]
    fn check_with_condition(
        mut self,
        value: f64,
        name: &str,
        condition: impl FnOnce(f64) -> bool,
        error_msg: &str,
    ) -> Self {
        if !value.is_finite() {
            self.errors
                .push(format!("{name} must be finite, got {value}"));
        } else if !condition(value) {
            self.errors.push(format!("{name} {error_msg}, got {value}"));
        }
        self
    }

    pub fn check_positive(self, value: f64, name: &str) -> Self {
        self.check_with_condition(value, name, |v| v > 0.0, "must be positive")
    }

    pub fn check_non_negative(self, value: f64, name: &str) -> Self {
        self.check_with_condition(value, name, |v| v >= 0.0, "must be non-negative")
    }

    pub fn check_finite(mut self, value: f64, name: &str) -> Self {
        if !value.is_finite() {
            self.errors
                .push(format!("{name} must be finite, got {value}"));
        }
        self
    }

    pub fn check_range(self, value: f64, min: f64, max: f64, name: &str) -> Self {
        self.check_with_condition(
            value,
            name,
            |v| v >= min && v <= max,
            &format!("must be between {min} and {max}"),
        )
    }

    pub fn build(self) -> QuantForgeResult<()> {
        if self.errors.is_empty() {
            Ok(())
        } else {
            Err(QuantForgeError::InvalidInput(self.errors.join("; ")))
        }
    }
}

impl Default for ValidationBuilder {
    fn default() -> Self {
        Self::new()
    }
}

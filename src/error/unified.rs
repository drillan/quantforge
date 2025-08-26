use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use thiserror::Error;

/// Unified error type for all QuantForge operations
#[derive(Error, Debug, Clone)]
pub enum QuantForgeError {
    #[error("Validation error: {context}")]
    ValidationError { context: String },

    #[error("Numerical error: {details}")]
    NumericalError { details: String },

    #[error("Convergence error after {iterations} iterations: {details}")]
    ConvergenceError { iterations: u32, details: String },

    #[error("Dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },

    #[error("Value out of range: {value} not in [{min}, {max}]")]
    OutOfRange { value: f64, min: f64, max: f64 },

    #[error("Invalid parameter: {param} = {value}, {reason}")]
    InvalidParameter {
        param: String,
        value: String,
        reason: String,
    },

    #[error("Overflow error: {context}")]
    OverflowError { context: String },

    #[error("Underflow error: {context}")]
    UnderflowError { context: String },

    #[error("Not finite: {param} = {value}")]
    NotFinite { param: String, value: f64 },

    #[error("Numerical instability detected")]
    NumericalInstability,

    #[error("Convergence failed after {0} iterations")]
    ConvergenceFailed(usize),

    #[error("Bracketing failed")]
    BracketingFailed,

    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Invalid numeric value")]
    InvalidNumericValue,

    #[error("Invalid spot price: {0}")]
    InvalidSpotPrice(String),

    #[error("Invalid strike price: {0}")]
    InvalidStrikePrice(String),

    #[error("Invalid time: {0}")]
    InvalidTime(String),

    #[error("Invalid market price: {0}")]
    InvalidMarketPrice(String),

    #[error("No-arbitrage condition breach: {0}")]
    NoArbitrageBreach(String),

    #[error("Invalid volatility: {0}")]
    InvalidVolatility(f64),
}

/// Result type alias for QuantForge operations
pub type QuantForgeResult<T> = Result<T, QuantForgeError>;

impl From<QuantForgeError> for PyErr {
    fn from(err: QuantForgeError) -> PyErr {
        match err {
            QuantForgeError::ValidationError { .. }
            | QuantForgeError::InvalidParameter { .. }
            | QuantForgeError::NotFinite { .. }
            | QuantForgeError::OutOfRange { .. }
            | QuantForgeError::InvalidInput(_)
            | QuantForgeError::InvalidNumericValue
            | QuantForgeError::InvalidSpotPrice(_)
            | QuantForgeError::InvalidStrikePrice(_)
            | QuantForgeError::InvalidTime(_)
            | QuantForgeError::InvalidMarketPrice(_)
            | QuantForgeError::NoArbitrageBreach(_)
            | QuantForgeError::InvalidVolatility(_) => PyValueError::new_err(err.to_string()),

            QuantForgeError::DimensionMismatch { .. } => PyTypeError::new_err(err.to_string()),

            QuantForgeError::NumericalError { .. }
            | QuantForgeError::ConvergenceError { .. }
            | QuantForgeError::OverflowError { .. }
            | QuantForgeError::UnderflowError { .. }
            | QuantForgeError::NumericalInstability
            | QuantForgeError::ConvergenceFailed(_)
            | QuantForgeError::BracketingFailed => PyRuntimeError::new_err(err.to_string()),
        }
    }
}

/// Validation builder for fluent error construction
pub struct ValidationBuilder {
    errors: Vec<String>,
}

impl Default for ValidationBuilder {
    fn default() -> Self {
        Self::new()
    }
}

impl ValidationBuilder {
    pub fn new() -> Self {
        Self { errors: Vec::new() }
    }

    pub fn check_positive(&mut self, value: f64, name: &str) -> &mut Self {
        if value <= 0.0 {
            self.errors
                .push(format!("{name} must be positive, got {value}"));
        }
        self
    }

    pub fn check_non_negative(&mut self, value: f64, name: &str) -> &mut Self {
        if value < 0.0 {
            self.errors
                .push(format!("{name} must be non-negative, got {value}"));
        }
        self
    }

    pub fn check_finite(&mut self, value: f64, name: &str) -> &mut Self {
        if !value.is_finite() {
            self.errors
                .push(format!("{name} must be finite, got {value}"));
        }
        self
    }

    pub fn check_range(&mut self, value: f64, min: f64, max: f64, name: &str) -> &mut Self {
        if value < min || value > max {
            self.errors.push(format!(
                "{name} must be in range [{min}, {max}], got {value}"
            ));
        }
        self
    }

    pub fn check_array_positive(&mut self, values: &[f64], name: &str) -> &mut Self {
        for (i, &val) in values.iter().enumerate() {
            if val <= 0.0 {
                self.errors
                    .push(format!("{name}[{i}] must be positive, got {val}"));
                break;
            }
        }
        self
    }

    pub fn check_array_finite(&mut self, values: &[f64], name: &str) -> &mut Self {
        for (i, &val) in values.iter().enumerate() {
            if !val.is_finite() {
                self.errors
                    .push(format!("{name}[{i}] must be finite, got {val}"));
                break;
            }
        }
        self
    }

    pub fn build(&self) -> QuantForgeResult<()> {
        if self.errors.is_empty() {
            Ok(())
        } else {
            Err(QuantForgeError::ValidationError {
                context: self.errors.join("; "),
            })
        }
    }
}

/// Common validation functions
pub fn validate_option_params(s: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<()> {
    ValidationBuilder::new()
        .check_positive(s, "spot")
        .check_finite(s, "spot")
        .check_positive(k, "strike")
        .check_finite(k, "strike")
        .check_positive(t, "time")
        .check_finite(t, "time")
        .check_finite(r, "rate")
        .check_positive(sigma, "volatility")
        .check_finite(sigma, "volatility")
        .build()
}

pub fn validate_forward_params(f: f64, k: f64, t: f64, r: f64, sigma: f64) -> QuantForgeResult<()> {
    ValidationBuilder::new()
        .check_positive(f, "forward")
        .check_finite(f, "forward")
        .check_positive(k, "strike")
        .check_finite(k, "strike")
        .check_positive(t, "time")
        .check_finite(t, "time")
        .check_finite(r, "rate")
        .check_positive(sigma, "volatility")
        .check_finite(sigma, "volatility")
        .build()
}

pub fn validate_dividend_params(q: f64) -> QuantForgeResult<()> {
    ValidationBuilder::new()
        .check_finite(q, "dividend_yield")
        .build()
}

pub fn validate_price_for_iv(
    price: f64,
    is_call: bool,
    s: f64,
    k: f64,
    r: f64,
    t: f64,
) -> QuantForgeResult<()> {
    ValidationBuilder::new()
        .check_positive(price, "option_price")
        .check_finite(price, "option_price")
        .build()?;

    // Check arbitrage bounds
    let discount = (-r * t).exp();
    let intrinsic = if is_call {
        (s - k * discount).max(0.0)
    } else {
        (k * discount - s).max(0.0)
    };

    let max_value = if is_call { s } else { k * discount };

    if price < intrinsic {
        return Err(QuantForgeError::OutOfRange {
            value: price,
            min: intrinsic,
            max: max_value,
        });
    }

    if price > max_value {
        return Err(QuantForgeError::OutOfRange {
            value: price,
            min: intrinsic,
            max: max_value,
        });
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validation_builder() {
        let result = ValidationBuilder::new()
            .check_positive(-1.0, "test_value")
            .build();
        assert!(result.is_err());

        let result = ValidationBuilder::new()
            .check_positive(1.0, "test_value")
            .check_finite(f64::NAN, "nan_value")
            .build();
        assert!(result.is_err());

        let result = ValidationBuilder::new()
            .check_positive(1.0, "test_value")
            .check_finite(1.0, "finite_value")
            .build();
        assert!(result.is_ok());
    }

    #[test]
    fn test_error_conversion() {
        let err = QuantForgeError::ValidationError {
            context: "test error".to_string(),
        };
        let py_err: PyErr = err.into();
        Python::with_gil(|py| {
            assert!(py_err.is_instance_of::<PyValueError>(py));
        });
    }
}

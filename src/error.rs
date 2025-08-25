use thiserror::Error;

#[derive(Error, Debug)]
#[allow(clippy::enum_variant_names)]
pub enum QuantForgeError {
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Price must be positive, got {0}")]
    InvalidPrice(f64),

    #[error("Time to maturity must be positive, got {0}")]
    InvalidTime(f64),

    #[error("Volatility must be positive, got {0}")]
    InvalidVolatility(f64),

    #[error("Input contains NaN or infinite values")]
    InvalidNumericValue,
}

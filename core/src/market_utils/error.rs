//! Error types for market pricing utilities

use std::error::Error;
use std::fmt;

use crate::constants::PERCENTAGE_MULTIPLIER;

/// Errors that can occur during market data processing
#[derive(Debug, Clone, PartialEq)]
pub enum MarketDataError {
    /// Invalid price value
    InvalidPrice(String),

    /// Invalid quantity value
    InvalidQuantity(String),

    /// Spread exceeds configured threshold
    AbnormalSpread {
        /// Actual spread percentage
        spread: f64,
        /// Configured threshold
        threshold: f64,
    },

    /// Crossed spread (bid > ask)
    CrossedSpread {
        /// Bid price
        bid: f64,
        /// Ask price
        ask: f64,
    },

    /// Invalid configuration
    InvalidConfig(String),

    /// Array length mismatch for batch operations
    ArrayLengthMismatch {
        /// Expected length
        expected: usize,
        /// Actual length
        actual: usize,
    },
}

impl fmt::Display for MarketDataError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            MarketDataError::InvalidPrice(msg) => write!(f, "Invalid price: {msg}"),
            MarketDataError::InvalidQuantity(msg) => write!(f, "Invalid quantity: {msg}"),
            MarketDataError::AbnormalSpread { spread, threshold } => {
                write!(
                    f,
                    "Abnormal spread: {:.1}% exceeds threshold {:.1}%",
                    spread * PERCENTAGE_MULTIPLIER,
                    threshold * PERCENTAGE_MULTIPLIER
                )
            }
            MarketDataError::CrossedSpread { bid, ask } => {
                write!(f, "Crossed spread: bid={bid} > ask={ask}")
            }
            MarketDataError::InvalidConfig(msg) => write!(f, "Invalid configuration: {msg}"),
            MarketDataError::ArrayLengthMismatch { expected, actual } => {
                write!(
                    f,
                    "Array length mismatch: expected {expected}, got {actual}"
                )
            }
        }
    }
}

impl Error for MarketDataError {}

/// Result type for market data operations
pub type MarketDataResult<T> = Result<T, MarketDataError>;

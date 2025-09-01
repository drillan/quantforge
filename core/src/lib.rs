//! QuantForge Core - Arrow-native option pricing library
//!
//! This crate provides high-performance option pricing using Apache Arrow
//! for efficient vectorized computation.

pub mod compute;
pub mod constants;
pub mod error;
pub mod math;

// Re-export main computation modules
pub use compute::american;
pub use compute::black76;
pub use compute::black_scholes;
pub use compute::greeks;
pub use compute::merton;

// Re-export error types
pub use error::{QuantForgeError, QuantForgeResult};

// Re-export constants
pub use constants::*;

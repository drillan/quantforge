//! QuantForge Core - Arrow-native option pricing library
//!
//! This crate provides high-performance option pricing using Apache Arrow
//! for efficient vectorized computation.

pub mod compute;
pub mod math;
pub mod constants;
pub mod error;

// Re-export main computation modules
pub use compute::black_scholes;
pub use compute::black76;
pub use compute::merton;
pub use compute::american;
pub use compute::greeks;

// Re-export error types
pub use error::{QuantForgeError, QuantForgeResult};

// Re-export constants
pub use constants::*;
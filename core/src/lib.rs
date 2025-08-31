//! QuantForge Core - Pure Rust implementation
//!
//! This crate provides the core computational engine for QuantForge
//! without any Python dependencies.

pub mod constants;
pub mod error;
pub mod math;
pub mod models;
pub mod traits;

// Re-export commonly used items
pub use constants::*;
pub use error::{QuantForgeError, QuantForgeResult};

// Re-export models
pub use models::{
    american::American, black76::Black76, black_scholes::BlackScholes, merton::Merton,
};

// Re-export traits
pub use traits::{BatchProcessor, Greeks, OptionModel};

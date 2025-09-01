//! Arrow-native computation kernels for option pricing

pub mod american;
pub mod arrow_native;
pub mod black76;
pub mod black_scholes;
pub mod greeks;
pub mod merton;

// Re-export for convenience
pub use american::American;
pub use arrow_native::ArrowNativeCompute;
pub use black76::Black76;
pub use black_scholes::BlackScholes;
pub use greeks::calculate_greeks;
pub use merton::Merton;

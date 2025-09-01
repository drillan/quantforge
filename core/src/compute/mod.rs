//! Arrow-native computation kernels for option pricing

pub mod black_scholes;
pub mod black76;
pub mod merton;
pub mod american;
pub mod greeks;

// Re-export for convenience
pub use black_scholes::BlackScholes;
pub use black76::Black76;
pub use merton::Merton;
pub use american::American;
pub use greeks::calculate_greeks;
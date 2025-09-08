//! Mathematical functions optimized for Arrow arrays

pub mod black_scholes_math;
pub mod distributions;
pub mod fast_erf;

// Re-export commonly used functions
pub use black_scholes_math::{calculate_black76_d1_d2, calculate_d1, calculate_d1_d2, d1_to_d2};
pub use distributions::{norm_cdf_array, norm_cdf_scalar, norm_pdf_array, norm_pdf_scalar};
pub use fast_erf::{fast_erf, fast_norm_cdf, fast_norm_pdf};

//! Mathematical functions optimized for Arrow arrays

pub mod distributions;

// Re-export commonly used functions
pub use distributions::{norm_cdf_array, norm_cdf_scalar, norm_pdf_array, norm_pdf_scalar};

use thiserror::Error;

#[derive(Error, Debug)]
#[allow(clippy::enum_variant_names)]
pub enum QuantForgeError {
    #[error("Invalid input: {0}")]
    InvalidInput(String),

    #[error("Spot price must be positive, got {0}")]
    InvalidSpotPrice(f64),

    #[error("Strike price must be positive, got {0}")]
    InvalidStrikePrice(f64),

    #[error("Time to maturity must be positive, got {0}")]
    InvalidTime(f64),

    #[error("Volatility must be positive, got {0}")]
    InvalidVolatility(f64),

    #[error("Input contains NaN or infinite values")]
    InvalidNumericValue,

    // インプライドボラティリティ関連エラー
    #[error("Price violates no-arbitrage bounds")]
    NoArbitrageBreach,

    #[error("Failed to converge after {0} iterations")]
    ConvergenceFailed(usize),

    #[error("Invalid market price: {0}")]
    InvalidMarketPrice(f64),

    #[error("Numerical instability detected (Vega too small)")]
    NumericalInstability,

    #[error("Failed to find valid bracket for root finding")]
    BracketingFailed,
}

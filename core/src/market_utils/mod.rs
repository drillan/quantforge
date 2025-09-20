//! Market pricing utilities for calculating mid prices from bid/ask data
//!
//! This module provides functionality for:
//! - Simple and weighted mid price calculation
//! - Spread calculation and validation
//! - Handling of abnormal spreads common in options markets
//! - Batch processing with Arrow arrays (in batch module)

pub mod error;
pub mod pricing;
pub mod validation;

// Re-export main types
pub use error::{MarketDataError, MarketDataResult};
pub use pricing::{
    mid_price, mid_price_with_config, spread, spread_pct, weighted_mid_price,
    weighted_mid_price_with_config, AbnormalSpreadHandling, CrossedSpreadHandling,
    MarketPricingConfig,
};

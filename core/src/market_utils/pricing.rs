//! Market pricing calculations

use crate::constants::market::DEFAULT_ABNORMAL_SPREAD_THRESHOLD_PCT;
use crate::market_utils::validation::{
    calculate_spread_pct, is_abnormal_spread, is_crossed_spread,
};

/// Configuration for market pricing calculations
#[derive(Debug, Clone)]
pub struct MarketPricingConfig {
    /// Maximum spread as percentage of mid price (None = no check)
    pub max_spread_pct: Option<f64>,

    /// How to handle abnormal spreads
    pub abnormal_handling: AbnormalSpreadHandling,

    /// How to handle crossed spreads (bid > ask)
    pub crossed_handling: CrossedSpreadHandling,
}

/// How to handle abnormal spreads
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum AbnormalSpreadHandling {
    /// Return NaN (recommended default)
    ReturnNaN,

    /// Log warning and continue with calculation
    LogAndContinue,

    /// Return error (for strict processing)
    ReturnError,
}

/// How to handle crossed spreads
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CrossedSpreadHandling {
    /// Return NaN (default)
    ReturnNaN,

    /// Swap bid and ask, then continue
    SwapAndContinue,

    /// Return error
    ReturnError,
}

impl Default for MarketPricingConfig {
    fn default() -> Self {
        Self {
            max_spread_pct: Some(DEFAULT_ABNORMAL_SPREAD_THRESHOLD_PCT),
            abnormal_handling: AbnormalSpreadHandling::ReturnNaN,
            crossed_handling: CrossedSpreadHandling::ReturnNaN,
        }
    }
}

/// Calculate simple mid price with default configuration
#[inline]
pub fn mid_price(bid: f64, ask: f64) -> f64 {
    mid_price_with_config(bid, ask, &MarketPricingConfig::default())
}

/// Calculate simple mid price with custom configuration
pub fn mid_price_with_config(bid: f64, ask: f64, config: &MarketPricingConfig) -> f64 {
    // Basic validation
    if !bid.is_finite() || !ask.is_finite() || bid < 0.0 || ask < 0.0 {
        return f64::NAN;
    }

    // Check for crossed spread
    if is_crossed_spread(bid, ask) {
        return match config.crossed_handling {
            CrossedSpreadHandling::ReturnNaN => f64::NAN,
            CrossedSpreadHandling::SwapAndContinue => {
                // Note: Crossed spread detected, swapping and continuing
                (ask + bid) / 2.0 // Still calculate mid
            }
            CrossedSpreadHandling::ReturnError => f64::NAN,
        };
    }

    // Check for abnormal spread
    if is_abnormal_spread(bid, ask, config.max_spread_pct) {
        return match config.abnormal_handling {
            AbnormalSpreadHandling::ReturnNaN => f64::NAN,
            AbnormalSpreadHandling::LogAndContinue => {
                // Note: Abnormal spread detected but continuing with calculation
                (bid + ask) / 2.0
            }
            AbnormalSpreadHandling::ReturnError => f64::NAN,
        };
    }

    (bid + ask) / 2.0
}

/// Calculate weighted mid price with default configuration
#[inline]
pub fn weighted_mid_price(bid: f64, bid_qty: Option<f64>, ask: f64, ask_qty: Option<f64>) -> f64 {
    weighted_mid_price_with_config(bid, bid_qty, ask, ask_qty, &MarketPricingConfig::default())
}

/// Calculate weighted mid price with custom configuration
pub fn weighted_mid_price_with_config(
    bid: f64,
    bid_qty: Option<f64>,
    ask: f64,
    ask_qty: Option<f64>,
    config: &MarketPricingConfig,
) -> f64 {
    // First check if simple mid is valid
    let simple_mid = mid_price_with_config(bid, ask, config);
    if simple_mid.is_nan() {
        return f64::NAN;
    }

    // Calculate weighted mid if both quantities are valid
    match (bid_qty, ask_qty) {
        (Some(bq), Some(aq)) if bq > 0.0 && aq > 0.0 => {
            // Normal weighted calculation
            (bid * aq + ask * bq) / (bq + aq)
        }
        (Some(0.0), Some(aq)) if aq > 0.0 => {
            // Zero bid quantity - use simple mid for safety
            // Note: Using simple mid when one-sided quantity is zero
            simple_mid
        }
        (Some(bq), Some(0.0)) if bq > 0.0 => {
            // Zero ask quantity - use simple mid for safety
            // Note: Using simple mid when one-sided quantity is zero
            simple_mid
        }
        _ => {
            // Missing or invalid quantities - use simple mid
            simple_mid
        }
    }
}

/// Calculate absolute spread
#[inline]
pub fn spread(bid: f64, ask: f64) -> f64 {
    ask - bid
}

/// Calculate spread as percentage of mid price
#[inline]
pub fn spread_pct(bid: f64, ask: f64) -> f64 {
    if is_crossed_spread(bid, ask) {
        return f64::NAN; // Percentage undefined for crossed spreads
    }
    calculate_spread_pct(bid, ask)
}

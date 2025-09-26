//! Validation utilities for market data

use crate::constants::market::{MIN_VALID_PRICE, MIN_VALID_QUANTITY};
use crate::market_utils::error::{MarketDataError, MarketDataResult};

/// Validate a single price value
#[inline]
pub fn validate_price(price: f64, name: &str) -> MarketDataResult<()> {
    if !price.is_finite() {
        return Err(MarketDataError::InvalidPrice(format!(
            "{name} must be finite, got {price:?}"
        )));
    }
    if price < MIN_VALID_PRICE {
        return Err(MarketDataError::InvalidPrice(format!(
            "{name} must be non-negative, got {price}"
        )));
    }
    Ok(())
}

/// Validate a single quantity value
#[inline]
pub fn validate_quantity(qty: f64, name: &str) -> MarketDataResult<()> {
    if !qty.is_finite() {
        return Err(MarketDataError::InvalidQuantity(format!(
            "{name} must be finite, got {qty:?}"
        )));
    }
    if qty < MIN_VALID_QUANTITY {
        return Err(MarketDataError::InvalidQuantity(format!(
            "{name} must be non-negative, got {qty}"
        )));
    }
    Ok(())
}

/// Check if prices form a crossed spread
#[inline]
pub fn is_crossed_spread(bid: f64, ask: f64) -> bool {
    bid > ask
}

/// Calculate spread percentage relative to mid price
#[inline]
pub fn calculate_spread_pct(bid: f64, ask: f64) -> f64 {
    let mid = (bid + ask) / 2.0;
    if mid > 0.0 {
        (ask - bid) / mid
    } else {
        f64::NAN
    }
}

/// Check if spread is abnormal based on threshold
#[inline]
pub fn is_abnormal_spread(bid: f64, ask: f64, threshold: Option<f64>) -> bool {
    if let Some(max_spread) = threshold {
        let spread_pct = calculate_spread_pct(bid, ask);
        spread_pct.is_finite() && spread_pct > max_spread
    } else {
        false
    }
}

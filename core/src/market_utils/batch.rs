//! Batch processing functions for market pricing utilities
//!
//! This module provides Arrow-native batch processing for market data calculations,
//! supporting broadcasting and parallel processing for high performance.

use arrow::array::builder::Float64Builder;
use arrow::array::{ArrayRef, Float64Array};
use arrow::error::ArrowError;
use rayon::prelude::*;
use std::sync::Arc;

use crate::compute::{get_scalar_or_array_value, validate_broadcast_compatibility};
use crate::constants::get_parallel_threshold;
use crate::market_utils::pricing::{
    mid_price_with_config, weighted_mid_price_with_config, MarketPricingConfig,
};
use crate::market_utils::validation::{
    calculate_spread_pct, is_abnormal_spread, is_crossed_spread,
};

/// Metrics collected during batch processing
#[derive(Debug, Clone, Default)]
pub struct BatchMetrics {
    /// Total number of elements processed
    pub total_processed: usize,
    /// Number of NaN results
    pub nan_count: usize,
    /// Number of crossed spreads (bid > ask)
    pub crossed_spreads: usize,
    /// Number of abnormal spreads (exceeding threshold)
    pub abnormal_spreads: usize,
    /// Mean spread percentage
    pub mean_spread_pct: f64,
    /// Maximum spread percentage
    pub max_spread_pct: f64,
}

/// Calculate mid prices for batch of bid/ask prices
///
/// # Arguments
/// * `bids` - Bid prices array (can be scalar for broadcasting)
/// * `asks` - Ask prices array (can be scalar for broadcasting)
///
/// # Returns
/// Arrow Float64Array of mid prices
pub fn mid_price_batch(bids: &Float64Array, asks: &Float64Array) -> Result<ArrayRef, ArrowError> {
    mid_price_batch_with_config(bids, asks, &MarketPricingConfig::default())
}

/// Calculate mid prices with custom configuration
///
/// # Arguments
/// * `bids` - Bid prices array
/// * `asks` - Ask prices array
/// * `config` - Pricing configuration
///
/// # Returns
/// Arrow Float64Array of mid prices
pub fn mid_price_batch_with_config(
    bids: &Float64Array,
    asks: &Float64Array,
    config: &MarketPricingConfig,
) -> Result<ArrayRef, ArrowError> {
    // Validate arrays for broadcasting compatibility
    let len = validate_broadcast_compatibility(&[bids, asks])?;

    // Handle empty arrays
    if len == 0 {
        return Ok(Arc::new(Float64Builder::new().finish()));
    }

    let mut builder = Float64Builder::with_capacity(len);

    if len >= get_parallel_threshold() {
        // Parallel processing for large arrays
        let results: Vec<f64> = (0..len)
            .into_par_iter()
            .map(|i| {
                let bid = get_scalar_or_array_value(bids, i);
                let ask = get_scalar_or_array_value(asks, i);
                mid_price_with_config(bid, ask, config)
            })
            .collect();

        builder.append_slice(&results);
        Ok(Arc::new(builder.finish()))
    } else {
        // Sequential processing for small arrays
        for i in 0..len {
            let bid = get_scalar_or_array_value(bids, i);
            let ask = get_scalar_or_array_value(asks, i);
            let mid = mid_price_with_config(bid, ask, config);
            builder.append_value(mid);
        }

        Ok(Arc::new(builder.finish()))
    }
}

/// Calculate mid prices and collect metrics
///
/// # Arguments
/// * `bids` - Bid prices array
/// * `asks` - Ask prices array
/// * `config` - Pricing configuration
///
/// # Returns
/// Tuple of (mid prices array, metrics)
pub fn mid_price_batch_with_metrics(
    bids: &Float64Array,
    asks: &Float64Array,
    config: &MarketPricingConfig,
) -> Result<(ArrayRef, BatchMetrics), ArrowError> {
    // Validate arrays for broadcasting compatibility
    let len = validate_broadcast_compatibility(&[bids, asks])?;

    // Handle empty arrays
    if len == 0 {
        return Ok((
            Arc::new(Float64Builder::new().finish()),
            BatchMetrics::default(),
        ));
    }

    let mut builder = Float64Builder::with_capacity(len);
    let mut metrics = BatchMetrics {
        total_processed: len,
        ..Default::default()
    };

    let mut spread_pcts = Vec::with_capacity(len);

    // Calculate mid prices and collect metrics
    for i in 0..len {
        let bid = get_scalar_or_array_value(bids, i);
        let ask = get_scalar_or_array_value(asks, i);

        // Check for crossed spread
        if is_crossed_spread(bid, ask) {
            metrics.crossed_spreads += 1;
        }

        // Check for abnormal spread
        if is_abnormal_spread(bid, ask, config.max_spread_pct) {
            metrics.abnormal_spreads += 1;
        }

        // Calculate spread percentage
        let spread_pct = calculate_spread_pct(bid, ask);
        if spread_pct.is_finite() && spread_pct >= 0.0 {
            spread_pcts.push(spread_pct);
            if spread_pct > metrics.max_spread_pct {
                metrics.max_spread_pct = spread_pct;
            }
        }

        // Calculate mid price
        let mid = mid_price_with_config(bid, ask, config);
        if mid.is_nan() {
            metrics.nan_count += 1;
        }
        builder.append_value(mid);
    }

    // Calculate mean spread percentage
    if !spread_pcts.is_empty() {
        metrics.mean_spread_pct = spread_pcts.iter().sum::<f64>() / spread_pcts.len() as f64;
    }

    Ok((Arc::new(builder.finish()), metrics))
}

/// Calculate weighted mid prices for batch
///
/// # Arguments
/// * `bids` - Bid prices array
/// * `bid_qtys` - Bid quantities array (optional)
/// * `asks` - Ask prices array
/// * `ask_qtys` - Ask quantities array (optional)
///
/// # Returns
/// Arrow Float64Array of weighted mid prices
pub fn weighted_mid_price_batch(
    bids: &Float64Array,
    bid_qtys: Option<&Float64Array>,
    asks: &Float64Array,
    ask_qtys: Option<&Float64Array>,
) -> Result<ArrayRef, ArrowError> {
    weighted_mid_price_batch_with_config(
        bids,
        bid_qtys,
        asks,
        ask_qtys,
        &MarketPricingConfig::default(),
    )
}

/// Calculate weighted mid prices with custom configuration
pub fn weighted_mid_price_batch_with_config(
    bids: &Float64Array,
    bid_qtys: Option<&Float64Array>,
    asks: &Float64Array,
    ask_qtys: Option<&Float64Array>,
    config: &MarketPricingConfig,
) -> Result<ArrayRef, ArrowError> {
    // Build array list for validation
    let mut arrays: Vec<&Float64Array> = vec![bids, asks];
    if let Some(bq) = bid_qtys {
        arrays.push(bq);
    }
    if let Some(aq) = ask_qtys {
        arrays.push(aq);
    }

    // Validate arrays for broadcasting compatibility
    let len = validate_broadcast_compatibility(&arrays)?;

    // Handle empty arrays
    if len == 0 {
        return Ok(Arc::new(Float64Builder::new().finish()));
    }

    let mut builder = Float64Builder::with_capacity(len);

    if len >= get_parallel_threshold() {
        // Parallel processing for large arrays
        let results: Vec<f64> = (0..len)
            .into_par_iter()
            .map(|i| {
                let bid = get_scalar_or_array_value(bids, i);
                let ask = get_scalar_or_array_value(asks, i);

                let bid_qty = bid_qtys.map(|bq| get_scalar_or_array_value(bq, i));
                let ask_qty = ask_qtys.map(|aq| get_scalar_or_array_value(aq, i));

                weighted_mid_price_with_config(bid, bid_qty, ask, ask_qty, config)
            })
            .collect();

        builder.append_slice(&results);
        Ok(Arc::new(builder.finish()))
    } else {
        // Sequential processing for small arrays
        for i in 0..len {
            let bid = get_scalar_or_array_value(bids, i);
            let ask = get_scalar_or_array_value(asks, i);

            let bid_qty = bid_qtys.map(|bq| get_scalar_or_array_value(bq, i));
            let ask_qty = ask_qtys.map(|aq| get_scalar_or_array_value(aq, i));

            let mid = weighted_mid_price_with_config(bid, bid_qty, ask, ask_qty, config);
            builder.append_value(mid);
        }

        Ok(Arc::new(builder.finish()))
    }
}

/// Calculate absolute spreads for batch
///
/// # Arguments
/// * `bids` - Bid prices array
/// * `asks` - Ask prices array
///
/// # Returns
/// Arrow Float64Array of spreads (ask - bid)
pub fn spread_batch(bids: &Float64Array, asks: &Float64Array) -> Result<ArrayRef, ArrowError> {
    // Validate arrays for broadcasting compatibility
    let len = validate_broadcast_compatibility(&[bids, asks])?;

    // Handle empty arrays
    if len == 0 {
        return Ok(Arc::new(Float64Builder::new().finish()));
    }

    let mut builder = Float64Builder::with_capacity(len);

    if len >= get_parallel_threshold() {
        // Parallel processing for large arrays
        let results: Vec<f64> = (0..len)
            .into_par_iter()
            .map(|i| {
                let bid = get_scalar_or_array_value(bids, i);
                let ask = get_scalar_or_array_value(asks, i);
                crate::market_utils::spread(bid, ask)
            })
            .collect();

        builder.append_slice(&results);
        Ok(Arc::new(builder.finish()))
    } else {
        // Sequential processing for small arrays
        for i in 0..len {
            let bid = get_scalar_or_array_value(bids, i);
            let ask = get_scalar_or_array_value(asks, i);
            let spread = crate::market_utils::spread(bid, ask);
            builder.append_value(spread);
        }

        Ok(Arc::new(builder.finish()))
    }
}

/// Calculate spread percentages for batch
///
/// # Arguments
/// * `bids` - Bid prices array
/// * `asks` - Ask prices array
///
/// # Returns
/// Arrow Float64Array of spread percentages
pub fn spread_pct_batch(bids: &Float64Array, asks: &Float64Array) -> Result<ArrayRef, ArrowError> {
    // Validate arrays for broadcasting compatibility
    let len = validate_broadcast_compatibility(&[bids, asks])?;

    // Handle empty arrays
    if len == 0 {
        return Ok(Arc::new(Float64Builder::new().finish()));
    }

    let mut builder = Float64Builder::with_capacity(len);

    if len >= get_parallel_threshold() {
        // Parallel processing for large arrays
        let results: Vec<f64> = (0..len)
            .into_par_iter()
            .map(|i| {
                let bid = get_scalar_or_array_value(bids, i);
                let ask = get_scalar_or_array_value(asks, i);
                crate::market_utils::spread_pct(bid, ask)
            })
            .collect();

        builder.append_slice(&results);
        Ok(Arc::new(builder.finish()))
    } else {
        // Sequential processing for small arrays
        for i in 0..len {
            let bid = get_scalar_or_array_value(bids, i);
            let ask = get_scalar_or_array_value(asks, i);
            let pct = crate::market_utils::spread_pct(bid, ask);
            builder.append_value(pct);
        }

        Ok(Arc::new(builder.finish()))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    #[test]
    fn test_mid_price_batch_simple() {
        let bids = Float64Array::from(vec![100.0, 101.0, 102.0]);
        let asks = Float64Array::from(vec![100.2, 101.3, 102.4]);

        let result = mid_price_batch(&bids, &asks).unwrap();
        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        assert_eq!(result_array.len(), 3);
        assert_relative_eq!(result_array.value(0), 100.1, epsilon = 1e-10);
        assert_relative_eq!(result_array.value(1), 101.15, epsilon = 1e-10);
        assert_relative_eq!(result_array.value(2), 102.2, epsilon = 1e-10);
    }

    #[test]
    fn test_mid_price_batch_broadcasting() {
        // Scalar bid, array ask
        let bid = Float64Array::from(vec![100.0]);
        let asks = Float64Array::from(vec![100.2, 100.3, 100.4]);

        let result = mid_price_batch(&bid, &asks).unwrap();
        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        assert_eq!(result_array.len(), 3);
        assert_relative_eq!(result_array.value(0), 100.1, epsilon = 1e-10);
        assert_relative_eq!(result_array.value(1), 100.15, epsilon = 1e-10);
        assert_relative_eq!(result_array.value(2), 100.2, epsilon = 1e-10);
    }

    #[test]
    fn test_mid_price_batch_with_metrics() {
        let bids = Float64Array::from(vec![100.0, 1.0, 105.0, 100.0]);
        let asks = Float64Array::from(vec![100.2, 1000.0, 104.0, 100.5]);
        let config = MarketPricingConfig::default();

        let (result, metrics) = mid_price_batch_with_metrics(&bids, &asks, &config).unwrap();
        let _result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        assert_eq!(metrics.total_processed, 4);
        assert_eq!(metrics.crossed_spreads, 1); // bid=105, ask=104
        assert!(metrics.abnormal_spreads > 0); // bid=1, ask=1000
        assert!(metrics.nan_count > 0); // Some should be NaN
        assert!(metrics.max_spread_pct > 0.0);
    }

    #[test]
    fn test_weighted_mid_price_batch() {
        let bids = Float64Array::from(vec![100.0, 101.0]);
        let bid_qtys = Float64Array::from(vec![1000.0, 2000.0]);
        let asks = Float64Array::from(vec![100.2, 101.3]);
        let ask_qtys = Float64Array::from(vec![1500.0, 1000.0]);

        let result =
            weighted_mid_price_batch(&bids, Some(&bid_qtys), &asks, Some(&ask_qtys)).unwrap();

        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();
        assert_eq!(result_array.len(), 2);

        // First weighted mid
        let expected_0 = (100.0 * 1500.0 + 100.2 * 1000.0) / 2500.0;
        assert_relative_eq!(result_array.value(0), expected_0, epsilon = 1e-10);
    }

    #[test]
    fn test_spread_batch() {
        let bids = Float64Array::from(vec![100.0, 99.8]);
        let asks = Float64Array::from(vec![100.2, 100.2]);

        let result = spread_batch(&bids, &asks).unwrap();
        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        assert_relative_eq!(result_array.value(0), 0.2, epsilon = 1e-10);
        assert_relative_eq!(result_array.value(1), 0.4, epsilon = 1e-10);
    }

    #[test]
    fn test_spread_pct_batch() {
        let bids = Float64Array::from(vec![100.0, 99.0]);
        let asks = Float64Array::from(vec![100.2, 101.0]);

        let result = spread_pct_batch(&bids, &asks).unwrap();
        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        // First: (100.2 - 100.0) / 100.1 ≈ 0.001998
        assert_relative_eq!(result_array.value(0), 0.001998, epsilon = 1e-5);
        // Second: (101.0 - 99.0) / 100.0 = 0.02
        assert_relative_eq!(result_array.value(1), 0.02, epsilon = 1e-10);
    }

    #[test]
    fn test_incompatible_lengths() {
        let bids = Float64Array::from(vec![100.0, 101.0]);
        let asks = Float64Array::from(vec![100.2, 100.3, 100.4]);

        let result = mid_price_batch(&bids, &asks);
        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("incompatible length"));
    }

    #[test]
    fn test_empty_arrays() {
        let bids = Float64Array::from(vec![] as Vec<f64>);
        let asks = Float64Array::from(vec![] as Vec<f64>);

        let result = mid_price_batch(&bids, &asks).unwrap();
        let _result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        assert_eq!(_result_array.len(), 0);
    }
}

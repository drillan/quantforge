//! Unified Greeks batch structure for all models
//!
//! This module provides a common GreeksBatch structure used by all option pricing models
//! to ensure consistency across the codebase.

/// Batch Greeks result structure (arrays of each Greek)
///
/// This structure contains vectors of Greeks calculated for batches of options.
/// All vectors have the same length, corresponding to the number of options in the batch.
#[derive(Debug, Clone)]
pub struct GreeksBatch {
    /// Delta values for each option
    pub delta: Vec<f64>,
    /// Gamma values for each option
    pub gamma: Vec<f64>,
    /// Vega values for each option (per 1% volatility change)
    pub vega: Vec<f64>,
    /// Theta values for each option (per day)
    pub theta: Vec<f64>,
    /// Rho values for each option (per 1% rate change)
    pub rho: Vec<f64>,
    /// Dividend rho values for each option (per 1% dividend yield change)
    /// This field is optional since not all models use dividends
    pub dividend_rho: Vec<f64>,
}

impl GreeksBatch {
    /// Create a new GreeksBatch with specified capacity
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            delta: Vec::with_capacity(capacity),
            gamma: Vec::with_capacity(capacity),
            vega: Vec::with_capacity(capacity),
            theta: Vec::with_capacity(capacity),
            rho: Vec::with_capacity(capacity),
            dividend_rho: Vec::with_capacity(capacity),
        }
    }

    /// Create a new GreeksBatch from vectors
    pub fn new(
        delta: Vec<f64>,
        gamma: Vec<f64>,
        vega: Vec<f64>,
        theta: Vec<f64>,
        rho: Vec<f64>,
        dividend_rho: Vec<f64>,
    ) -> Self {
        debug_assert_eq!(delta.len(), gamma.len());
        debug_assert_eq!(delta.len(), vega.len());
        debug_assert_eq!(delta.len(), theta.len());
        debug_assert_eq!(delta.len(), rho.len());
        debug_assert_eq!(delta.len(), dividend_rho.len());

        Self {
            delta,
            gamma,
            vega,
            theta,
            rho,
            dividend_rho,
        }
    }

    /// Get the number of options in the batch
    pub fn len(&self) -> usize {
        self.delta.len()
    }

    /// Check if the batch is empty
    pub fn is_empty(&self) -> bool {
        self.delta.is_empty()
    }
}

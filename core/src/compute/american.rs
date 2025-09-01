//! American option pricing - Arrow-native implementation

use arrow::array::{Float64Array, ArrayRef};
use arrow::error::ArrowError;

/// American option model using Bjerksund-Stensland approximation
pub struct American;

impl American {
    /// Calculate American call option price
    pub fn call_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        // Bjerksund-Stensland approximation for American options
        Err(ArrowError::NotYetImplemented(
            "American option implementation pending".to_string()
        ))
    }
    
    /// Calculate American put option price
    pub fn put_price(
        spots: &Float64Array,
        strikes: &Float64Array,
        times: &Float64Array,
        rates: &Float64Array,
        sigmas: &Float64Array,
    ) -> Result<ArrayRef, ArrowError> {
        Err(ArrowError::NotYetImplemented(
            "American option implementation pending".to_string()
        ))
    }
}
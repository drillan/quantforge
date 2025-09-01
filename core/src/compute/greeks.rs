//! Unified Greeks calculation for all models

use arrow::array::{Array, Float64Array, StructArray, ArrayRef};
use arrow::datatypes::{DataType, Field};
use arrow::error::ArrowError;
use std::sync::Arc;

use crate::compute::black_scholes::BlackScholes;

/// Calculate all Greeks for a given model and return as a StructArray
pub fn calculate_greeks(
    model: &str,
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    rates: &Float64Array,
    sigmas: &Float64Array,
    is_call: bool,
) -> Result<StructArray, ArrowError> {
    match model {
        "black_scholes" | "bs" => {
            calculate_black_scholes_greeks(spots, strikes, times, rates, sigmas, is_call)
        }
        _ => Err(ArrowError::NotYetImplemented(
            format!("Greeks calculation for model '{}' not yet implemented", model)
        ))
    }
}

/// Calculate Black-Scholes Greeks
fn calculate_black_scholes_greeks(
    spots: &Float64Array,
    strikes: &Float64Array,
    times: &Float64Array,
    rates: &Float64Array,
    sigmas: &Float64Array,
    is_call: bool,
) -> Result<StructArray, ArrowError> {
    // Calculate each Greek
    let delta = BlackScholes::delta(spots, strikes, times, rates, sigmas, is_call)?;
    let gamma = BlackScholes::gamma(spots, strikes, times, rates, sigmas)?;
    let vega = BlackScholes::vega(spots, strikes, times, rates, sigmas)?;
    let theta = BlackScholes::theta(spots, strikes, times, rates, sigmas, is_call)?;
    let rho = BlackScholes::rho(spots, strikes, times, rates, sigmas, is_call)?;
    
    // Create fields for the struct
    let fields = vec![
        Field::new("delta", DataType::Float64, false),
        Field::new("gamma", DataType::Float64, false),
        Field::new("vega", DataType::Float64, false),
        Field::new("theta", DataType::Float64, false),
        Field::new("rho", DataType::Float64, false),
    ];
    
    // Create the StructArray
    let arrays: Vec<ArrayRef> = vec![delta, gamma, vega, theta, rho];
    
    StructArray::try_new(fields.into(), arrays, None)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_calculate_greeks() {
        let spots = Float64Array::from(vec![100.0]);
        let strikes = Float64Array::from(vec![100.0]);
        let times = Float64Array::from(vec![1.0]);
        let rates = Float64Array::from(vec![0.05]);
        let sigmas = Float64Array::from(vec![0.2]);
        
        let greeks = calculate_greeks(
            "black_scholes",
            &spots,
            &strikes,
            &times,
            &rates,
            &sigmas,
            true
        ).unwrap();
        
        // Verify structure
        assert_eq!(greeks.len(), 1);
        assert_eq!(greeks.num_columns(), 5);
        
        // Check field names
        let fields: Vec<String> = greeks.fields()
            .iter()
            .map(|f| f.name().clone())
            .collect();
        
        assert_eq!(fields, vec!["delta", "gamma", "vega", "theta", "rho"]);
    }
}
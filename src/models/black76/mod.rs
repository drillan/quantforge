//! Black76 model for commodity and futures options

pub mod greeks;
pub mod implied_volatility;
pub mod pricing;

use crate::error::QuantForgeError;
use crate::models::{Greeks, PricingModel};

/// Black76 model for commodity and futures options
pub struct Black76;

/// Parameters for Black76 model
#[derive(Debug, Clone, Copy)]
pub struct Black76Params {
    /// Forward price
    pub forward: f64,
    /// Strike price
    pub strike: f64,
    /// Time to maturity (in years)
    pub time: f64,
    /// Risk-free rate (for discounting)
    pub rate: f64,
    /// Volatility (annualized)
    pub sigma: f64,
}

impl Black76Params {
    /// Create new Black76 parameters
    pub fn new(forward: f64, strike: f64, time: f64, rate: f64, sigma: f64) -> Self {
        Self {
            forward,
            strike,
            time,
            rate,
            sigma,
        }
    }

    /// Validate parameters
    pub fn validate(&self) -> Result<(), QuantForgeError> {
        if self.forward <= 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "Forward price must be positive".to_string(),
            ));
        }
        if self.strike <= 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "Strike price must be positive".to_string(),
            ));
        }
        if self.time <= 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "Time to maturity must be positive".to_string(),
            ));
        }
        if self.sigma <= 0.0 {
            return Err(QuantForgeError::InvalidInput(
                "Volatility must be positive".to_string(),
            ));
        }
        if !self.forward.is_finite()
            || !self.strike.is_finite()
            || !self.time.is_finite()
            || !self.rate.is_finite()
            || !self.sigma.is_finite()
        {
            return Err(QuantForgeError::InvalidInput(
                "All parameters must be finite".to_string(),
            ));
        }
        Ok(())
    }

    /// Calculate d1 for Black76 model
    #[inline]
    pub fn d1(&self) -> f64 {
        let sqrt_time = self.time.sqrt();
        ((self.forward / self.strike).ln() + 0.5 * self.sigma * self.sigma * self.time)
            / (self.sigma * sqrt_time)
    }

    /// Calculate d2 for Black76 model
    #[inline]
    pub fn d2(&self) -> f64 {
        self.d1() - self.sigma * self.time.sqrt()
    }

    /// Calculate discount factor
    #[inline]
    pub fn discount_factor(&self) -> f64 {
        (-self.rate * self.time).exp()
    }
}

impl PricingModel for Black76 {
    type Params = Black76Params;

    fn call_price(params: &Self::Params) -> f64 {
        pricing::call_price(params)
    }

    fn put_price(params: &Self::Params) -> f64 {
        pricing::put_price(params)
    }

    fn greeks(params: &Self::Params, is_call: bool) -> Greeks {
        greeks::calculate_greeks(params, is_call)
    }

    fn implied_volatility(
        price: f64,
        params: &Self::Params,
        is_call: bool,
        initial_guess: Option<f64>,
    ) -> Result<f64, QuantForgeError> {
        implied_volatility::calculate_iv(price, params, is_call, initial_guess)
    }
}

// Re-export main functions
pub use greeks::{calculate_greeks, delta, gamma, rho, theta, vega};
pub use implied_volatility::{calculate_iv, calculate_iv_batch};
pub use pricing::{call_price, call_price_batch, put_price, put_price_batch};

// Utility function to convert spot to forward
/// Convert spot price to forward price
/// F = S * exp((r - q) * T)
pub fn spot_to_forward(spot: f64, rate: f64, div_yield: f64, time: f64) -> f64 {
    spot * ((rate - div_yield) * time).exp()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_params_validation() {
        // Valid params
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);
        assert!(params.validate().is_ok());

        // Invalid forward
        let params = Black76Params::new(-100.0, 100.0, 1.0, 0.05, 0.2);
        assert!(params.validate().is_err());

        // Invalid strike
        let params = Black76Params::new(100.0, -100.0, 1.0, 0.05, 0.2);
        assert!(params.validate().is_err());

        // Invalid time
        let params = Black76Params::new(100.0, 100.0, -1.0, 0.05, 0.2);
        assert!(params.validate().is_err());

        // Invalid volatility
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, -0.2);
        assert!(params.validate().is_err());
    }

    #[test]
    fn test_spot_to_forward() {
        let spot = 100.0;
        let rate = 0.05;
        let div_yield = 0.02;
        let time = 1.0;

        let forward = spot_to_forward(spot, rate, div_yield, time);
        let expected = 100.0 * ((0.05 - 0.02) * 1.0_f64).exp();
        assert!((forward - expected).abs() < 1e-10);
    }
}

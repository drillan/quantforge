// Legacy modules - will be refactored
pub mod black_scholes;
pub mod black_scholes_parallel;

// New model implementations
pub mod american;
pub mod black76;
pub mod black_scholes_model;
pub mod greeks;
pub mod greeks_parallel;
pub mod implied_volatility;
pub mod iv_initial_guess;
pub mod merton;

// Re-export legacy functions for backward compatibility during migration
pub use black_scholes::{bs_call_price, bs_call_price_batch, bs_put_price, bs_put_price_batch};
pub use black_scholes_parallel::{
    bs_call_price_batch_parallel, bs_call_price_batch_parallel_py, bs_put_price_batch_parallel,
    bs_put_price_batch_parallel_py,
};
pub use greeks::{
    calculate_all_greeks, delta_call, delta_call_batch, delta_put, delta_put_batch, gamma,
    gamma_batch, rho_call, rho_call_batch, rho_put, rho_put_batch, theta_call, theta_call_batch,
    theta_put, theta_put_batch, vega, vega_batch, Greeks,
};
pub use implied_volatility::{
    implied_volatility_batch, implied_volatility_batch_parallel, implied_volatility_call,
    implied_volatility_put,
};

// New model trait system
// Greeks is already imported above

/// Common trait for all option pricing models
pub trait PricingModel {
    /// Model-specific parameters
    type Params;

    /// Calculate call option price
    fn call_price(params: &Self::Params) -> f64;

    /// Calculate put option price
    fn put_price(params: &Self::Params) -> f64;

    /// Calculate all Greeks for the option
    fn greeks(params: &Self::Params, is_call: bool) -> Greeks;

    /// Calculate implied volatility from option price
    fn implied_volatility(
        price: f64,
        params: &Self::Params,
        is_call: bool,
        initial_guess: Option<f64>,
    ) -> Result<f64, crate::error::QuantForgeError>;
}

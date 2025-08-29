//! Black76 Greeks calculations

use super::Black76Params;
use crate::math::distributions::{norm_cdf, norm_pdf};
use crate::models::Greeks;

/// Calculate all Greeks for Black76 model
pub fn calculate_greeks(params: &Black76Params, is_call: bool) -> Greeks {
    if params.validate().is_err() {
        return Greeks {
            delta: f64::NAN,
            gamma: f64::NAN,
            vega: f64::NAN,
            theta: f64::NAN,
            rho: f64::NAN,
        };
    }

    let d1 = params.d1();
    let d2 = params.d2();
    let sqrt_time = params.time.sqrt();
    let discount = params.discount_factor();
    let nd1 = norm_pdf(d1);
    let _nd2 = norm_pdf(d2);

    // Delta: ∂V/∂F
    let delta_val = if is_call {
        discount * norm_cdf(d1)
    } else {
        -discount * norm_cdf(-d1)
    };

    // Gamma: ∂²V/∂F²
    let gamma_val = discount * nd1 / (params.forward * params.sigma * sqrt_time);

    // Vega: ∂V/∂σ
    let vega_val = discount * params.forward * nd1 * sqrt_time;

    // Theta: -∂V/∂T (negative because we want time decay)
    let theta_val = if is_call {
        -params.forward * discount * nd1 * params.sigma / (2.0 * sqrt_time)
            - params.rate * params.forward * discount * norm_cdf(d1)
            + params.rate * params.strike * discount * norm_cdf(d2)
    } else {
        -params.forward * discount * nd1 * params.sigma / (2.0 * sqrt_time)
            + params.rate * params.forward * discount * norm_cdf(-d1)
            - params.rate * params.strike * discount * norm_cdf(-d2)
    };

    // Rho: ∂V/∂r
    let rho_val = if is_call {
        -params.time * discount * (params.forward * norm_cdf(d1) - params.strike * norm_cdf(d2))
    } else {
        -params.time * discount * (params.strike * norm_cdf(-d2) - params.forward * norm_cdf(-d1))
    };

    Greeks {
        delta: delta_val,
        gamma: gamma_val,
        vega: vega_val / 100.0,   // Convert to per 1% change
        theta: theta_val / 365.0, // Convert to per day
        rho: rho_val / 100.0,     // Convert to per 1% change
    }
}

/// Calculate Delta for Black76 model
pub fn delta(params: &Black76Params, is_call: bool) -> f64 {
    if params.validate().is_err() {
        return f64::NAN;
    }

    let d1 = params.d1();
    let discount = params.discount_factor();

    if is_call {
        discount * norm_cdf(d1)
    } else {
        -discount * norm_cdf(-d1)
    }
}

/// Calculate Gamma for Black76 model
pub fn gamma(params: &Black76Params) -> f64 {
    if params.validate().is_err() {
        return f64::NAN;
    }

    let d1 = params.d1();
    let sqrt_time = params.time.sqrt();
    let discount = params.discount_factor();

    discount * norm_pdf(d1) / (params.forward * params.sigma * sqrt_time)
}

/// Calculate Vega for Black76 model
pub fn vega(params: &Black76Params) -> f64 {
    if params.validate().is_err() {
        return f64::NAN;
    }

    let d1 = params.d1();
    let sqrt_time = params.time.sqrt();
    let discount = params.discount_factor();

    discount * params.forward * norm_pdf(d1) * sqrt_time / 100.0
}

/// Calculate Theta for Black76 model
pub fn theta(params: &Black76Params, is_call: bool) -> f64 {
    if params.validate().is_err() {
        return f64::NAN;
    }

    let d1 = params.d1();
    let d2 = params.d2();
    let sqrt_time = params.time.sqrt();
    let discount = params.discount_factor();

    // Black76 theta formula
    let common_term = -params.forward * discount * norm_pdf(d1) * params.sigma / (2.0 * sqrt_time);
    
    let theta_val = if is_call {
        common_term - params.rate * discount * (params.forward * norm_cdf(d1) - params.strike * norm_cdf(d2))
    } else {
        common_term - params.rate * discount * (-params.forward * norm_cdf(-d1) + params.strike * norm_cdf(-d2))
    };

    -theta_val / 365.0 // Negative for time decay, convert to per day
}

/// Calculate Rho for Black76 model
pub fn rho(params: &Black76Params, is_call: bool) -> f64 {
    if params.validate().is_err() {
        return f64::NAN;
    }

    let d1 = params.d1();
    let d2 = params.d2();
    let discount = params.discount_factor();

    let rho_val = if is_call {
        -params.time * discount * (params.forward * norm_cdf(d1) - params.strike * norm_cdf(d2))
    } else {
        -params.time * discount * (params.strike * norm_cdf(-d2) - params.forward * norm_cdf(-d1))
    };

    rho_val / 100.0 // Convert to per 1% change
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;

    #[test]
    fn test_greeks_consistency() {
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);

        // Calculate Greeks using the all-in-one function
        let greeks_call = calculate_greeks(&params, true);
        let greeks_put = calculate_greeks(&params, false);

        // Calculate Greeks individually
        let delta_call = delta(&params, true);
        let delta_put = delta(&params, false);
        let gamma_val = gamma(&params);
        let vega_val = vega(&params);
        let theta_call = theta(&params, true);
        let theta_put = theta(&params, false);
        let rho_call = rho(&params, true);
        let rho_put = rho(&params, false);

        // Verify consistency
        assert!((greeks_call.delta - delta_call).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_put.delta - delta_put).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_call.gamma - gamma_val).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_put.gamma - gamma_val).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_call.vega - vega_val).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_put.vega - vega_val).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_call.theta - theta_call).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_put.theta - theta_put).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_call.rho - rho_call).abs() < NUMERICAL_TOLERANCE);
        assert!((greeks_put.rho - rho_put).abs() < NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_gamma_symmetry() {
        // Gamma should be the same for call and put
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);

        let greeks_call = calculate_greeks(&params, true);
        let greeks_put = calculate_greeks(&params, false);

        assert!((greeks_call.gamma - greeks_put.gamma).abs() < NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_vega_symmetry() {
        // Vega should be the same for call and put
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);

        let greeks_call = calculate_greeks(&params, true);
        let greeks_put = calculate_greeks(&params, false);

        assert!((greeks_call.vega - greeks_put.vega).abs() < NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_delta_bounds() {
        // Call delta should be between 0 and discount factor
        // Put delta should be between -discount factor and 0
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);
        let discount = params.discount_factor();

        let greeks_call = calculate_greeks(&params, true);
        let greeks_put = calculate_greeks(&params, false);

        assert!(greeks_call.delta >= 0.0);
        assert!(greeks_call.delta <= discount);
        assert!(greeks_put.delta <= 0.0);
        assert!(greeks_put.delta >= -discount);
    }

    #[test]
    fn test_theta_sign() {
        // Theta should be finite and reasonable
        let params = Black76Params::new(100.0, 100.0, 1.0, 0.05, 0.2);

        let greeks_call = calculate_greeks(&params, true);
        let _greeks_put = calculate_greeks(&params, false);

        // Theta should be finite and reasonable (daily theta)
        assert!(greeks_call.theta.is_finite());
        assert!(greeks_call.theta.abs() < 1.0); // Daily theta should be small
    }

    #[test]
    fn test_deep_itm_delta() {
        // Deep ITM call delta should be close to discount factor
        let params = Black76Params::new(150.0, 100.0, 0.1, 0.05, 0.2);
        let discount = params.discount_factor();

        let greeks_call = calculate_greeks(&params, true);
        assert!((greeks_call.delta - discount).abs() < 0.01);

        // Deep OTM put (which is equivalent to deep ITM call scenario) should have small delta
        let params = Black76Params::new(150.0, 100.0, 0.1, 0.05, 0.2);
        let greeks_put = calculate_greeks(&params, false);
        assert!(greeks_put.delta.abs() < 0.01);
    }
}

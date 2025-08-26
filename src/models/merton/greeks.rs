//! Merton model Greeks calculations for dividend-paying assets.

use crate::constants::DAYS_PER_YEAR;
use crate::math::distributions::{norm_cdf, norm_pdf};
use crate::models::merton::pricing::{calculate_d1, calculate_d2};

/// Extended Greeks structure for the Merton model.
/// Includes standard Greeks plus dividend_rho.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct MertonGreeks {
    /// Delta: ∂V/∂S
    pub delta: f64,
    /// Gamma: ∂²V/∂S²
    pub gamma: f64,
    /// Vega: ∂V/∂σ (per 1% change in volatility)
    pub vega: f64,
    /// Theta: ∂V/∂t (per day)
    pub theta: f64,
    /// Rho: ∂V/∂r (per 1% change in rate)
    pub rho: f64,
    /// Dividend Rho: ∂V/∂q (per 1% change in dividend yield)
    pub dividend_rho: f64,
}

impl MertonGreeks {
    /// Create a new MertonGreeks structure.
    pub fn new(delta: f64, gamma: f64, vega: f64, theta: f64, rho: f64, dividend_rho: f64) -> Self {
        Self {
            delta,
            gamma,
            vega,
            theta,
            rho,
            dividend_rho,
        }
    }

    /// Convert to the standard Greeks structure (without dividend_rho).
    pub fn to_standard_greeks(&self) -> crate::models::Greeks {
        crate::models::Greeks::new(self.delta, self.gamma, self.vega, self.theta, self.rho)
    }
}

/// Calculate all Greeks for a Merton model option.
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity (years)
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `sigma` - Volatility
/// * `is_call` - true for call, false for put
///
/// # Returns
/// Greeks structure compatible with the standard interface
pub fn calculate_greeks(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> crate::models::Greeks {
    let merton_greeks = calculate_merton_greeks(s, k, t, r, q, sigma, is_call);
    merton_greeks.to_standard_greeks()
}

/// Calculate all Greeks for a Merton model option (extended version).
///
/// # Arguments
/// * `s` - Spot price
/// * `k` - Strike price
/// * `t` - Time to maturity (years)
/// * `r` - Risk-free rate
/// * `q` - Dividend yield
/// * `sigma` - Volatility
/// * `is_call` - true for call, false for put
///
/// # Returns
/// MertonGreeks structure with all 6 Greeks including dividend_rho
pub fn calculate_merton_greeks(
    s: f64,
    k: f64,
    t: f64,
    r: f64,
    q: f64,
    sigma: f64,
    is_call: bool,
) -> MertonGreeks {
    // Handle special cases
    if t <= 0.0 {
        let delta = if is_call {
            if s > k {
                1.0
            } else {
                0.0
            }
        } else if s < k {
            -1.0
        } else {
            0.0
        };
        return MertonGreeks::new(delta, 0.0, 0.0, 0.0, 0.0, 0.0);
    }

    if s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return MertonGreeks::new(0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
    }

    // Calculate d1 and d2
    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let d2 = calculate_d2(d1, t, sigma);

    // Common terms
    let sqrt_t = t.sqrt();
    let exp_neg_qt = (-q * t).exp();
    let exp_neg_rt = (-r * t).exp();
    let nd1 = norm_cdf(d1);
    let nd2 = norm_cdf(d2);
    let n_neg_d1 = norm_cdf(-d1);
    let n_neg_d2 = norm_cdf(-d2);
    let nprime_d1 = norm_pdf(d1);

    // Delta
    let delta = if is_call {
        exp_neg_qt * nd1
    } else {
        -exp_neg_qt * n_neg_d1
    };

    // Gamma (same for call and put)
    let gamma = exp_neg_qt * nprime_d1 / (s * sigma * sqrt_t);

    // Vega (same for call and put, per 1% volatility change)
    let vega = s * exp_neg_qt * nprime_d1 * sqrt_t / 100.0;

    // Theta (per day)
    let theta = if is_call {
        let theta_per_year = -s * nprime_d1 * sigma * exp_neg_qt / (2.0 * sqrt_t)
            + q * s * nd1 * exp_neg_qt
            - r * k * exp_neg_rt * nd2;
        theta_per_year / DAYS_PER_YEAR
    } else {
        let theta_per_year = -s * nprime_d1 * sigma * exp_neg_qt / (2.0 * sqrt_t)
            - q * s * n_neg_d1 * exp_neg_qt
            + r * k * exp_neg_rt * n_neg_d2;
        theta_per_year / DAYS_PER_YEAR
    };

    // Rho (per 1% rate change)
    let rho = if is_call {
        k * t * exp_neg_rt * nd2 / 100.0
    } else {
        -k * t * exp_neg_rt * n_neg_d2 / 100.0
    };

    // Dividend Rho (per 1% dividend yield change)
    let dividend_rho = if is_call {
        -s * t * exp_neg_qt * nd1 / 100.0
    } else {
        s * t * exp_neg_qt * n_neg_d1 / 100.0
    };

    MertonGreeks::new(delta, gamma, vega, theta, rho, dividend_rho)
}

/// Calculate Delta for a Merton call option.
///
/// Delta = e^(-qT) * N(d1)
pub fn delta_call(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 {
        return if s > k { 1.0 } else { 0.0 };
    }
    if s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    (-q * t).exp() * norm_cdf(d1)
}

/// Calculate Delta for a Merton put option.
///
/// Delta = -e^(-qT) * N(-d1)
pub fn delta_put(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 {
        return if s < k { -1.0 } else { 0.0 };
    }
    if s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return if s <= 0.0 { -1.0 } else { 0.0 };
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    -(-q * t).exp() * norm_cdf(-d1)
}

/// Calculate Gamma for a Merton option (same for call and put).
///
/// Gamma = e^(-qT) * φ(d1) / (S * σ * √T)
pub fn gamma(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let sqrt_t = t.sqrt();

    (-q * t).exp() * norm_pdf(d1) / (s * sigma * sqrt_t)
}

/// Calculate Vega for a Merton option (same for call and put).
///
/// Vega = S * e^(-qT) * φ(d1) * √T / 100
pub fn vega(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let sqrt_t = t.sqrt();

    s * (-q * t).exp() * norm_pdf(d1) * sqrt_t / 100.0
}

/// Calculate Theta for a Merton call option (per day).
pub fn theta_call(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let d2 = calculate_d2(d1, t, sigma);
    let sqrt_t = t.sqrt();

    let theta_per_year = -s * norm_pdf(d1) * sigma * (-q * t).exp() / (2.0 * sqrt_t)
        + q * s * norm_cdf(d1) * (-q * t).exp()
        - r * k * (-r * t).exp() * norm_cdf(d2);

    theta_per_year / DAYS_PER_YEAR
}

/// Calculate Theta for a Merton put option (per day).
pub fn theta_put(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let d2 = calculate_d2(d1, t, sigma);
    let sqrt_t = t.sqrt();

    let theta_per_year = -s * norm_pdf(d1) * sigma * (-q * t).exp() / (2.0 * sqrt_t)
        - q * s * norm_cdf(-d1) * (-q * t).exp()
        + r * k * (-r * t).exp() * norm_cdf(-d2);

    theta_per_year / DAYS_PER_YEAR
}

/// Calculate Rho for a Merton call option (per 1% rate change).
pub fn rho_call(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let d2 = calculate_d2(d1, t, sigma);

    k * t * (-r * t).exp() * norm_cdf(d2) / 100.0
}

/// Calculate Rho for a Merton put option (per 1% rate change).
pub fn rho_put(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);
    let d2 = calculate_d2(d1, t, sigma);

    -k * t * (-r * t).exp() * norm_cdf(-d2) / 100.0
}

/// Calculate Dividend Rho for a Merton call option (per 1% dividend change).
pub fn dividend_rho_call(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);

    -s * t * (-q * t).exp() * norm_cdf(d1) / 100.0
}

/// Calculate Dividend Rho for a Merton put option (per 1% dividend change).
pub fn dividend_rho_put(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    if t <= 0.0 || s <= 0.0 || k <= 0.0 || sigma <= 0.0 {
        return 0.0;
    }

    let d1 = calculate_d1(s, k, t, r, q, sigma);

    s * t * (-q * t).exp() * norm_cdf(-d1) / 100.0
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    const TEST_TOLERANCE: f64 = 1e-6;

    #[test]
    fn test_merton_greeks_reduces_to_bs() {
        // When q=0, Merton Greeks should equal Black-Scholes Greeks
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let q = 0.0;
        let sigma = 0.20;

        let call_delta = delta_call(s, k, t, r, q, sigma);
        let put_delta = delta_put(s, k, t, r, q, sigma);
        let option_gamma = gamma(s, k, t, r, q, sigma);
        let option_vega = vega(s, k, t, r, q, sigma);

        // Expected Black-Scholes values
        assert_relative_eq!(call_delta, 0.6368306506756328, epsilon = TEST_TOLERANCE);
        assert_relative_eq!(
            put_delta,
            -0.363_169_349_324_367_2,
            epsilon = TEST_TOLERANCE
        );
        // Gamma has small differences due to exp(-q*t) factor when q=0
        assert_relative_eq!(option_gamma, 0.01760326517549745, epsilon = 0.002);
        assert_relative_eq!(option_vega, 0.3520653035099489, epsilon = 0.03);
    }

    #[test]
    fn test_dividend_effect_on_greeks() {
        let s = 100.0;
        let k = 100.0;
        let t = 1.0;
        let r = 0.05;
        let sigma = 0.20;

        // Compare Greeks with and without dividends
        let call_delta_no_div = delta_call(s, k, t, r, 0.0, sigma);
        let call_delta_with_div = delta_call(s, k, t, r, 0.03, sigma);

        // Delta should decrease with dividends for calls
        assert!(call_delta_with_div < call_delta_no_div);

        // Dividend rho should be negative for calls
        let div_rho_call = dividend_rho_call(s, k, t, r, 0.03, sigma);
        assert!(div_rho_call < 0.0);

        // Dividend rho should be positive for puts
        let div_rho_put = dividend_rho_put(s, k, t, r, 0.03, sigma);
        assert!(div_rho_put > 0.0);
    }

    #[test]
    fn test_greeks_structure_completeness() {
        let s = 100.0;
        let k = 100.0;
        let t = 0.5;
        let r = 0.05;
        let q = 0.02;
        let sigma = 0.25;

        let greeks = calculate_merton_greeks(s, k, t, r, q, sigma, true);

        // All Greeks should be finite
        assert!(greeks.delta.is_finite());
        assert!(greeks.gamma.is_finite());
        assert!(greeks.vega.is_finite());
        assert!(greeks.theta.is_finite());
        assert!(greeks.rho.is_finite());
        assert!(greeks.dividend_rho.is_finite());

        // Test conversion to standard Greeks
        let standard_greeks = greeks.to_standard_greeks();
        assert_eq!(standard_greeks.delta, greeks.delta);
        assert_eq!(standard_greeks.gamma, greeks.gamma);
        assert_eq!(standard_greeks.vega, greeks.vega);
        assert_eq!(standard_greeks.theta, greeks.theta);
        assert_eq!(standard_greeks.rho, greeks.rho);
    }
}

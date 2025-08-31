//! Bjerksund-Stensland 2002 American option pricing implementation

use crate::constants::{BS2002_BETA_MIN, BS2002_H_FACTOR};
use crate::error::QuantForgeResult;
use crate::math::distributions::norm_cdf;

/// Parameters for American option pricing
#[derive(Debug, Clone, Copy)]
pub struct AmericanParams {
    pub s: f64,     // Spot price
    pub k: f64,     // Strike price
    pub t: f64,     // Time to maturity
    pub r: f64,     // Risk-free rate
    pub q: f64,     // Dividend yield
    pub sigma: f64, // Volatility
}

impl AmericanParams {
    /// Cost of carry parameter (b = r - q)
    #[inline]
    pub fn b(&self) -> f64 {
        self.r - self.q
    }
}

/// Calculate American call option price using Bjerksund-Stensland 2002
pub fn american_call_price(params: &AmericanParams) -> QuantForgeResult<f64> {
    // Handle extreme moneyness to avoid numerical issues
    let moneyness = params.s / params.k;
    if moneyness > 100.0 {
        // Deep ITM call - essentially worth S - K*exp(-r*t)
        let intrinsic = params.s - params.k;
        let discounted = params.s - params.k * (-params.r * params.t).exp();
        return Ok(discounted.max(intrinsic).max(0.0));
    }
    if moneyness < 0.01 {
        // Deep OTM call - essentially worthless
        return Ok(0.0);
    }

    // If time to maturity is very small, return intrinsic value
    if params.t < 1e-10 {
        return Ok((params.s - params.k).max(0.0));
    }

    // For non-dividend paying calls, American equals European
    if params.q == 0.0 {
        let euro_price = european_call_price(params);
        let intrinsic = (params.s - params.k).max(0.0);
        return Ok(euro_price.max(intrinsic));
    }

    let result = bjerksund_stensland_2002(params, true);

    // Ensure result is at least intrinsic value
    let intrinsic = (params.s - params.k).max(0.0);
    if result.is_nan() || result.is_infinite() {
        // Fall back to European value for numerical stability
        let euro_price = european_call_price(params);
        return Ok(euro_price.max(intrinsic));
    }

    // Apply no-arbitrage bound: American >= max(intrinsic, European)
    let euro_price = european_call_price(params);
    Ok(result.max(intrinsic).max(euro_price))
}

/// Calculate American put option price using Bjerksund-Stensland 2002
pub fn american_put_price(params: &AmericanParams) -> QuantForgeResult<f64> {
    // Handle extreme moneyness to avoid numerical issues
    let moneyness = params.k / params.s;
    if moneyness > 100.0 {
        // Deep ITM put - essentially worth K*exp(-r*t) - S
        return Ok((params.k * (-params.r * params.t).exp() - params.s).max(0.0));
    }
    if moneyness < 0.01 {
        // Deep OTM put - essentially worthless
        return Ok(0.0);
    }

    // If time to maturity is very small, return intrinsic value
    if params.t < 1e-10 {
        return Ok((params.k - params.s).max(0.0));
    }

    // Use put-call transformation
    // P(S,K,T,r,q,σ) = C(K,S,T,q,r,σ)
    let transformed = AmericanParams {
        s: params.k,
        k: params.s,
        t: params.t,
        r: params.q,
        q: params.r,
        sigma: params.sigma,
    };

    let result = bjerksund_stensland_2002(&transformed, false);

    // Calculate intrinsic value first (needed in multiple places)
    let intrinsic = (params.k - params.s).max(0.0);

    // Ensure non-negative result and at least intrinsic value
    if result.is_nan() || result.is_infinite() {
        // Fall back to European value for numerical stability
        let euro_price = european_put_price(params);
        return Ok(euro_price.max(intrinsic));
    }

    // Apply no-arbitrage bound: American >= max(intrinsic, European)
    let euro_price = european_put_price(params);
    Ok(result.max(intrinsic).max(euro_price))
}

/// Main Bjerksund-Stensland 2002 algorithm
fn bjerksund_stensland_2002(params: &AmericanParams, _is_original_call: bool) -> f64 {
    let b = params.b();
    let v2 = params.sigma * params.sigma;

    // Calculate beta
    let beta = calculate_beta(params.r, b, v2);

    // Calculate B∞ and B0
    let b_infinity = calculate_b_infinity(params.k, params.r, b, v2, beta);
    let b_zero = calculate_b_zero(params.k, params.r, b);

    // Calculate h(T) and I (trigger price)
    let h_t = -(b * params.t + BS2002_H_FACTOR * params.sigma * params.t.sqrt());
    // Use exp_m1 for numerical stability: 1 - exp(h_t) = -exp_m1(h_t)
    let i = b_zero + (b_infinity - b_zero) * (-h_t.exp_m1());

    // If S >= I, immediate exercise is optimal
    // Use strict inequality to avoid numerical issues at ATM
    if params.s > i * (1.0 + 1e-10) {
        return (params.s - params.k).max(0.0);
    }

    // Calculate alpha
    let alpha = (i - params.k) * i.powf(-beta);

    // Calculate the option value using phi functions
    let result = alpha * params.s.powf(beta) - alpha * phi(params.s, params.t, beta, i, i, params)
        + phi(params.s, params.t, 1.0, i, i, params)
        - phi(params.s, params.t, 1.0, params.k, i, params)
        - params.k * phi(params.s, params.t, 0.0, i, i, params)
        + params.k * phi(params.s, params.t, 0.0, params.k, i, params);

    // Ensure result is not NaN and at least intrinsic value
    if result.is_nan() || result.is_infinite() {
        return 0.0;
    }

    result.max(0.0)
}

/// Calculate the beta parameter
fn calculate_beta(r: f64, b: f64, v2: f64) -> f64 {
    let beta = (0.5 - b / v2) + ((b / v2 - 0.5).powi(2) + 2.0 * r / v2).sqrt();
    beta.max(BS2002_BETA_MIN)
}

/// Calculate B∞ (asymptotic exercise boundary)
fn calculate_b_infinity(k: f64, _r: f64, _b: f64, _v2: f64, beta: f64) -> f64 {
    beta * k / (beta - 1.0)
}

/// Calculate B0 (immediate exercise boundary)
fn calculate_b_zero(k: f64, r: f64, b: f64) -> f64 {
    if b >= r {
        k
    } else {
        k.max(r * k / b)
    }
}

/// Phi auxiliary function
fn phi(s: f64, t: f64, gamma: f64, h: f64, i: f64, params: &AmericanParams) -> f64 {
    let b = params.b();
    let v = params.sigma;
    let v2 = v * v;

    let lambda = (-params.r + gamma * b + 0.5 * gamma * (gamma - 1.0) * v2) * t;
    let d1 = -((s / h).ln() + (b + (gamma - 0.5) * v2) * t) / (v * t.sqrt());
    let d2 = -((i.powi(2) / (s * h)).ln() + (b + (gamma - 0.5) * v2) * t) / (v * t.sqrt());

    let kappa = 2.0 * b / v2 + 2.0 * gamma - 1.0;

    lambda.exp() * s.powf(gamma) * (norm_cdf(d1) - (i / s).powf(kappa) * norm_cdf(d2))
}

/// Psi auxiliary function (for future use in more complex scenarios)
#[allow(dead_code, clippy::too_many_arguments)]
fn psi(
    s: f64,
    t2: f64,
    gamma: f64,
    h: f64,
    i2: f64,
    i1: f64,
    t1: f64,
    params: &AmericanParams,
) -> f64 {
    let b = params.b();
    let v = params.sigma;
    let v2 = v * v;
    let r = params.r;

    // Calculate e1-e4 terms
    let vsqrt_t1 = v * t1.sqrt();
    let e1 = ((s / i1).ln() + (b + (gamma - 0.5) * v2) * t1) / vsqrt_t1;
    let e2 = ((i2.powi(2) / (s * i1)).ln() + (b + (gamma - 0.5) * v2) * t1) / vsqrt_t1;

    let vsqrt_t2 = v * t2.sqrt();
    let e3 = ((s / h).ln() + (b + (gamma - 0.5) * v2) * t2) / vsqrt_t2;
    let e4 = ((i2.powi(2) / (s * h)).ln() + (b + (gamma - 0.5) * v2) * t2) / vsqrt_t2;

    let lambda = (-r + gamma * b + 0.5 * gamma * (gamma - 1.0) * v2) * t2;
    let kappa = 2.0 * b / v2 + (2.0 * gamma - 1.0);

    let rho = ((2.0 * b + v2 * (2.0 * gamma - 1.0)) * t1 / v2).sqrt() / vsqrt_t2;

    lambda.exp()
        * s.powf(gamma)
        * (cbnd(-e1, -e3, rho) - (i2 / s).powf(kappa) * cbnd(-e2, -e4, rho))
}

/// Cumulative bivariate normal distribution
fn cbnd(a: f64, b: f64, rho: f64) -> f64 {
    // Handle extreme values to avoid NaN
    if a.abs() > 8.0 || b.abs() > 8.0 {
        // For extreme values, use limiting behavior
        if a > 8.0 && b > 8.0 {
            return 1.0;
        }
        if a < -8.0 || b < -8.0 {
            return 0.0;
        }
        // One extreme, one normal - use univariate approximation
        if a.abs() > 8.0 {
            return if a > 0.0 { norm_cdf(b) } else { 0.0 };
        }
        if b.abs() > 8.0 {
            return if b > 0.0 { norm_cdf(a) } else { 0.0 };
        }
    }

    // Handle special cases
    if (rho - 1.0).abs() < 1e-10 {
        return norm_cdf(a.min(b));
    }
    if (rho + 1.0).abs() < 1e-10 {
        return (norm_cdf(a) + norm_cdf(b) - 1.0).max(0.0);
    }

    // Drezner-Wesolowsky approximation for general case
    let a1 = a / (2.0 * (1.0 - rho * rho)).sqrt();
    let b1 = b / (2.0 * (1.0 - rho * rho)).sqrt();

    // Gauss-Legendre quadrature weights and abscissae
    let weights = [0.0796, 0.0773, 0.0670, 0.0500, 0.0278];
    let nodes = [0.9815, 0.9041, 0.7699, 0.5873, 0.3678];

    let mut result = 0.0;
    for i in 0..5 {
        let x = nodes[i];
        let w = weights[i];

        let sin_x = (x * std::f64::consts::PI * 0.5).sin();
        let cos_x = (x * std::f64::consts::PI * 0.5).cos();

        let val1 = norm_cdf(a1 - rho * sin_x / cos_x) * norm_cdf(b1 - sin_x / cos_x);
        let val2 = norm_cdf(a1 + rho * sin_x / cos_x) * norm_cdf(b1 + sin_x / cos_x);

        result += w * (val1 + val2);
    }

    result * std::f64::consts::PI * 0.25 + norm_cdf(a) * norm_cdf(b)
}

/// European call price (Black-Scholes formula) for comparison
fn european_call_price(params: &AmericanParams) -> f64 {
    let b = params.b();
    let sqrt_t = params.t.sqrt();
    let d1 = ((params.s / params.k).ln() + (b + 0.5 * params.sigma * params.sigma) * params.t)
        / (params.sigma * sqrt_t);
    let d2 = d1 - params.sigma * sqrt_t;

    params.s * ((-params.q * params.t).exp()) * norm_cdf(d1)
        - params.k * ((-params.r * params.t).exp()) * norm_cdf(d2)
}

/// European put price (Black-Scholes formula) for comparison
fn european_put_price(params: &AmericanParams) -> f64 {
    let b = params.b();
    let sqrt_t = params.t.sqrt();
    let d1 = ((params.s / params.k).ln() + (b + 0.5 * params.sigma * params.sigma) * params.t)
        / (params.sigma * sqrt_t);
    let d2 = d1 - params.sigma * sqrt_t;

    params.k * ((-params.r * params.t).exp()) * norm_cdf(-d2)
        - params.s * ((-params.q * params.t).exp()) * norm_cdf(-d1)
}

//! Simplified American option implementation for testing
//! Based on Haug (2007) formulas

use super::formulas::black_scholes_call_scalar;

/// Simplified BS2002 for testing - American call with dividends
pub fn american_call_simple(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // If no dividends, American call = European call
    if q <= 0.0 {
        return black_scholes_call_scalar(s, k, t, r, sigma);
    }

    // Near expiry
    if t < 1e-10 {
        return (s - k).max(0.0);
    }

    // For now, use simple approximation: European value + early exercise premium estimate
    // This is a placeholder for testing while we debug BS2002
    let european_value = black_scholes_call_scalar(s * (-q * t).exp(), k, t, r - q, sigma);

    // Simple early exercise premium estimate (not accurate but bounded)
    let early_ex_premium = if q > r {
        // High dividend case - more likely to exercise early
        let intrinsic = (s - k).max(0.0);
        (intrinsic - european_value).max(0.0) * 0.5 // Conservative estimate
    } else {
        0.0 // Low dividend - early exercise less likely
    };

    european_value + early_ex_premium
}

/// Simplified American put using put-call transformation
pub fn american_put_simple(s: f64, k: f64, t: f64, r: f64, q: f64, sigma: f64) -> f64 {
    // Near expiry
    if t < 1e-10 {
        return (k - s).max(0.0);
    }

    // Use put-call transformation
    american_call_simple(k, s, t, q, r, sigma)
}

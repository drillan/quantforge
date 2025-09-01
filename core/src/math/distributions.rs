//! Statistical distribution functions optimized for Arrow arrays

use crate::constants::INV_SQRT_2PI;
use arrow::array::{ArrayRef, Float64Array};
use arrow::compute::kernels::arity::unary;
use arrow::error::ArrowError;
use libm::erf;
use std::sync::Arc;

/// Standard normal cumulative distribution function for Arrow arrays
///
/// Uses the error function (erf) for high precision calculation.
/// Φ(x) = (1 + erf(x/√2)) / 2
///
/// # Arguments
/// * `x` - Arrow Float64Array of values
///
/// # Returns
/// Arrow Float64Array of CDF values
pub fn norm_cdf_array(x: &Float64Array) -> Result<ArrayRef, ArrowError> {
    let sqrt_2 = std::f64::consts::SQRT_2;

    let result: Float64Array = unary(x, move |x_val| {
        if x_val.is_nan() {
            f64::NAN
        } else if x_val > 8.0 {
            1.0
        } else if x_val < -8.0 {
            0.0
        } else {
            0.5 * (1.0 + erf(x_val / sqrt_2))
        }
    });

    Ok(Arc::new(result))
}

/// Standard normal probability density function for Arrow arrays
///
/// φ(x) = (1/√(2π)) × exp(-x²/2)
///
/// # Arguments
/// * `x` - Arrow Float64Array of values
///
/// # Returns
/// Arrow Float64Array of PDF values
pub fn norm_pdf_array(x: &Float64Array) -> Result<ArrayRef, ArrowError> {
    let result: Float64Array = unary(x, |x_val| {
        if x_val.is_nan() {
            f64::NAN
        } else if x_val.abs() > 40.0 {
            0.0
        } else {
            INV_SQRT_2PI * (-0.5 * x_val * x_val).exp()
        }
    });

    Ok(Arc::new(result))
}

/// Standard normal CDF for scalar values (backward compatibility)
#[inline]
pub fn norm_cdf_scalar(x: f64) -> f64 {
    if x.is_nan() {
        f64::NAN
    } else if x > 8.0 {
        1.0
    } else if x < -8.0 {
        0.0
    } else {
        0.5 * (1.0 + erf(x / std::f64::consts::SQRT_2))
    }
}

/// Standard normal PDF for scalar values (backward compatibility)
#[inline]
pub fn norm_pdf_scalar(x: f64) -> f64 {
    if x.is_nan() {
        f64::NAN
    } else if x.abs() > 40.0 {
        0.0
    } else {
        INV_SQRT_2PI * (-0.5 * x * x).exp()
    }
}

// Keep the old names for compatibility during migration
pub use norm_cdf_scalar as norm_cdf;
pub use norm_pdf_scalar as norm_pdf;

#[cfg(test)]
mod tests {
    use super::*;
    use crate::constants::NUMERICAL_TOLERANCE;

    #[test]
    fn test_norm_cdf_array() {
        let values = Float64Array::from(vec![0.0, 1.0, -1.0, 2.0, -2.0]);
        let result = norm_cdf_array(&values).unwrap();
        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        // Standard values
        assert!((result_array.value(0) - 0.5).abs() < NUMERICAL_TOLERANCE);
        assert!((result_array.value(1) - 0.8413447460685429).abs() < NUMERICAL_TOLERANCE);
        assert!((result_array.value(2) - 0.15865525393145707).abs() < NUMERICAL_TOLERANCE);
    }

    #[test]
    fn test_norm_pdf_array() {
        let values = Float64Array::from(vec![0.0, 1.0, -1.0]);
        let result = norm_pdf_array(&values).unwrap();
        let result_array = result.as_any().downcast_ref::<Float64Array>().unwrap();

        // φ(0) = 1/√(2π) ≈ 0.3989422804014327
        assert!((result_array.value(0) - 0.3989422804014327).abs() < 1e-15);

        // φ(1) = φ(-1) by symmetry
        assert!((result_array.value(1) - result_array.value(2)).abs() < 1e-15);
    }

    #[test]
    fn test_scalar_compatibility() {
        let test_values = vec![0.0, 0.5, 1.0, -1.0, 2.0];

        for x in test_values {
            let array = Float64Array::from(vec![x]);
            let array_result = norm_cdf_array(&array).unwrap();
            let array_value = array_result
                .as_any()
                .downcast_ref::<Float64Array>()
                .unwrap()
                .value(0);

            let scalar_value = norm_cdf_scalar(x);

            assert!(
                (array_value - scalar_value).abs() < 1e-15,
                "Mismatch for x={x}: array={array_value}, scalar={scalar_value}"
            );
        }
    }
}

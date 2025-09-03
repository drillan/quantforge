//! Arrow-native computation kernels for option pricing

pub mod american;
pub mod american_simple;
pub mod arrow_native;
pub mod black76;
pub mod black_scholes;
pub mod formulas;
pub mod greeks;
pub mod merton;

// Re-export for convenience
pub use american::American;
pub use arrow_native::ArrowNativeCompute;
pub use black76::Black76;
pub use black_scholes::BlackScholes;
pub use greeks::calculate_greeks;
pub use merton::Merton;

use arrow::array::Float64Array;

/// Get value from array with broadcasting support
/// If array has length 1, use that value for all indices (scalar broadcasting)
/// Otherwise, use the value at the given index
#[inline(always)]
pub fn get_scalar_or_array_value(array: &Float64Array, index: usize) -> f64 {
    if array.len() == 1 {
        array.value(0) // Scalar value applied to all
    } else {
        array.value(index) // Array value at index
    }
}

/// Get the maximum length from multiple arrays
/// Used to determine output length for broadcasting operations
pub fn get_max_length(arrays: &[&Float64Array]) -> usize {
    arrays.iter().map(|a| a.len()).max().unwrap_or(0)
}

/// Validate arrays for broadcasting compatibility
/// Arrays must have length 1 (scalar) or the same length as the maximum
pub fn validate_broadcast_compatibility(
    arrays: &[&Float64Array],
) -> Result<usize, arrow::error::ArrowError> {
    let max_len = get_max_length(arrays);

    // Allow empty arrays - return 0 for length
    if max_len == 0 {
        return Ok(0);
    }

    for (i, array) in arrays.iter().enumerate() {
        if array.len() != 1 && array.len() != max_len {
            return Err(arrow::error::ArrowError::InvalidArgumentError(format!(
                "Array at index {} has incompatible length {} for broadcasting (expected 1 or {})",
                i,
                array.len(),
                max_len
            )));
        }
    }

    Ok(max_len)
}

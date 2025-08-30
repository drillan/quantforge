//! Loop unrolling optimization for cache-friendly batch processing
//!
//! Processes data in chunks of 4 elements to help compiler auto-vectorization.

use crate::models::black_scholes::{bs_call_price, bs_put_price};

/// Process batch of call prices with 4-way loop unrolling
///
/// This helps the compiler generate SIMD instructions automatically
/// while maintaining readable and maintainable code.
#[inline(always)]
pub fn call_price_unrolled_4(
    spots: &[f64],
    k: f64,
    t: f64,
    r: f64,
    sigma: f64,
    output: &mut [f64],
) {
    // Process chunks of 4 for better cache utilization
    let chunks = spots.chunks_exact(4);
    let remainder = chunks.remainder();
    let mut out_chunks = output.chunks_exact_mut(4);

    // Process aligned chunks
    for (chunk, out_chunk) in chunks.zip(&mut out_chunks) {
        // Unrolled computation - compiler can auto-vectorize this
        out_chunk[0] = bs_call_price(chunk[0], k, t, r, sigma);
        out_chunk[1] = bs_call_price(chunk[1], k, t, r, sigma);
        out_chunk[2] = bs_call_price(chunk[2], k, t, r, sigma);
        out_chunk[3] = bs_call_price(chunk[3], k, t, r, sigma);
    }

    // Handle remainder
    let out_remainder = out_chunks.into_remainder();
    for (i, &spot) in remainder.iter().enumerate() {
        out_remainder[i] = bs_call_price(spot, k, t, r, sigma);
    }
}

/// Process batch of put prices with 4-way loop unrolling
#[inline(always)]
pub fn put_price_unrolled_4(spots: &[f64], k: f64, t: f64, r: f64, sigma: f64, output: &mut [f64]) {
    // Process chunks of 4 for better cache utilization
    let chunks = spots.chunks_exact(4);
    let remainder = chunks.remainder();
    let mut out_chunks = output.chunks_exact_mut(4);

    // Process aligned chunks
    for (chunk, out_chunk) in chunks.zip(&mut out_chunks) {
        // Unrolled computation - compiler can auto-vectorize this
        out_chunk[0] = bs_put_price(chunk[0], k, t, r, sigma);
        out_chunk[1] = bs_put_price(chunk[1], k, t, r, sigma);
        out_chunk[2] = bs_put_price(chunk[2], k, t, r, sigma);
        out_chunk[3] = bs_put_price(chunk[3], k, t, r, sigma);
    }

    // Handle remainder
    let out_remainder = out_chunks.into_remainder();
    for (i, &spot) in remainder.iter().enumerate() {
        out_remainder[i] = bs_put_price(spot, k, t, r, sigma);
    }
}

/// Generic unrolled batch processor for any function
#[inline(always)]
pub fn process_batch_unrolled_4<F>(input: &[f64], output: &mut [f64], processor: F)
where
    F: Fn(f64) -> f64,
{
    let chunks = input.chunks_exact(4);
    let remainder = chunks.remainder();
    let mut out_chunks = output.chunks_exact_mut(4);

    // Process aligned chunks
    for (chunk, out_chunk) in chunks.zip(&mut out_chunks) {
        out_chunk[0] = processor(chunk[0]);
        out_chunk[1] = processor(chunk[1]);
        out_chunk[2] = processor(chunk[2]);
        out_chunk[3] = processor(chunk[3]);
    }

    // Handle remainder
    let out_remainder = out_chunks.into_remainder();
    for (i, &value) in remainder.iter().enumerate() {
        out_remainder[i] = processor(value);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_call_price_unrolled() {
        let spots = vec![100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0];
        let mut output = vec![0.0; spots.len()];

        call_price_unrolled_4(&spots, 100.0, 1.0, 0.05, 0.2, &mut output);

        // Verify all elements were processed
        assert!(output.iter().all(|&x| x > 0.0));

        // Verify correctness for known values
        for (i, &spot) in spots.iter().enumerate() {
            let expected = bs_call_price(spot, 100.0, 1.0, 0.05, 0.2);
            assert!((output[i] - expected).abs() < 1e-10);
        }
    }

    #[test]
    fn test_process_batch_unrolled() {
        let input = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let mut output = vec![0.0; input.len()];

        process_batch_unrolled_4(&input, &mut output, |x| x * x);

        assert_eq!(output, vec![1.0, 4.0, 9.0, 16.0, 25.0]);
    }
}

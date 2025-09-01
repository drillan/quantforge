//! Broadcasting support for array operations

use super::ArrayLike;
use numpy::PyUntypedArrayMethods;

/// Iterator that broadcasts arrays to the same length
pub struct BroadcastIterator<'a> {
    pub(crate) inputs: Vec<&'a ArrayLike<'a>>,
    length: usize,
    position: usize,
}

impl<'a> BroadcastIterator<'a> {
    /// Create a new broadcast iterator from ArrayLike inputs
    #[allow(dead_code)]
    pub fn new(inputs: Vec<&'a ArrayLike<'a>>) -> Result<Self, String> {
        // Check if any input is empty array (not scalar)
        // If any array is empty, the result should be empty
        for input in &inputs {
            if let ArrayLike::Array(arr) = input {
                if arr.len() == 0 {
                    // Return empty iterator if any array is empty
                    return Ok(Self {
                        inputs: vec![],
                        length: 0,
                        position: 0,
                    });
                }
            }
        }

        // Find the maximum length (excluding empty arrays)
        let mut max_len = 0;
        for input in &inputs {
            let len = input.len();
            if len > 1 && max_len > 1 && len != max_len {
                return Err(format!(
                    "Shape mismatch: cannot broadcast arrays of length {len} and {max_len}"
                ));
            }
            max_len = max_len.max(len);
        }

        // This should not happen after the empty check above
        if max_len == 0 {
            return Ok(Self {
                inputs: vec![],
                length: 0,
                position: 0,
            });
        }

        Ok(Self {
            inputs,
            length: max_len,
            position: 0,
        })
    }

    /// Get the broadcast length
    #[allow(dead_code)]
    pub fn len(&self) -> usize {
        self.length
    }

    /// Check if empty
    #[allow(dead_code)]
    pub fn is_empty(&self) -> bool {
        self.length == 0
    }

    /// Compute results using a function without copying data (zero-copy)
    /// Sequential processing for small data
    #[allow(dead_code)]
    pub fn compute_with<F>(&self, f: F) -> Vec<f64>
    where
        F: Fn(&[f64]) -> f64,
    {
        let mut results = Vec::with_capacity(self.length);
        let mut buffer = vec![0.0; self.inputs.len()];

        for i in 0..self.length {
            for (j, input) in self.inputs.iter().enumerate() {
                // Use get_broadcast for zero-copy access
                buffer[j] = input.get_broadcast(i).unwrap_or(f64::NAN);
            }
            results.push(f(&buffer));
        }

        results
    }

    /// Compute results in parallel using a function without copying data (zero-copy)
    /// Parallel processing for large data
    /// NOTE: This module is deprecated, use BroadcastIteratorOptimized instead
    #[allow(dead_code)]
    pub fn compute_parallel_with<F>(&self, _f: F, _chunk_size: usize) -> Vec<f64>
    where
        F: Fn(&[f64]) -> f64 + Send + Sync,
    {
        // Deprecated: Use BroadcastIteratorOptimized instead
        // This implementation has thread safety issues with PyO3
        vec![]
    }
}

impl<'a> Iterator for BroadcastIterator<'a> {
    type Item = Vec<f64>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.position >= self.length {
            return None;
        }

        let values: Vec<f64> = self.inputs
            .iter()
            .map(|input| input.get_broadcast(self.position).unwrap_or(f64::NAN))
            .collect();

        self.position += 1;
        Some(values)
    }
}

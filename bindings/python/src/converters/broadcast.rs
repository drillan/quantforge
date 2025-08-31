//! Broadcasting support for array operations

use super::ArrayLike;
use numpy::PyUntypedArrayMethods;

/// Iterator that broadcasts arrays to the same length
pub struct BroadcastIterator {
    pub(crate) arrays: Vec<Vec<f64>>,
    length: usize,
    position: usize,
}

impl BroadcastIterator {
    /// Create a new broadcast iterator from ArrayLike inputs
    pub fn new(inputs: Vec<&ArrayLike>) -> Result<Self, String> {
        // Check if any input is empty array (not scalar)
        // If any array is empty, the result should be empty
        for input in &inputs {
            if let ArrayLike::Array(arr) = input {
                if arr.len() == 0 {
                    // Return empty iterator if any array is empty
                    return Ok(Self {
                        arrays: vec![],
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
                arrays: vec![],
                length: 0,
                position: 0,
            });
        }

        // Convert all inputs to Vec with broadcasting
        let arrays: Vec<Vec<f64>> = inputs
            .into_iter()
            .map(|input| match input {
                ArrayLike::Scalar(val) => vec![*val; max_len],
                ArrayLike::Array(arr) => {
                    let vec = arr
                        .as_slice()
                        .map(|s| s.to_vec())
                        .unwrap_or_else(|_| vec![0.0; max_len]);
                    if vec.is_empty() {
                        vec![]
                    } else if vec.len() == 1 {
                        vec![vec[0]; max_len]
                    } else {
                        vec
                    }
                }
            })
            .collect();

        Ok(Self {
            arrays,
            length: max_len,
            position: 0,
        })
    }

    /// Get the broadcast length
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
    pub fn compute_with<F>(&self, f: F) -> Vec<f64>
    where
        F: Fn(&[f64]) -> f64,
    {
        let mut results = Vec::with_capacity(self.length);
        let mut buffer = vec![0.0; self.arrays.len()];

        for i in 0..self.length {
            for (j, arr) in self.arrays.iter().enumerate() {
                buffer[j] = arr[i];
            }
            results.push(f(&buffer));
        }

        results
    }

    /// Compute results in parallel using a function without copying data (zero-copy)
    /// Parallel processing for large data
    pub fn compute_parallel_with<F>(&self, f: F, chunk_size: usize) -> Vec<f64>
    where
        F: Fn(&[f64]) -> f64 + Send + Sync,
    {
        use rayon::prelude::*;

        let num_inputs = self.arrays.len();

        (0..self.length)
            .into_par_iter()
            .chunks(chunk_size)
            .flat_map(|chunk| {
                let mut buffer = vec![0.0; num_inputs];
                let mut chunk_results = Vec::with_capacity(chunk.len());

                for i in chunk {
                    for (j, arr) in self.arrays.iter().enumerate() {
                        buffer[j] = arr[i];
                    }
                    chunk_results.push(f(&buffer));
                }

                chunk_results
            })
            .collect()
    }
}

impl Iterator for BroadcastIterator {
    type Item = Vec<f64>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.position >= self.length {
            return None;
        }

        let values: Vec<f64> = self.arrays.iter().map(|arr| arr[self.position]).collect();

        self.position += 1;
        Some(values)
    }
}

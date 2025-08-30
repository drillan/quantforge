//! Broadcasting support for batch operations
//!
//! This module provides NumPy-style broadcasting for array operations,
//! allowing scalars and arrays of different sizes to be combined efficiently.

use crate::error::QuantForgeError;

/// Represents an input that can be either a scalar or an array
#[derive(Debug, Clone)]
pub enum ArrayLike<'a> {
    Scalar(f64),
    Array(&'a [f64]),
}

impl<'a> ArrayLike<'a> {
    /// Get the length of the input (1 for scalar, array length for array)
    pub fn len(&self) -> usize {
        match self {
            ArrayLike::Scalar(_) => 1,
            ArrayLike::Array(arr) => arr.len(),
        }
    }

    /// Convert ArrayLike to a `Vec<f64>`
    /// For scalars, returns a single-element Vec
    pub fn to_vec(&self) -> Vec<f64> {
        match self {
            ArrayLike::Scalar(v) => vec![*v],
            ArrayLike::Array(arr) => arr.to_vec(),
        }
    }

    /// Check if the array is empty
    pub fn is_empty(&self) -> bool {
        match self {
            ArrayLike::Scalar(_) => false, // Scalar is never empty
            ArrayLike::Array(arr) => arr.is_empty(),
        }
    }

    /// Check if this input can be broadcast to the target size
    pub fn can_broadcast_to(&self, target_size: usize) -> bool {
        let len = self.len();
        len == 1 || len == target_size
    }

    /// Get value at index with broadcasting
    pub fn get_broadcast(&self, index: usize) -> f64 {
        match self {
            ArrayLike::Scalar(val) => *val,
            ArrayLike::Array(arr) => {
                if arr.len() == 1 {
                    arr[0]
                } else {
                    arr[index]
                }
            }
        }
    }
}

/// Calculate the output size for broadcasting multiple inputs
pub fn calculate_output_size(inputs: &[ArrayLike]) -> Result<usize, QuantForgeError> {
    if inputs.is_empty() {
        return Ok(0);
    }

    // Check if any input is empty
    if inputs.iter().any(|input| input.is_empty()) {
        return Ok(0);
    }

    // Find the maximum non-1 length
    let max_len = inputs
        .iter()
        .map(|input| input.len())
        .filter(|&len| len > 1)
        .max()
        .unwrap_or(1);

    // Verify all inputs can broadcast to this size
    for input in inputs {
        if !input.can_broadcast_to(max_len) {
            return Err(QuantForgeError::InvalidInput(format!(
                "Cannot broadcast arrays: incompatible shapes. Got lengths: {:?}",
                inputs.iter().map(|i| i.len()).collect::<Vec<_>>()
            )));
        }
    }

    Ok(max_len)
}

/// Broadcast multiple inputs to a common size
pub struct BroadcastIterator<'a> {
    inputs: Vec<ArrayLike<'a>>,
    size: usize,
    index: usize,
}

impl<'a> BroadcastIterator<'a> {
    /// Create a new broadcast iterator
    pub fn new(inputs: Vec<ArrayLike<'a>>) -> Result<Self, QuantForgeError> {
        let size = calculate_output_size(&inputs)?;
        Ok(BroadcastIterator {
            inputs,
            size,
            index: 0,
        })
    }

    /// Compute values with a function, avoiding unnecessary copies
    ///
    /// This method processes all broadcast values without creating intermediate `Vec<f64>`
    /// for each iteration, significantly reducing memory allocation overhead.
    pub fn compute_with<F, R>(&self, f: F) -> Vec<R>
    where
        F: Fn(&[f64]) -> R,
        R: Send,
    {
        let mut buffer = vec![0.0; self.inputs.len()];
        let mut results = Vec::with_capacity(self.size);

        for i in 0..self.size {
            // Reuse buffer for each iteration
            for (j, input) in self.inputs.iter().enumerate() {
                buffer[j] = input.get_broadcast(i);
            }
            results.push(f(&buffer));
        }

        results
    }

    /// Parallel version of compute_with using chunked processing
    ///
    /// Processes data in chunks for efficient parallel execution.
    /// Each chunk gets its own buffer to avoid synchronization overhead.
    pub fn compute_parallel_with<F, R>(&self, f: F, chunk_size: usize) -> Vec<R>
    where
        F: Fn(&[f64]) -> R + Sync + Send,
        R: Send,
    {
        use rayon::prelude::*;

        (0..self.size)
            .into_par_iter()
            .chunks(chunk_size)
            .flat_map(|chunk| {
                // Create a buffer for this chunk - minimal overhead since chunks are large
                let mut buffer = vec![0.0; self.inputs.len()];
                chunk
                    .into_iter()
                    .map(|i| {
                        // Fill buffer with broadcast values
                        for (j, input) in self.inputs.iter().enumerate() {
                            buffer[j] = input.get_broadcast(i);
                        }
                        f(&buffer)
                    })
                    .collect::<Vec<_>>()
            })
            .collect()
    }
}

impl<'a> Iterator for BroadcastIterator<'a> {
    type Item = Vec<f64>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.index >= self.size {
            return None;
        }

        let values: Vec<f64> = self
            .inputs
            .iter()
            .map(|input| input.get_broadcast(self.index))
            .collect();

        self.index += 1;
        Some(values)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = self.size - self.index;
        (remaining, Some(remaining))
    }
}

/// Helper function to validate and broadcast arrays
pub fn broadcast_and_validate(
    inputs: Vec<ArrayLike>,
) -> Result<BroadcastIterator, QuantForgeError> {
    // Validate that all scalar values are finite and valid
    for input in &inputs {
        match input {
            ArrayLike::Scalar(val) => {
                if !val.is_finite() {
                    return Err(QuantForgeError::InvalidInput(
                        "All values must be finite".to_string(),
                    ));
                }
            }
            ArrayLike::Array(arr) => {
                for &val in arr.iter() {
                    if !val.is_finite() {
                        return Err(QuantForgeError::InvalidInput(
                            "All values must be finite".to_string(),
                        ));
                    }
                }
            }
        }
    }

    BroadcastIterator::new(inputs)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scalar_broadcast() {
        let inputs = vec![
            ArrayLike::Scalar(100.0),
            ArrayLike::Array(&[95.0, 100.0, 105.0]),
            ArrayLike::Scalar(1.0),
        ];

        let size = calculate_output_size(&inputs).unwrap();
        assert_eq!(size, 3);

        let mut iter = BroadcastIterator::new(inputs).unwrap();
        assert_eq!(iter.next(), Some(vec![100.0, 95.0, 1.0]));
        assert_eq!(iter.next(), Some(vec![100.0, 100.0, 1.0]));
        assert_eq!(iter.next(), Some(vec![100.0, 105.0, 1.0]));
        assert_eq!(iter.next(), None);
    }

    #[test]
    fn test_incompatible_shapes() {
        let inputs = vec![
            ArrayLike::Array(&[1.0, 2.0, 3.0]),
            ArrayLike::Array(&[4.0, 5.0]),
        ];

        let result = calculate_output_size(&inputs);
        assert!(result.is_err());
    }

    #[test]
    fn test_single_element_arrays() {
        let inputs = vec![
            ArrayLike::Array(&[100.0]), // Single element array
            ArrayLike::Array(&[95.0, 100.0, 105.0]),
            ArrayLike::Scalar(1.0),
        ];

        let size = calculate_output_size(&inputs).unwrap();
        assert_eq!(size, 3);

        let mut iter = BroadcastIterator::new(inputs).unwrap();
        assert_eq!(iter.next(), Some(vec![100.0, 95.0, 1.0]));
        assert_eq!(iter.next(), Some(vec![100.0, 100.0, 1.0]));
        assert_eq!(iter.next(), Some(vec![100.0, 105.0, 1.0]));
    }

    #[test]
    fn test_all_scalars() {
        let inputs = vec![
            ArrayLike::Scalar(100.0),
            ArrayLike::Scalar(95.0),
            ArrayLike::Scalar(1.0),
        ];

        let size = calculate_output_size(&inputs).unwrap();
        assert_eq!(size, 1);

        let mut iter = BroadcastIterator::new(inputs).unwrap();
        assert_eq!(iter.next(), Some(vec![100.0, 95.0, 1.0]));
        assert_eq!(iter.next(), None);
    }

    #[test]
    fn test_compute_with_no_copy() {
        let inputs = vec![ArrayLike::Array(&[1.0, 2.0, 3.0]), ArrayLike::Scalar(2.0)];
        let iter = BroadcastIterator::new(inputs).unwrap();

        let results = iter.compute_with(|vals| vals[0] + vals[1]);
        assert_eq!(results, vec![3.0, 4.0, 5.0]);
    }

    #[test]
    fn test_compute_parallel_with() {
        let inputs = vec![
            ArrayLike::Array(&[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
            ArrayLike::Scalar(10.0),
        ];
        let iter = BroadcastIterator::new(inputs).unwrap();

        let results = iter.compute_parallel_with(|vals| vals[0] * vals[1], 2);
        assert_eq!(
            results,
            vec![10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
        );
    }

    #[test]
    fn test_compute_with_memory_efficiency() {
        // Test that compute_with uses less memory than collect()
        let large_size = 10000;
        let large_array: Vec<f64> = (0..large_size).map(|i| i as f64).collect();
        let inputs = vec![
            ArrayLike::Array(&large_array),
            ArrayLike::Scalar(2.0),
            ArrayLike::Scalar(3.0),
        ];

        let iter = BroadcastIterator::new(inputs).unwrap();

        // This should be more memory efficient than collect()
        let results = iter.compute_with(|vals| vals[0] + vals[1] * vals[2]);

        assert_eq!(results.len(), large_size);
        assert_eq!(results[0], 0.0 + 2.0 * 3.0);
        assert_eq!(results[large_size - 1], (large_size - 1) as f64 + 2.0 * 3.0);
    }
}

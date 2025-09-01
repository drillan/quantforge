//! Optimized broadcasting support for array operations
//! 
//! This version minimizes memory allocation by working with slices where possible

use super::ArrayLike;
use numpy::{PyArrayMethods, PyUntypedArrayMethods};

/// Represents a broadcast input that can be a scalar or slice
pub enum BroadcastInput {
    Scalar(f64),
    Array(Vec<f64>),  // We need to own the data for lifetime reasons
}

impl BroadcastInput {
    /// Get value at index with broadcasting
    pub fn get_broadcast(&self, index: usize) -> f64 {
        match self {
            BroadcastInput::Scalar(val) => *val,
            BroadcastInput::Array(arr) => {
                if arr.len() == 1 {
                    arr[0]
                } else {
                    arr[index]
                }
            }
        }
    }
}

/// Optimized broadcast iterator that minimizes memory allocation
pub struct BroadcastIteratorOptimized {
    inputs: Vec<BroadcastInput>,
    length: usize,
}

impl BroadcastIteratorOptimized {
    /// Create a new broadcast iterator from ArrayLike inputs
    /// This version minimizes memory allocation by only copying when necessary
    pub fn new(inputs: Vec<&ArrayLike>) -> Result<Self, String> {
        // Check if any input is empty array (not scalar)
        for input in &inputs {
            if let ArrayLike::Array(arr) = input {
                if arr.len() == 0 {
                    // Return empty iterator if any array is empty
                    return Ok(Self {
                        inputs: vec![],
                        length: 0,
                    });
                }
            }
        }

        // Find the maximum length
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

        if max_len == 0 {
            return Ok(Self {
                inputs: vec![],
                length: 0,
            });
        }

        // Convert inputs, minimizing allocation
        let broadcast_inputs: Vec<BroadcastInput> = inputs
            .into_iter()
            .map(|input| match input {
                ArrayLike::Scalar(val) => BroadcastInput::Scalar(*val),
                ArrayLike::Array(arr) => {
                    // We need to copy the data here due to lifetime constraints
                    // But we only copy the actual data, not broadcast it
                    if let Ok(slice) = arr.as_slice() {
                        BroadcastInput::Array(slice.to_vec())
                    } else {
                        // Non-contiguous array - need to copy via to_vec
                        BroadcastInput::Array(arr.to_vec().unwrap_or_default())
                    }
                }
            })
            .collect();

        Ok(Self {
            inputs: broadcast_inputs,
            length: max_len,
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
    
    /// Get value at index for a specific input
    pub fn get_value_at(&self, input_index: usize, data_index: usize) -> f64 {
        if input_index >= self.inputs.len() || data_index >= self.length {
            f64::NAN
        } else {
            self.inputs[input_index].get_broadcast(data_index)
        }
    }

    /// Compute results using a function (sequential)
    pub fn compute_with<F>(&self, f: F) -> Vec<f64>
    where
        F: Fn(&[f64]) -> f64,
    {
        let mut results = Vec::with_capacity(self.length);
        let mut buffer = vec![0.0; self.inputs.len()];

        for i in 0..self.length {
            for (j, input) in self.inputs.iter().enumerate() {
                buffer[j] = input.get_broadcast(i);
            }
            results.push(f(&buffer));
        }

        results
    }

    /// Compute results in parallel
    pub fn compute_parallel_with<F>(&self, f: F, chunk_size: usize) -> Vec<f64>
    where
        F: Fn(&[f64]) -> f64 + Send + Sync,
    {
        use rayon::prelude::*;

        let num_inputs = self.inputs.len();

        (0..self.length)
            .into_par_iter()
            .chunks(chunk_size)
            .flat_map(|chunk| {
                let mut buffer = vec![0.0; num_inputs];
                let mut chunk_results = Vec::with_capacity(chunk.len());

                for i in chunk {
                    for (j, input) in self.inputs.iter().enumerate() {
                        buffer[j] = input.get_broadcast(i);
                    }
                    chunk_results.push(f(&buffer));
                }

                chunk_results
            })
            .collect()
    }
}
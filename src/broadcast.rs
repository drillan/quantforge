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
}

impl<'a> Iterator for BroadcastIterator<'a> {
    type Item = Vec<f64>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.index >= self.size {
            return None;
        }

        let values: Vec<f64> = self.inputs
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
            ArrayLike::Array(&[100.0]),  // Single element array
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
}
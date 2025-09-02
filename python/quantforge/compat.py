"""Compatibility layer for numpy arrays to Arrow arrays."""

import numpy as np
import pyarrow as pa
from typing import Union, Dict, Any

ArrayLike = Union[np.ndarray, pa.Array, float, int]


def to_arrow_array(arr: ArrayLike) -> pa.Array:
    """Convert input to Arrow array."""
    if isinstance(arr, pa.Array):
        return arr
    elif isinstance(arr, (np.ndarray, list)):
        return pa.array(arr, type=pa.float64())
    elif isinstance(arr, (float, int)):
        return pa.array([float(arr)], type=pa.float64())
    else:
        raise TypeError(f"Cannot convert {type(arr)} to Arrow array")


def from_arrow_array(arr: pa.Array) -> np.ndarray:
    """Convert Arrow array to numpy array."""
    return arr.to_numpy()


def ensure_all_same_length(*arrays: ArrayLike) -> int:
    """Ensure all arrays have the same length or are scalars."""
    lengths = []
    for arr in arrays:
        if isinstance(arr, (float, int)):
            lengths.append(1)
        elif isinstance(arr, (np.ndarray, list)):
            lengths.append(len(arr))
        elif isinstance(arr, pa.Array):
            lengths.append(len(arr))
        else:
            raise TypeError(f"Unsupported type: {type(arr)}")
    
    # Remove all 1s (scalars)
    non_scalar_lengths = [l for l in lengths if l > 1]
    
    if not non_scalar_lengths:
        return 1  # All scalars
    
    # Check all non-scalar arrays have same length
    if len(set(non_scalar_lengths)) > 1:
        raise ValueError(f"Arrays have incompatible lengths: {non_scalar_lengths}")
    
    return non_scalar_lengths[0]


def broadcast_arrays(*arrays: ArrayLike, length: int) -> tuple:
    """Broadcast arrays to the same length."""
    result = []
    for arr in arrays:
        if isinstance(arr, (float, int)):
            # Scalar - broadcast to length
            result.append(pa.array([float(arr)] * length, type=pa.float64()))
        elif isinstance(arr, (np.ndarray, list)):
            if len(arr) == 1:
                # Single element - broadcast
                result.append(pa.array([float(arr[0])] * length, type=pa.float64()))
            elif len(arr) == length:
                # Already correct length
                result.append(pa.array(arr, type=pa.float64()))
            else:
                raise ValueError(f"Cannot broadcast array of length {len(arr)} to {length}")
        elif isinstance(arr, pa.Array):
            if len(arr) == 1:
                # Single element - broadcast
                result.append(pa.array([arr[0].as_py()] * length, type=pa.float64()))
            elif len(arr) == length:
                result.append(arr)
            else:
                raise ValueError(f"Cannot broadcast array of length {len(arr)} to {length}")
        else:
            raise TypeError(f"Unsupported type: {type(arr)}")
    
    return tuple(result)
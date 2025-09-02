"""
Arrow FFI bridge for zero-copy operations.

This module provides a bridge between PyArrow and Rust using the Arrow C Data Interface.
It attempts to minimize data copies when passing arrays between Python and Rust.
"""

import ctypes

import numpy as np
import pyarrow as pa


class ArrowCDataInterface:
    """
    Helper class for Arrow C Data Interface operations.

    This class provides methods to work with PyArrow's PyCapsule interface
    for zero-copy data exchange.
    """

    @staticmethod
    def export_array(array: pa.Array) -> tuple[int, int]:
        """
        Export a PyArrow array to C Data Interface pointers.

        Parameters
        ----------
        array : pa.Array
            The PyArrow array to export

        Returns
        -------
        tuple[int, int]
            Pointers to FFI_ArrowArray and FFI_ArrowSchema
        """
        # PyCapsule Interface (Arrow 14.0+)
        if hasattr(array, "__arrow_c_array__"):
            capsule = array.__arrow_c_array__()
            # Extract pointers from PyCapsule
            # This is a simplified representation - actual implementation would need
            # proper PyCapsule handling
            return capsule

        # Fallback to legacy interface
        # Create C structs for Arrow Array and Schema
        c_array = ctypes.c_void_p()
        c_schema = ctypes.c_void_p()

        # Export using PyArrow's internal API
        # Note: This requires access to PyArrow's C API
        # In practice, this would need proper FFI bindings
        array._export_to_c(ctypes.addressof(c_array), ctypes.addressof(c_schema))

        return c_array.value, c_schema.value

    @staticmethod
    def import_array(array_ptr: int, schema_ptr: int) -> pa.Array:
        """
        Import an array from C Data Interface pointers.

        Parameters
        ----------
        array_ptr : int
            Pointer to FFI_ArrowArray
        schema_ptr : int
            Pointer to FFI_ArrowSchema

        Returns
        -------
        pa.Array
            The imported PyArrow array
        """
        # PyCapsule Interface (Arrow 14.0+)
        if hasattr(pa.Array, "_import_from_c_capsule"):
            # Create PyCapsule from pointers
            # This is a simplified representation
            capsule = (array_ptr, schema_ptr)
            return pa.Array._import_from_c_capsule(capsule)

        # Fallback to legacy interface
        return pa.Array._import_from_c(array_ptr, schema_ptr)


def prepare_arrow_arrays(*arrays: pa.Array) -> list:
    """
    Prepare Arrow arrays for FFI transfer.

    Ensures all arrays are Float64 and have compatible shapes.

    Parameters
    ----------
    *arrays : pa.Array
        Arrays to prepare

    Returns
    -------
    list[pa.Array]
        Prepared arrays
    """
    prepared = []

    for arr in arrays:
        # Ensure array type
        if not isinstance(arr, pa.Array):
            arr = pa.array(arr)

        # Cast to Float64 if needed
        if arr.type != pa.float64():
            arr = arr.cast(pa.float64())

        prepared.append(arr)

    return prepared


def arrays_to_numpy_fallback(*arrays: pa.Array) -> tuple:
    """
    Fallback conversion to NumPy when FFI is not available.

    Parameters
    ----------
    *arrays : pa.Array
        Arrays to convert

    Returns
    -------
    tuple[np.ndarray, ...]
        NumPy arrays
    """
    return tuple(arr.to_numpy() for arr in arrays)


def numpy_to_arrow(np_array: np.ndarray) -> pa.Array:
    """
    Convert NumPy array to Arrow with zero-copy when possible.

    Parameters
    ----------
    np_array : np.ndarray
        NumPy array to convert

    Returns
    -------
    pa.Array
        Arrow array (zero-copy when data is contiguous)
    """
    # PyArrow can do zero-copy conversion for contiguous arrays
    return pa.array(np_array, type=pa.float64())


def validate_ffi_available() -> bool:
    """
    Check if Arrow FFI is available.

    Returns
    -------
    bool
        True if FFI is available, False otherwise
    """
    try:
        # Check for PyCapsule Interface
        if hasattr(pa.Array, "__arrow_c_array__"):
            return True

        # Check for legacy C interface
        if hasattr(pa.Array, "_export_to_c"):
            return True

        return False
    except Exception:
        return False


# Export public interface
__all__ = [
    "ArrowCDataInterface",
    "prepare_arrow_arrays",
    "arrays_to_numpy_fallback",
    "numpy_to_arrow",
    "validate_ffi_available",
]

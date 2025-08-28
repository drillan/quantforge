"""Optimized validators using NumPy vectorization for batch operations."""

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from .errors import DimensionError, ValidationError


class VectorizedValidator:
    """Vectorized validation for NumPy arrays with minimal overhead."""

    @staticmethod
    def ensure_array(data: ArrayLike, dtype: DTypeLike = np.float64, name: str = "data") -> NDArray[np.float64]:
        """Convert input to NumPy array with specified dtype.

        This is a zero-copy operation when possible.

        Args:
            data: Input data (scalar, list, or array)
            dtype: Target data type
            name: Parameter name for error messages

        Returns:
            NumPy array with specified dtype

        Raises:
            ValidationError: If conversion fails
        """
        try:
            arr = np.asarray(data, dtype=dtype)
        except (ValueError, TypeError) as e:
            raise ValidationError(name, data, f"cannot convert to {dtype}: {e}") from e

        return arr

    @staticmethod
    def validate_positive_array(data: ArrayLike, name: str = "data", strict: bool = True) -> NDArray[np.float64]:
        """Validate that all array elements are positive.

        Uses vectorized operations for performance.

        Args:
            data: Input array
            name: Parameter name for error messages
            strict: If True, values must be > 0; if False, >= 0

        Returns:
            Validated array as NumPy array

        Raises:
            ValidationError: If any element is non-positive or non-finite
        """
        arr = VectorizedValidator.ensure_array(data, name=name)

        # Vectorized checks
        if strict:
            invalid_mask = arr <= 0
            error_msg = "all elements must be positive"
        else:
            invalid_mask = arr < 0
            error_msg = "all elements must be non-negative"

        if np.any(invalid_mask):
            # Find first invalid index for better error message
            first_bad = np.argmax(invalid_mask)
            raise ValidationError(name, f"element at index {first_bad} = {arr[first_bad]}", error_msg)

        # Check for NaN/Inf
        if not np.all(np.isfinite(arr)):
            first_bad = np.argmax(~np.isfinite(arr))
            raise ValidationError(
                name, f"element at index {first_bad} = {arr[first_bad]}", "all elements must be finite"
            )

        return arr

    @staticmethod
    def validate_shape_compatibility(
        arrays: dict[str, ArrayLike], broadcast: bool = True
    ) -> dict[str, NDArray[np.float64]]:
        """Validate that multiple arrays have compatible shapes.

        Args:
            arrays: Dictionary of name -> array
            broadcast: If True, allow NumPy broadcasting rules

        Returns:
            Dictionary of validated NumPy arrays

        Raises:
            DimensionError: If shapes are incompatible
        """
        result = {}
        shapes = []

        # Convert all to arrays and get shapes
        for name, data in arrays.items():
            arr = VectorizedValidator.ensure_array(data, name=name)
            result[name] = arr
            shapes.append((name, arr.shape))

        if not broadcast:
            # All shapes must be identical
            first_shape = shapes[0][1]
            for name, shape in shapes[1:]:
                if shape != first_shape:
                    raise DimensionError(expected=first_shape, actual=shape, parameter=name)
        else:
            # Check broadcasting compatibility
            try:
                # Attempt to broadcast all arrays together
                np.broadcast_arrays(*result.values())
            except ValueError as e:
                # Find problematic shapes
                _ = ", ".join(f"{name}={shape}" for name, shape in shapes)  # 形状情報（エラーメッセージには使用しない）
                raise DimensionError(expected=(-1,), actual=(-1,), parameter="arrays") from e

        return result

    @staticmethod
    def validate_option_arrays(
        spot: ArrayLike,
        strike: ArrayLike,
        time: ArrayLike,
        rate: ArrayLike,
        sigma: ArrayLike,
        dividend: ArrayLike | None = None,
        broadcast: bool = True,
    ) -> dict[str, NDArray[np.float64]]:
        """Validate and prepare option pricing arrays.

        Combines all validation steps in a single pass for efficiency.

        Args:
            spot: Spot prices
            strike: Strike prices
            time: Times to maturity
            rate: Risk-free rates
            sigma: Volatilities
            dividend: Optional dividend yields
            broadcast: Allow broadcasting

        Returns:
            Dictionary of validated arrays

        Raises:
            ValidationError: If any validation fails
            DimensionError: If shapes are incompatible
        """
        # Build arrays dict
        arrays = {
            "spot": spot,
            "strike": strike,
            "time": time,
            "rate": rate,
            "sigma": sigma,
        }
        if dividend is not None:
            arrays["dividend"] = dividend

        # Validate shapes
        validated = VectorizedValidator.validate_shape_compatibility(arrays, broadcast=broadcast)

        # Validate values (vectorized)
        validated["spot"] = VectorizedValidator.validate_positive_array(validated["spot"], "spot prices")
        validated["strike"] = VectorizedValidator.validate_positive_array(validated["strike"], "strike prices")
        validated["time"] = VectorizedValidator.validate_positive_array(
            validated["time"], "times to maturity", strict=False
        )
        validated["sigma"] = VectorizedValidator.validate_positive_array(validated["sigma"], "volatilities")

        # Rate and dividend can be any finite value
        if not np.all(np.isfinite(validated["rate"])):
            raise ValidationError("rate", "array", "all elements must be finite")

        if "dividend" in validated and not np.all(np.isfinite(validated["dividend"])):
            raise ValidationError("dividend", "array", "all elements must be finite")

        return validated


def validate_batch_inputs(model_type: str, **kwargs: ArrayLike) -> dict[str, NDArray[np.float64]]:
    """Validate inputs for batch processing based on model type.

    This is a convenience function that routes to the appropriate validator.

    Args:
        model_type: One of 'black_scholes', 'black76', 'merton', 'american'
        **kwargs: Model-specific parameters

    Returns:
        Dictionary of validated NumPy arrays

    Raises:
        ValueError: If model_type is unknown
        ValidationError: If validation fails
    """
    if model_type == "black_scholes":
        required = {"spot", "strike", "time", "rate", "sigma"}
        if not required.issubset(kwargs.keys()):
            missing = required - kwargs.keys()
            raise ValueError(f"Missing required parameters: {missing}")

        return VectorizedValidator.validate_option_arrays(
            kwargs["spot"], kwargs["strike"], kwargs["time"], kwargs["rate"], kwargs["sigma"]
        )

    elif model_type == "black76":
        # Black76 uses 'forward' instead of 'spot'
        required = {"forward", "strike", "time", "rate", "sigma"}
        if not required.issubset(kwargs.keys()):
            # Check if 'forwards' (plural) was used instead
            if "forwards" in kwargs and "forward" not in kwargs:
                kwargs["forward"] = kwargs.pop("forwards")
            else:
                missing = required - kwargs.keys()
                raise ValueError(f"Missing required parameters: {missing}")

        # Rename for validation
        return VectorizedValidator.validate_option_arrays(
            kwargs["forward"],  # Use forward as spot
            kwargs["strike"],
            kwargs["time"],
            kwargs["rate"],
            kwargs["sigma"],
        )

    elif model_type in ["merton", "american"]:
        required = {"spot", "strike", "time", "rate", "sigma", "dividend"}
        if not required.issubset(kwargs.keys()):
            # Check for 'dividends' (plural) or 'q' notation
            if "dividends" in kwargs and "dividend" not in kwargs:
                kwargs["dividend"] = kwargs.pop("dividends")
            elif "q" in kwargs and "dividend" not in kwargs:
                kwargs["dividend"] = kwargs.pop("q")
            else:
                missing = required - kwargs.keys()
                raise ValueError(f"Missing required parameters: {missing}")

        return VectorizedValidator.validate_option_arrays(
            kwargs["spot"], kwargs["strike"], kwargs["time"], kwargs["rate"], kwargs["sigma"], kwargs["dividend"]
        )

    else:
        raise ValueError(f"Unknown model type: {model_type}")

# Basic stub file for pyarrow types used in quantforge
from collections.abc import Sequence
from typing import Any

class Array:
    """PyArrow Array type stub"""
    def __init__(self, data: Sequence[Any]) -> None: ...
    def to_numpy(self) -> Any: ...
    def __len__(self) -> int: ...

class DataType:
    """PyArrow DataType stub"""

    pass

class ChunkedArray:
    """PyArrow ChunkedArray stub"""

    pass

def array(data: Sequence[Any]) -> Array: ...

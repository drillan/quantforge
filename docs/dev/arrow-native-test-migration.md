# Arrow Native Test Migration Documentation

## Overview
This document records the learnings and patterns from migrating QuantForge tests to support the new Arrow Native architecture.

## Key Differences

### Before: NumPy-based
- Functions returned `np.ndarray`
- Direct array operations worked
- Tests assumed NumPy arrays

### After: Arrow Native
- Functions return `arro3.core.Array`
- Direct operations on Arrow Scalars fail
- Tests must handle Arrow arrays properly

## Implementation Patterns

### 1. ArrowArrayHelper Class

```python
class ArrowArrayHelper:
    @staticmethod
    def is_arrow(obj: Any) -> bool
        """Check if object is an Arrow array."""
        
    @staticmethod
    def to_list(arr: Any) -> List[float]
        """Convert Arrow or NumPy array to Python list."""
        
    @staticmethod
    def get_value(arr: Any, index: int) -> float
        """Get value at index from Arrow or NumPy array."""
        
    @staticmethod
    def assert_type(result: Any) -> None
        """Assert that result is an Arrow array."""
```

### 2. Parametrized Tests

```python
@pytest.mark.parametrize("array_type", INPUT_ARRAY_TYPES)
def test_batch_processing(self, array_type: str) -> None:
    # Create test arrays with specified type
    spots = create_test_array([100.0, 105.0, 110.0], array_type)
    
    # Call function (always returns Arrow)
    prices = black_scholes.call_price_batch(spots, ...)
    
    # Verify Arrow type and convert for comparisons
    arrow.assert_type(prices)
    prices_list = arrow.to_list(prices)
    assert prices_list[0] < prices_list[1]
```

### 3. Common Conversion Issues

#### Issue: Direct Scalar Comparison
```python
# Fails with Arrow Scalars
assert prices[0] < prices[1]
```

#### Solution: Convert to List First
```python
# Works with Arrow
prices_list = arrow.to_list(prices)
assert prices_list[0] < prices_list[1]
```

#### Issue: NumPy Operations on Arrow Arrays
```python
# Fails
assert np.all(prices >= 0)
```

#### Solution: Convert to NumPy
```python
# Works
prices_np = np.array(arrow.to_list(prices))
assert np.all(prices_np >= 0)
```

## Test Migration Status

### Completed Files
- [x] conftest.py - Added ArrowArrayHelper
- [x] test_black_scholes.py - Parametrized batch tests
- [x] test_black76.py - Parametrized batch tests
- [x] test_merton.py - Parametrized batch tests
- [x] test_integration.py - Arrow conversions
- [x] test_put_options.py - Arrow conversions
- [x] base_testing.py - Updated to_numpy_array
- [x] test_validation.py - Arrow Scalar fixes
- [x] test_full_workflow.py - E2E Arrow support

### Pending Files
- [ ] Remaining test files need Arrow migration
- [ ] Performance test threshold adjustments
- [ ] American Options implementation

## Success Rate Progress
- Initial: 48.5% (241/497 tests)
- After Phase 1: 51.8% (258/498 tests)
- Target: 85% or higher

## Lessons Learned

1. **Always convert Arrow Scalars before comparison**
   - Arrow Scalars cannot be directly compared with Python floats
   - Use `arrow.to_list()` for safe conversion

2. **Test both input types**
   - Support both NumPy and PyArrow inputs
   - Output is always Arrow Native

3. **Use helper functions consistently**
   - Reduces code duplication
   - Makes tests more maintainable

4. **Check for Arrow type first**
   - Use `arrow.assert_type()` to verify Arrow arrays
   - Helps catch type mismatches early
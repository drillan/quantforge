# Contribution Guide

We welcome contributions to QuantForge! This guide explains how to contribute to the project.

## Code of Conduct

- Constructive and respectful communication
- Respect for Diversity and Inclusion
- Professional Behavior

## Type of Contribution

### 🐛 Bug Report

Information to include when creating an issue:

```markdown
## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.12.1]
- QuantForge: [e.g., 0.1.0]
- CPU: [e.g., Intel i9-12900K]

## Reproduction Steps
1. ...
2. ...

## Expected Behavior
...

## Actual Behavior
...

## Error Message
```

### ✨ Feature Proposal

```markdown
## Proposal
...

## Motivation
Why this feature is needed

## Proposed API
```python
# Examples
```

## Expected Implementation
...
```

### 📝 Document Improvement

- Correcting typos and omissions
- Improve Description
- Add New Examples
- translation

## Development Flow

### 1. Environment Setup

```bash
# Fork repository
git clone https://github.com/yourusername/quantforge.git
cd quantforge

# Create development branch
git checkout -b feature/your-feature

# Set up development environment
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Rust environment
rustup update
cargo build
```

### 2. Coding Standards

#### Rust

```rust
// ✅ Good
pub fn calculate_price(
    spot: f64,
    strike: f64,
    rate: f64,
    vol: f64,
    time: f64,
) -> Result<f64> {
    validate_inputs(spot, strike, rate, vol, time)?;
    // ...
}

// ❌ Bad
pub fn calc(s: f64, k: f64, r: f64, v: f64, t: f64) -> f64 {
    // ...
}
```

#### Python

```python
# ✅ Good
def calculate_implied_volatility(
    price: float,
    spot: float,
    strike: float,
    rate: float,
    time: float,
    option_type: str = "call",
) -> float:
    """
    Calculate implied volatility using Newton-Raphson method.
    
    Args:
        price: Market price of the option
        spot: Current spot price
        strike: Strike price
        rate: Risk-free rate
        time: Time to maturity in years
        option_type: "call" or "put"
    
    Returns:
        Implied volatility
    
    Raises:
        ConvergenceError: If calculation doesn't converge
    """
    # Implementation
```

### 3. Create Test

#### Rust Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    
    #[test]
    fn test_black_scholes_call() {
        let price = black_scholes_call(100.0, 100.0, 0.05, 0.2, 1.0);
        assert_relative_eq!(price, 10.4506, epsilon = 1e-4);
    }
    
    #[test]
    #[should_panic(expected = "Invalid spot price")]
    fn test_negative_spot() {
        black_scholes_call(-100.0, 100.0, 0.05, 0.2, 1.0);
    }
}
```

#### Python Testing

```python
import pytest
import numpy as np
from quantforge.models import black_scholes

def test_black_scholes_call():
    """Test Black-Scholes call option pricing."""
    price = black_scholes.call_price(100, 100, 1.0, 0.05, 0.2)
    assert abs(price - 10.4506) < 1e-4

def test_batch_processing():
    """Test batch processing with NumPy arrays."""
    spots = np.array([95, 100, 105])
    prices = black_scholes.call_price_batch(spots, 100, 1.0, 0.05, 0.2)
    assert len(prices) == 3
    assert all(p > 0 for p in prices)

@pytest.mark.parametrize("spot,strike,time,expected", [
    (110, 100, 1.0, True),   # ITM
    (100, 100, 1.0, False),  # ATM
    (90, 100, 1.0, False),   # OTM
])
def test_moneyness(spot, strike, time, expected):
    """Test in-the-money detection via price comparison."""
    price = black_scholes.call_price(spot, strike, time, 0.05, 0.2)
    # ITM calls have intrinsic value > 0
    intrinsic = max(spot - strike, 0)
    assert (intrinsic > 0) == expected
```

### 4. Documentation

```python
def new_feature(param1: float, param2: str) -> dict:
    """
    Brief description of the feature.
    
    Longer description explaining the purpose
    and behavior of the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Dictionary containing:
            - key1: Description
            - key2: Description
    
    Raises:
        ValueError: When param1 is negative
        TypeError: When param2 is not a string
    
    Examples:
        >>> result = new_feature(10.0, "test")
        >>> print(result['key1'])
        10.0
    
    Note:
        This feature requires Python 3.12+
    
    See Also:
        related_function: For similar functionality
    """
    pass
```

### 5. Commit

```bash
# Check changes
git status
git diff

# Run tests
cargo test
pytest

# Format
cargo fmt
black .
isort .

# Lint
cargo clippy
ruff check .

# Commit
git add -A
git commit -m "feat: Add new pricing model

- Implement Heston model
- Add tests and documentation
- Update Python bindings

Closes #123"
```

#### Commit Message Conventions

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Format
- `refactor`: Refactoring
- `test`: Add test
- `chore`: Build tool-related

### 6. Pull Request

```markdown
## Summary
This PR...

## Changes
- [ ] Implement feature A
- [ ] Add tests
- [ ] Update documentation

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Performance tests conducted

## Review Points
- Implementation approach in file X
- Performance impact

## Screenshots (if applicable)
...

## Related Issues
Closes #123
```

## Review Process

### as a reviewer

- Constructive Feedback
- Specific Improvement Proposals
- Point out the positive aspects

```markdown
# Good feedback example
This implementation is efficient! For further improvement,
using precomputation here could speed it up by about 20%:

```rust
let sqrt_time = time.sqrt();  // Precomputation
```

# Bad feedback example
This code is slow.
```

### as author

- Thank you for your feedback.
- Ask questions if unclear
- Add explanations as needed

## Release Process

1. Version Update
2. Update CHANGELOG
3. Create Tags
4. Create GitHub Release
5. PyPI Release

## Support

### If You Have Questions

- [GitHub Discussions](https://github.com/yourusername/quantforge/discussions)
- [Discord](https://discord.gg/quantforge)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/quantforge)

### Acknowledgments to Contributors

Thank you to all our contributors! The list of contributors can be found [here](https://github.com/yourusername/quantforge/graphs/contributors).

## License

Contributions will be released under the same MIT license as the project.

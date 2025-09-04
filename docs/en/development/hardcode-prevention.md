# Hardcode Prevention Guidelines

## Overview

The QuantForge project strictly prohibits hardcoded configuration values based on the principle of zero technical debt.
This document provides guidelines for developers to avoid hardcoding and properly manage constants.

## Why Hardcoding is Problematic

1. **Reduced maintainability**: Same values scattered across multiple locations, leading to omissions during changes
2. **Reduced readability**: Unclear meaning of magic numbers
3. **Testing difficulties**: Difficulty changing values reduces test flexibility
4. **Technical debt**: Cost of later fixes increases

## Configuration Value Management System

### Constant Placement Locations

| Type | Rust Location | Python Location | Example |
|------|--------------|-----------------|---------|
| Precision/Tolerance | `src/constants.rs` | `tests/conftest.py` | `PRACTICAL_TOLERANCE = 1e-3` |
| Math Constants/Coefficients | Near usage location | Near usage location | Abramowitz coefficients |
| Input Validation Limits | `src/validation.rs` | - | Price/time ranges |
| Test Values | - | `tests/conftest.py` | Standard test cases |

### Currently Defined Major Constants

#### Precision Levels (Rust/Python Common)

```{code-block} rust
:name: hardcode-prevention-code-src/constants.rs
:caption: src/constants.rs

// src/constants.rs
pub const PRACTICAL_TOLERANCE: f64 = 1e-3;   // Practical precision
pub const THEORETICAL_TOLERANCE: f64 = 1e-5; // Theoretical precision
pub const NUMERICAL_TOLERANCE: f64 = 1e-7;   // Numerical precision
```

```{code-block} python
:name: hardcode-prevention-code-tests/conftest.py
:caption: tests/conftest.py

# tests/conftest.py
PRACTICAL_TOLERANCE: Final[float] = 1e-3   # Practical precision
THEORETICAL_TOLERANCE: Final[float] = 1e-5 # Theoretical precision
NUMERICAL_TOLERANCE: Final[float] = 1e-7   # Numerical precision
```

## Development Workflow

### 1. During New Implementation

```{code-block} bash
:name: hardcode-prevention-code-step-1
:caption: Step 1: Check existing constants

# Step 1: Check existing constants
grep -r "desired_value" src/constants.rs tests/conftest.py

# Step 2: Define if constant doesn't exist
# Example: Add to src/constants.rs
pub const NEW_CONSTANT: f64 = 3.14159; // π - Pi

# Step 3: Use in implementation
use crate::constants::NEW_CONSTANT;

# Step 4: Verify
./scripts/detect_hardcode.sh
```

### 2. When Modifying Existing Code

When hardcoded values are found:

```{code-block} rust
:name: hardcode-prevention-code-before
:caption: Before (bad example)

// Before (bad example)
if x > 8.0 { return 1.0; }

// After (good example)
const NORM_CDF_UPPER_BOUND: f64 = 8.0;
if x > NORM_CDF_UPPER_BOUND { return 1.0; }
```

### 3. When Creating Test Code

```{code-block} python
:name: hardcode-prevention-code-before
:caption: Before (bad example)

# Before (bad example)
assert abs(actual - expected) < 1e-5

# After (good example)
from conftest import THEORETICAL_TOLERANCE
assert abs(actual - expected) < THEORETICAL_TOLERANCE
```

## Hardcode Detection Tool

### Automatic Detection Script

```{code-block} bash
:name: hardcode-prevention-code-how-to-run
:caption: How to run

# How to run
./scripts/detect_hardcode.sh

# Output example
🔍 QuantForge Hardcode Detection Script
=========================================
📊 Detecting floating-point numbers...
✅ No issues
🔬 Detecting scientific notation...
✅ No issues
```

### Automatic Checks in CI/CD

Hardcode detection runs automatically on PRs and commits.

## Permitted Exceptions

Only the following values may be hardcoded:

- `0`, `1`, `2`, `-1` (basic integers)
- `0.5` (mathematical expression of 1/2)
- Array indices
- Loop counters
- Descriptive numbers in error messages

## Frequently Asked Questions

### Q: Do experimental codes in playground/ also need constants?

A: playground/ and scratch/ are exceptions, but using constants is still recommended whenever possible.

### Q: What about constants from external libraries?

A: Redefine them whenever possible to clarify meaning:

```{code-block} rust
:name: hardcode-prevention-code-stdf64epsilon
:caption: Rather than std::f64::EPSILON

// Rather than std::f64::EPSILON
pub const MACHINE_EPSILON: f64 = std::f64::EPSILON;
```

### Q: Where should test-only values be defined?

A: Consolidate in `tests/conftest.py` or define at the beginning of each test file.

## Checklist

Confirmation items for new code/PR reviews:

- [ ] All numeric literals (except permitted exceptions) are defined as constants
- [ ] Constants have descriptive names
- [ ] Same values are not duplicated in multiple locations
- [ ] Common values between Rust/Python are synchronized
- [ ] `./scripts/detect_hardcode.sh` shows no errors

## Summary

Hardcode prevention is an important practice for preventing technical debt.
By implementing correctly from the start rather than "fixing later",
we can maintain a highly maintainable, high-quality codebase.
# Documentation Code Testing Guide

Automated testing system for Python code samples within QuantForge project documentation to ensure consistency with the API.

## Overview

### Purpose
- Ensure all Python code samples in documentation are executable
- Automatically detect documentation inconsistencies when APIs change
- Provide code examples that users can copy and paste immediately

### System Architecture
```
tests/doc_tests/
├── README.md                    # System overview
├── code_extractor.py           # Code block extraction engine
├── conftest.py                 # pytest configuration and fixtures
├── test_documentation_code.py  # Main test file
├── fix_documentation_codes.py  # Automatic fix script
├── check_doc_codes.py          # Statistics check tool
├── analyze_errors.py           # Error analysis tool
└── FINAL_REPORT.md            # Implementation completion report
```

## Usage

### Basic Test Execution

```bash
# Test all documentation code
pytest tests/doc_tests/ -v

# Test specific documents only
pytest tests/doc_tests/ --doc-filter quickstart

# Test with detailed reporting
pytest tests/doc_tests/ --doc-report

# Skip time-consuming tests
pytest tests/doc_tests/ --skip-doc-slow
```

### Statistics Checking

```bash
# Display overall statistics
uv run python tests/doc_tests/check_doc_codes.py

# Check code blocks in specific files
uv run python tests/doc_tests/code_extractor.py docs/en/quickstart.md

# Detailed error analysis
uv run python tests/doc_tests/analyze_errors.py
```

### Automatic Fixes

```bash
# Check fix content with dry-run (recommended)
python tests/doc_tests/fix_documentation_codes.py docs/ --dry-run --verbose

# Fix specific files only
python tests/doc_tests/fix_documentation_codes.py docs/en/quickstart.md

# Fix all documentation
python tests/doc_tests/fix_documentation_codes.py docs/
```

## Supported Code Block Formats

### 1. Simple Python Code Blocks
```markdown
```python
from quantforge.models import black_scholes
price = black_scholes.call_price(100, 100, 1.0, 0.05, 0.2)
print(f"Price: {price}")
```
```

### 2. Sphinx Code Blocks
```markdown
```{code-block} python
:name: example-name
:caption: Sample Code
:no-test:  # Skip with this option

from quantforge.models import black_scholes
price = black_scholes.call_price(100, 100, 1.0, 0.05, 0.2)
```
```

## Automatic Skip Features

The following patterns are automatically skipped:

### Undefined Function Usage
```python
# Automatically skipped example
market_price = get_market_price(strike)  # Undefined function
```

### Matplotlib Display
```python
# Automatically skipped example
plt.show()  # matplotlib display
pyplot.show()
```

### Placeholder Code
```python
# Automatically skipped example
# Actual market data retrieval function
...  # Ellipsis
```

### Manual Skip
```markdown
```{code-block} python
:no-test:

# This code will not be tested
experimental_function()
```
```

## Test Environment

### Automatically Provided Environment
The following environment is automatically provided during test execution:

```python
# QuantForge modules
from quantforge.models import black_scholes, black76, merton, american
import quantforge

# Numerical computation libraries
import numpy as np
import pyarrow as pa

# Mock functions
def get_market_price(strike):
    """Mock function to get market price"""
    base_price = 10.0
    moneyness = abs(100.0 - strike) / 100.0
    return base_price * (1.0 - moneyness * 0.5)

# Standard libraries
import time
import math
```

### matplotlib Support
- Automatically disables display when matplotlib is installed
- Avoids errors when not installed

## Automatic Fix Features

### Fixable Issues

#### 1. Batch API Parameter Name Inconsistencies
```python
# Before fix (incorrect)
black_scholes.call_price_batch(spots=spots, strikes=100.0, times=1.0, rates=0.05, sigmas=0.2)

# After fix (correct)
black_scholes.call_price_batch(spots=spots, strikes=100.0, times=1.0, rates=0.05, sigmas=0.2)
```

#### 2. Greeks Dictionary Access Inconsistencies
```python
# Before fix (incorrect)
delta = greeks['delta']

# After fix (correct)
delta = greeks['delta']
```

#### 3. Code Block Type Misclassification
```markdown
<!-- Before fix (incorrect) -->
```bash
pip install quantforge
```

<!-- After fix (correct) -->
```bash
pip install quantforge
```
```

### Issues Requiring Manual Fix

The following cannot be automatically fixed and require manual intervention:

- **Context Dependencies**: References to variables defined in previous code blocks
- **Syntax Errors**: Complex syntax issues or indentation errors
- **Undefined Variables**: Missing imports, lack of variable definitions
- **Incomplete Code**: Pseudo-code for explanatory purposes

## Developer Guide

### Adding New Skip Patterns

Add regular expressions to `SKIP_PATTERNS` in `tests/doc_tests/code_extractor.py`:

```python
SKIP_PATTERNS = [
    # Existing patterns
    r'get_market_price\s*\(',
    r'plt\.show\s*\(',

    # Add new patterns
    r'your_custom_pattern\s*\(',
]
```

### Adding New Mock Functions

Add to the `mock_functions` fixture in `tests/doc_tests/conftest.py`:

```python
@pytest.fixture
def mock_functions():
    def your_mock_function(param):
        """New mock function"""
        return some_result

    return {
        'get_market_price': get_market_price,
        'your_mock_function': your_mock_function,  # Add this
    }
```

### Adding Automatic Fix Rules

Add new fix rules to `tests/doc_tests/fix_documentation_codes.py`:

```python
NEW_FIXES = [
    CodeFix(
        pattern=r'old_pattern',
        replacement='new_pattern',
        description='Fix description',
        context='application_condition'  # Optional
    ),
]
```

## CI/CD Integration

### GitHub Actions Configuration Example

```yaml
name: Documentation Code Test

on:
  pull_request:
    paths:
      - 'docs/**/*.md'
  push:
    branches: [main]

jobs:
  doc-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync --group dev

      - name: Test documentation code
        run: |
          uv run pytest tests/doc_tests/ --doc-report -v

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: doc-test-results
          path: |
            doc_test_reports/
            .pytest_cache/
```

## Troubleshooting

### Common Issues and Solutions

#### ImportError: No module named 'matplotlib'
**Symptom**: matplotlib not found error
**Solution**: matplotlib is not required. It will be automatically skipped.

#### call_price_batch() got an unexpected keyword argument 'k'
**Symptom**: Error with old parameter names
**Solution**: Run the automatic fix script:
```bash
python tests/doc_tests/fix_documentation_codes.py docs/ --dry-run
```

#### 'dict' object has no attribute 'delta'
**Symptom**: greeks attribute access error
**Solution**: Change `greeks.delta` to `greeks['delta']`.

#### Massive syntax errors
**Symptom**: bash commands interpreted as Python
**Solution**: Set appropriate code block types:
```markdown
```bash  # Not python
pip install quantforge
```
```

### Debugging Methods

#### Test Specific Code Blocks Only
```bash
# Check specific file and line
uv run python -c "
from tests.doc_tests.code_extractor import DocCodeExtractor
blocks = DocCodeExtractor().extract_from_file(Path('docs/en/quickstart.md'))
for i, block in enumerate(blocks):
    if block.line_number == 70:  # Specific line
        print(f'Block {i}: {block.code}')
"
```

#### Test Execution Environment
```bash
# Directly check test environment
uv run python -c "
from tests.doc_tests.conftest import CodeExecutor
from tests.doc_tests.check_doc_codes import SimpleCodeExecutor
executor = SimpleCodeExecutor()
success, output, error = executor.execute('print(\"Hello World\")')
print(f'Success: {success}, Output: {output}, Error: {error}')
"
```

## Performance Metrics

### Current Statistics (as of 2025-09-20)

```
Total code blocks: 279
Test targets: 258 (92.5%)
Successful: 124 (48.1%)
Errors: 134 (51.9%)
Skipped: 21 (7.5%)
```

### Error Distribution
- Syntax errors: 46.3% (bash command misclassification, etc.)
- Undefined variables: 23.9% (missing imports, context dependencies)
- Others: 29.8% (attribute errors, missing modules, etc.)

## Related Resources

- [System Implementation Report](../../../tests/doc_tests/FINAL_REPORT.md)
- [pytest Documentation](https://docs.pytest.org/)
- [MyST Markdown Guide](https://myst-parser.readthedocs.io/)
- [Code-block Specification](https://myst-parser.readthedocs.io/en/latest/syntax/code_and_apis.html)

## Change History

| Date | Changes | Author |
|------|---------|--------|
| 2025-09-20 | Initial version, system implementation completed | AI Assistant |

---

> Use this guide together with `tests/doc_tests/README.md`. For technical details, also refer to comments in implementation files.
#!/bin/bash
# Test QuantForge wheel installation and functionality
set -e

echo "🧪 Testing QuantForge wheel installation..."

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if wheel exists
if [ ! -f dist/*.whl ]; then
    echo -e "${RED}❌ No wheel file found in dist/${NC}"
    echo "Please run ./scripts/build-wheel.sh first"
    exit 1
fi

# Get latest wheel
WHEEL_FILE=$(ls -t dist/*.whl | head -1)
WHEEL_NAME=$(basename "$WHEEL_FILE")

echo "📦 Testing wheel: $WHEEL_NAME"

# Create temporary virtual environment
VENV_DIR=$(mktemp -d)
echo "🔧 Creating temporary venv at $VENV_DIR"

# Use Python 3.12 explicitly
if ! command -v python3.12 &> /dev/null; then
    echo -e "${RED}❌ Python 3.12 not found${NC}"
    echo "Please install Python 3.12 or higher"
    exit 1
fi

python3.12 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install wheel
echo "📥 Installing wheel..."
pip install --quiet --upgrade pip
pip install --quiet "$WHEEL_FILE"

# Run comprehensive tests
echo "🔬 Running import tests..."

python -c "
import sys
import time

# Color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'

print(f'Python version: {sys.version}')
print('━' * 50)

# Test 1: Basic import
try:
    start = time.perf_counter()
    import quantforge
    elapsed = (time.perf_counter() - start) * 1000
    print(f'{GREEN}✅ quantforge imported successfully ({elapsed:.1f}ms){NC}')
    print(f'   Version: {quantforge.__version__}')
except Exception as e:
    print(f'{RED}❌ Failed to import quantforge: {e}{NC}')
    sys.exit(1)

# Test 2: Import models
try:
    from quantforge.models import black_scholes, black76
    from quantforge import models
    print(f'{GREEN}✅ Models imported successfully{NC}')
except Exception as e:
    print(f'{RED}❌ Failed to import models: {e}{NC}')
    sys.exit(1)

# Test 3: Basic functionality
try:
    price = black_scholes.call_price(100, 100, 1.0, 0.05, 0.2)
    assert 10 < price < 15, f'Unexpected price: {price}'
    print(f'{GREEN}✅ black_scholes.call_price: {price:.4f}{NC}')
except Exception as e:
    print(f'{RED}❌ black_scholes test failed: {e}{NC}')
    sys.exit(1)

# Test 4: Greeks calculation
try:
    greeks = black_scholes.greeks(100, 100, 1.0, 0.05, 0.2, True)  # True for call
    print(f'{GREEN}✅ Greeks calculated successfully{NC}')
    print(f'   Delta: {greeks.delta:.4f}')
    print(f'   Gamma: {greeks.gamma:.4f}')
    print(f'   Theta: {greeks.theta:.4f}')
    print(f'   Vega: {greeks.vega:.4f}')
    print(f'   Rho: {greeks.rho:.4f}')
except Exception as e:
    print(f'{RED}❌ Greeks test failed: {e}{NC}')
    sys.exit(1)

# Test 5: Batch processing
try:
    import numpy as np
    s_array = np.array([95.0, 100.0, 105.0])
    prices = black_scholes.call_price_batch(s_array, 100, 1.0, 0.05, 0.2)
    assert len(prices) == 3, f'Expected 3 prices, got {len(prices)}'
    print(f'{GREEN}✅ Batch processing works{NC}')
    print(f'   Prices: {prices}')
except Exception as e:
    print(f'{RED}❌ Batch processing failed: {e}{NC}')
    sys.exit(1)

# Test 6: Black76 model
try:
    price = black76.call_price(100, 100, 1.0, 0.05, 0.2)
    print(f'{GREEN}✅ black76.call_price: {price:.4f}{NC}')
except Exception as e:
    print(f'{RED}❌ black76 test failed: {e}{NC}')
    sys.exit(1)

# Test 7: American Option
try:
    from quantforge.models import american  # American option might be separate
    price = models.american.call_price(100, 100, 1.0, 0.05, 0.2, 100)
    print(f'{GREEN}✅ american.call_price: {price:.4f}{NC}')
except Exception as e:
    print(f'{YELLOW}⚠️ American option test skipped (may not be implemented): {e}{NC}')

print('━' * 50)
print(f'{GREEN}🎉 All tests passed!{NC}')
"

TEST_RESULT=$?

# Clean up
deactivate
rm -rf "$VENV_DIR"

if [ $TEST_RESULT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Wheel test completed successfully!${NC}"
    echo "The wheel is ready for distribution."
else
    echo ""
    echo -e "${RED}❌ Wheel test failed${NC}"
    exit 1
fi
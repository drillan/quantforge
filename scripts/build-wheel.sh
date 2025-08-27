#!/bin/bash
# Build QuantForge wheel for local development
set -e

echo "🔨 Building QuantForge wheel for local development..."
echo "Target: Python 3.12+ with abi3-py312"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Profile selection
PROFILE=${1:-dev}

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/*.whl 2>/dev/null || true
mkdir -p dist

if [ "$PROFILE" = "dev" ]; then
    echo -e "${GREEN}📦 Development build (fast, unoptimized)${NC}"
    maturin build --release -o dist
elif [ "$PROFILE" = "release" ]; then
    echo -e "${GREEN}📦 Release build (optimized, stripped)${NC}"
    # Add release-specific optimizations
    RUSTFLAGS="-C target-cpu=native" maturin build \
        --release \
        --strip \
        -o dist
elif [ "$PROFILE" = "manylinux" ]; then
    echo -e "${GREEN}📦 manylinux2014 build (Docker required)${NC}"
    echo -e "${YELLOW}Note: manylinux wheels are automatically built by GitHub Actions for releases.${NC}"
    echo -e "${YELLOW}      Local manylinux builds are only needed for testing compatibility.${NC}"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed or not running${NC}"
        echo "Docker is optional for local development since:"
        echo "  • GitHub Actions automatically builds manylinux wheels"
        echo "  • Local 'dev' or 'release' builds work fine for development"
        echo ""
        echo "To proceed without Docker, use: $0 dev"
        exit 1
    fi
    
    docker run --rm -v $(pwd):/io \
        ghcr.io/pyo3/maturin build \
        --release \
        --strip \
        --compatibility manylinux2014 \
        -o /io/dist
else
    echo -e "${RED}❌ Unknown profile: $PROFILE${NC}"
    echo "Usage: $0 [dev|release|manylinux]"
    echo "  dev       - Fast development build (recommended for local development)"
    echo "  release   - Optimized release build"
    echo "  manylinux - manylinux2014 compatible build (optional, requires Docker)"
    echo ""
    echo "Note: manylinux wheels are automatically built by GitHub Actions."
    echo "      Docker is NOT required for normal development."
    exit 1
fi

# Check build result
if [ ! -f dist/*.whl ]; then
    echo -e "${RED}❌ Build failed: No wheel file generated${NC}"
    exit 1
fi

# Get wheel file info
WHEEL_FILE=$(ls -t dist/*.whl | head -1)
WHEEL_NAME=$(basename "$WHEEL_FILE")
WHEEL_SIZE=$(du -h "$WHEEL_FILE" | cut -f1)
SIZE_KB=$(du -k "$WHEEL_FILE" | cut -f1)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Build successful!${NC}"
echo "📦 Wheel: $WHEEL_NAME"
echo "📏 Size: $WHEEL_SIZE"

# Size warnings
if [ "$SIZE_KB" -gt 500 ]; then
    echo -e "${RED}⚠️  Warning: Wheel size exceeds 500KB target${NC}"
elif [ "$SIZE_KB" -gt 400 ]; then
    echo -e "${YELLOW}⚠️  Warning: Wheel size approaching 500KB limit${NC}"
else
    echo -e "${GREEN}✨ Wheel size is optimal (<400KB)${NC}"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To install and test:"
echo "  pip install --force-reinstall $WHEEL_FILE"
echo "Or use:"
echo "  ./scripts/test-wheel.sh"
#!/bin/bash
# build_all.sh - Complete build script for Lite3 API and Python bindings

set -e  # Exit on error

echo "========================================="
echo "Lite3 API Build Script"
echo "========================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on Windows (Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo -e "${RED}Error: This script must be run on Linux${NC}"
    echo "For Windows, use WSL or build manually with CMake"
    exit 1
fi

# Detect platform
if [ "$(uname -m)" = "aarch64" ]; then
    PLATFORM="arm"
    echo -e "${GREEN}Detected ARM platform${NC}"
else
    PLATFORM="x86"
    echo -e "${GREEN}Detected x86 platform${NC}"
fi

# Check if we should build for simulation
if [ "$PLATFORM" = "x86" ]; then
    BUILD_SIM="ON"
    echo -e "${GREEN}Building with simulation support${NC}"
else
    BUILD_SIM="OFF"
    echo -e "${YELLOW}Building for hardware (no simulation)${NC}"
fi

# Check dependencies
echo
echo "Checking dependencies..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 not found${NC}"
        echo "Please install $1 and try again"
        exit 1
    else
        echo -e "${GREEN}✓ $1 found${NC}"
    fi
}

check_command cmake
check_command make
check_command python3
check_command g++

# Check Python packages
echo
echo "Checking Python packages..."
python3 -c "import pybind11" 2>/dev/null && echo -e "${GREEN}✓ pybind11 found${NC}" || \
    (echo -e "${YELLOW}! pybind11 not found. Installing...${NC}" && pip3 install pybind11)

python3 -c "import numpy" 2>/dev/null && echo -e "${GREEN}✓ numpy found${NC}" || \
    (echo -e "${YELLOW}! numpy not found. Installing...${NC}" && pip3 install "numpy<2.0")

if [ "$BUILD_SIM" = "ON" ]; then
    python3 -c "import pybullet" 2>/dev/null && echo -e "${GREEN}✓ pybullet found${NC}" || \
        (echo -e "${YELLOW}! pybullet not found. Installing...${NC}" && pip3 install pybullet)
fi

# Create build directory
echo
echo "Creating build directory..."
mkdir -p build
cd build

# Configure with CMake
echo
echo "Configuring with CMake..."
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_PLATFORM=$PLATFORM \
    -DBUILD_SIM=$BUILD_SIM \
    -DSEND_REMOTE=OFF \
    -DBUILD_LITE3_API=ON \
    -DBUILD_PYTHON_BINDINGS=ON

# Build
echo
echo "Building (this may take a few minutes)..."
make -j$(nproc)

# Check build results
echo
echo "Checking build results..."

if [ -f "liblite3_api.so" ]; then
    echo -e "${GREEN}✓ liblite3_api.so built successfully${NC}"
else
    echo -e "${RED}✗ liblite3_api.so not found${NC}"
    exit 1
fi

if [ -f "test_lite3_controller" ]; then
    echo -e "${GREEN}✓ test_lite3_controller built successfully${NC}"
else
    echo -e "${YELLOW}! test_lite3_controller not found${NC}"
fi

# Check for Python module
PYTHON_MODULE=$(find ../python_package/pylite3 -name "pylite3*.so" 2>/dev/null | head -n 1)
if [ -n "$PYTHON_MODULE" ]; then
    echo -e "${GREEN}✓ Python module built: $(basename $PYTHON_MODULE)${NC}"
else
    echo -e "${RED}✗ Python module not found${NC}"
    exit 1
fi

# Run C++ tests
echo
echo "Running C++ tests..."
if [ -f "test_lite3_controller" ]; then
    ./test_lite3_controller
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ C++ tests passed${NC}"
    else
        echo -e "${RED}✗ C++ tests failed${NC}"
        exit 1
    fi
fi

# Install Python package
echo
echo "Installing Python package..."
cd ../python_package
pip3 install -e .

# Test Python import
echo
echo "Testing Python import..."
python3 -c "import pylite3; print('PyLite3 version:', pylite3.version())"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python package installed successfully${NC}"
else
    echo -e "${RED}✗ Python package import failed${NC}"
    exit 1
fi

echo
echo "========================================="
echo -e "${GREEN}Build completed successfully!${NC}"
echo "========================================="
echo
echo "Next steps:"
echo "1. Start simulator (if using simulation):"
echo "   cd interface/robot/simulation"
echo "   python3 pybullet_simulation.py"
echo
echo "2. Try Python examples:"
echo "   cd python_package/examples"
echo "   python3 01_basic_control.py"
echo
echo "3. Or run C++ example:"
echo "   cd build"
echo "   ./simple_example"

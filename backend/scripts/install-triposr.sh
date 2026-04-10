#!/bin/bash
# TripoSR Installation Script (User Directory Version)
# Installs TripoSR for self-hosted 3D model generation
# Requires: Python 3.8+, Git, NVIDIA GPU with 8GB+ VRAM (recommended)

set -e

echo "============================================"
echo "TripoSR Installation Script"
echo "============================================"
echo ""

# Configuration - Install in user directory to avoid sudo
INSTALL_DIR="${TRIPOR_INSTALL_DIR:-$HOME/triposr}"
PYTHON_CMD="${PYTHON_CMD:-python3}"
VENV_PYTHON="${PWD}/venv/bin/python"

# Check Python installation
echo "Checking Python installation..."
if ! command -v $VENV_PYTHON &> /dev/null; then
    echo "Error: Virtualenv Python not found at $VENV_PYTHON"
    exit 1
fi

PYTHON_VERSION=$($VENV_PYTHON --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Check disk space
echo "Checking disk space..."
AVAILABLE_SPACE=$(df -h "$HOME" 2>/dev/null | tail -1 | awk '{print $4}' || echo "Unknown")
echo "Available space: $AVAILABLE_SPACE"
echo ""

# Clone TripoSR repository
echo "Cloning TripoSR repository to $INSTALL_DIR..."
if [ -d "$INSTALL_DIR" ]; then
    echo "Directory $INSTALL_DIR already exists."
    echo "Using existing installation, updating..."
    cd "$INSTALL_DIR"
    git pull || true
else
    git clone https://github.com/VAST-AI-Research/TripoSR.git "$INSTALL_DIR"
    echo "Repository cloned successfully"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
cd "$INSTALL_DIR"

# Check for NVIDIA GPU
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || true
    echo ""
    echo "Installing with CUDA support..."
    $VENV_PYTHON -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
else
    echo "No NVIDIA GPU detected. Installing CPU version (slower)..."
    $VENV_PYTHON -m pip install torch torchvision
fi

# Install TripoSR requirements
echo "Installing TripoSR requirements..."
$VENV_PYTHON -m pip install -r requirements.txt

# Verify installation
echo ""
echo "Verifying installation..."
$VENV_PYTHON infer.py --help || echo "Note: infer.py help not available yet"

# Set environment variable in .env file
ENV_FILE="${PWD}/.env"
echo ""
echo "Updating .env file..."
if [ -f "$ENV_FILE" ]; then
    # Remove existing TRIPOR_PATH if present
    grep -v "^TRIPOR_PATH=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
    mv "$ENV_FILE.tmp" "$ENV_FILE"
    echo "TRIPOR_PATH=$INSTALL_DIR" >> "$ENV_FILE"
    echo "Added TRIPOR_PATH=$INSTALL_DIR to .env"
else
    echo "TRIPOR_PATH=$INSTALL_DIR" > "$ENV_FILE"
    echo "Created .env with TRIPOR_PATH=$INSTALL_DIR"
fi

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "TripoSR installed at: $INSTALL_DIR"
echo ""
echo "To generate 3D models:"
echo "  $VENV_PYTHON $INSTALL_DIR/infer.py --input image.jpg --output model.glb"
echo ""
echo "Note: First run will download model weights (~2GB)"
echo "GPU: ~30 seconds per model | CPU: ~5-10 minutes per model"
echo ""

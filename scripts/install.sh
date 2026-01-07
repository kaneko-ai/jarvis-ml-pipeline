#!/bin/bash
# JARVIS Research OS - One-liner Installation Script
# Usage: curl -sSL https://raw.githubusercontent.com/kaneko-ai/jarvis-ml-pipeline/main/scripts/install.sh | bash

set -e

echo "🚀 Installing JARVIS Research OS..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED_VERSION="3.10"

if [[ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]]; then
    echo "❌ Error: Python 3.10+ is required (found: $PYTHON_VERSION)"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Install method selection
if command -v uv &> /dev/null; then
    echo "📦 Installing with uv..."
    uv pip install jarvis-research-os
elif command -v pip &> /dev/null; then
    echo "📦 Installing with pip..."
    pip install jarvis-research-os
else
    echo "❌ Error: Neither uv nor pip found"
    exit 1
fi

# Verify installation
if command -v jarvis &> /dev/null; then
    echo ""
    echo "✅ JARVIS Research OS installed successfully!"
    echo ""
    echo "Quick start:"
    echo "  jarvis --help              # Show help"
    echo "  jarvis run --goal 'test'   # Run a task"
    echo "  jarvis screen --help       # Active learning screening"
    echo ""
else
    echo "⚠️ Warning: 'jarvis' command not found in PATH"
    echo "Try: python -m jarvis_cli --help"
fi

# Optional: Install extras
read -p "Install optional dependencies (PDF, LLM, embeddings)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 Installing optional dependencies..."
    pip install "jarvis-research-os[all]"
    echo "✅ Optional dependencies installed"
fi

echo ""
echo "🎉 Installation complete!"
echo "Documentation: https://github.com/kaneko-ai/jarvis-ml-pipeline"

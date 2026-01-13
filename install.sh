#!/bin/bash
# Quick installation script

set -e

echo "=================================="
echo "CDKG RAG System - Installation"
echo "=================================="
echo

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo
echo "Creating virtual environment..."
python3 -m venv venv

# Activate and install
echo
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "=================================="
echo "✅ Installation complete!"
echo "=================================="
echo
echo "Next steps:"
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo
echo "2. Copy .env.template to .env and configure:"
echo "   cp .env.template .env"
echo "   # Then edit .env with your credentials"
echo
echo "3. Copy your cdl_db data:"
echo "   cp -r /path/to/cdl_db data/"
echo
echo "4. Run setup validation:"
echo "   python setup.py"
echo
echo "5. Run the pipeline:"
echo "   python run_pipeline.py"
echo

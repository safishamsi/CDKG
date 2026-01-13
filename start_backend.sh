#!/bin/bash
# Start backend with proper environment setup

echo "🚀 Starting CDKG RAG Backend..."
echo ""

# Use Python 3.9 to avoid protobuf issues
if command -v python3.9 &> /dev/null; then
    echo "Using Python 3.9..."
    python3.9 backend_api.py
else
    echo "Python 3.9 not found, using default python..."
    # Set environment variables to avoid tensorflow issues
    export TF_CPP_MIN_LOG_LEVEL=3
    export TRANSFORMERS_NO_TF=1
    python backend_api.py
fi


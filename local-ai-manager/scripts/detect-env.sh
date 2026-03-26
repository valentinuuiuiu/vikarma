#!/bin/bash
# Local AI Environment Detection Script
# Run this to detect available hardware and installed backends

set -e

echo "=== Local AI Environment Detection ==="
echo ""

# GPU Detection
echo "--- GPU Detection ---"
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU Found:"
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    echo ""
    echo "CUDA Available: $(python3 -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || echo 'PyTorch not installed')"
else
    echo "No NVIDIA GPU detected"
fi

# AMD GPU
if command -v rocm-smi &> /dev/null; then
    echo "AMD GPU Found:"
    rocm-smi --showproductname
fi

# Apple Silicon
if [[ "$(uname)" == "Darwin" ]] && [[ "$(sysctl -n machdep.cpu.brand_string)" == *"Apple"* ]]; then
    echo "Apple Silicon detected - Metal acceleration available"
fi

echo ""

# Backend Detection
echo "--- Backend Detection ---"

# Ollama
if command -v ollama &> /dev/null; then
    echo "✓ Ollama installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
    echo "  Models: $(ollama list 2>/dev/null | tail -n +2 | wc -l) installed"
    if pgrep -x "ollama" > /dev/null; then
        echo "  Status: RUNNING (pid $(pgrep -x ollama))"
    else
        echo "  Status: NOT RUNNING"
    fi
else
    echo "✗ Ollama not installed"
fi

# llama.cpp
if command -v main &> /dev/null || [ -f "$HOME/llama.cpp/main" ]; then
    echo "✓ llama.cpp available"
else
    echo "✗ llama.cpp not found"
fi

# LocalAI (Docker)
if docker ps --format '{{.Names}}' | grep -q localai; then
    echo "✓ LocalAI running in Docker"
    echo "  Endpoint: $(docker ps --filter name=localai --format '{{.Ports}}')"
else
    echo "✗ LocalAI not running"
fi

# vLLM
if python3 -c "import vllm" 2>/dev/null; then
    echo "✓ vLLM installed"
else
    echo "✗ vLLM not installed"
fi

# NVIDIA NIM
if command -v nim &> /dev/null || python3 -c "import nim" 2>/dev/null; then
    echo "✓ NVIDIA NIM available"
else
    echo "✗ NVIDIA NIM not installed"
fi

echo ""

# API Endpoints Check
echo "--- API Endpoints ---"
for port in 11434 8080 8000; do
    if curl -s --connect-timeout 1 "http://localhost:$port" > /dev/null 2>&1; then
        service="unknown"
        [ $port -eq 11434 ] && service="Ollama"
        [ $port -eq 8080 ] && service="LocalAI/vLLM"
        [ $port -eq 8000 ] && service="vLLM"
        echo "✓ Port $port ($service): ACTIVE"
    else
        echo "✗ Port $port: inactive"
    fi
done

echo ""
echo "=== Detection Complete ==="
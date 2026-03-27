#!/bin/bash
# Model Benchmarking Script
# Compares inference speed across different quantizations

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <model_name> [prompt]"
    echo "Example: $0 llama3.2 'What is the meaning of life?'"
    exit 1
fi

# Ensure required dependencies are available before running benchmarks
if ! command -v ollama >/dev/null 2>&1; then
    echo "Error: 'ollama' is not installed or not in PATH. Please install/configure ollama before running this benchmark."
    exit 1
fi

MODEL=$1
PROMPT=${2:-"Hello, how are you?"}
TIMES=3

echo "=== Benchmarking $MODEL ==="
echo "Prompt: $PROMPT"
echo "Runs: $TIMES"
echo ""

# Test default quantization
echo "--- Default Model ---"
for i in $(seq 1 $TIMES); do
    echo "Run $i:"
    time ollama run "$MODEL" "$PROMPT" 2>&1 | grep -E "eval|total" || true
    echo ""
done

# Check if quantized versions exist
for q in q4_0 q8_0; do
    MODEL_Q="${MODEL}:${q}"
    if ollama list | grep -q "$MODEL_Q"; then
        echo "--- $q Quantization ---"
        for i in $(seq 1 $TIMES); do
            echo "Run $i:"
            time ollama run "$MODEL_Q" "$PROMPT" 2>&1 | grep -E "eval|total" || true
            echo ""
        done
    fi
done

echo "=== Benchmark Complete ==="
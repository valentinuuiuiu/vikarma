#!/bin/bash
# Install Ollama and pull recommended models

set -e

echo "Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo ""
echo "Starting Ollama service..."
ollama serve &
sleep 5

echo ""
echo "Pulling recommended models..."
read -p "Pull llama3.2? [Y/n]: " pull_llama
if [[ "$pull_llama" != "n" ]]; then
    ollama pull llama3.2
fi

read -p "Pull mistral? [Y/n]: " pull_mistral
if [[ "$pull_mistral" != "n" ]]; then
    ollama pull mistral
fi

read -p "Pull codellama for coding? [y/N]: " pull_code
if [[ "$pull_code" == "y" ]]; then
    ollama pull codellama
fi

echo ""
echo "Installed models:"
ollama list

echo ""
echo "=== Ollama Setup Complete ==="
echo "API endpoint: http://localhost:11434"
echo "Test with: ollama run llama3.2"
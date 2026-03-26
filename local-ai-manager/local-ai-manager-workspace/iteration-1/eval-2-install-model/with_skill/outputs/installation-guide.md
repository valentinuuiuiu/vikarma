# Llama 3.2 Local Installation Guide for RTX 4090 (24GB VRAM)

## System Analysis

Your RTX 4090 with 24GB VRAM is excellent for running local LLMs. This GPU can comfortably run:
- Llama 3.2 3B (all quantizations)
- Llama 3.2 11B Vision (all quantizations)
- Llama 3.1 8B (all quantizations)
- Llama 3.1 70B (Q4 quantization - ~40GB VRAM needed, may need CPU offload)

## Recommended Backend: Ollama

For coding assistance, **Ollama** is recommended as the easiest backend to set up with excellent GPU acceleration support.

## Installation Steps

### Step 1: Verify NVIDIA Drivers

```bash
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
```

Ensure your RTX 4090 is detected and drivers are up to date.

### Step 2: Verify CUDA Toolkit

```bash
nvcc --version
```

If not installed:
```bash
# Ubuntu
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update && sudo apt install cuda
```

### Step 3: Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 4: Start Ollama Server

```bash
ollama serve &
```

### Step 5: Pull Llama 3.2

```bash
# Standard version (3B parameters - recommended for coding)
ollama pull llama3.2

# Vision version (11B parameters - for multimodal tasks)
ollama pull llama3.2-vision

# With specific quantization
ollama pull llama3.2:q4_0    # 4-bit (faster, less VRAM)
ollama pull llama3.2:q8_0    # 8-bit (more accurate)
```

### Step 6: Run Llama 3.2

```bash
ollama run llama3.2
```

## Coding Assistance Configuration

### For Best Coding Performance

Llama 3.2 3B is optimized for edge devices but may be limited for complex coding tasks. Consider these alternatives for better coding assistance:

```bash
# DeepSeek Coder - Excellent for code generation
ollama pull deepseek-coder:6.7b

# Code Llama - Meta's coding model
ollama pull codellama:7b

# StarCoder2 - Great for code completion
ollama pull starcoder2:7b
```

### GPU Memory Optimization

Your RTX 4090 has 24GB VRAM. For optimal performance:

```bash
# View GPU memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Force GPU offload (Ollama auto-detects, but you can specify)
OLLAMA_GPU_LAYER_COUNT=35 ollama run llama3.2
```

### Context Window Configuration

For coding tasks, larger context windows help with code analysis:

```bash
ollama run llama3.2 --context-window 8192
```

## API Integration

Ollama provides an OpenAI-compatible API on port 11434:

### Generate Endpoint

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Write a Python function to sort a list"
}'
```

### Chat Endpoint

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "Explain this code snippet"}
  ]
}'
```

### Python Integration

```python
import requests

def query_llama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "llama3.2", "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

# Example usage
result = query_llama("Write a function to merge two sorted lists")
print(result)
```

## Model Comparison for RTX 4090

| Model | Parameters | VRAM Required | Best For |
|-------|------------|---------------|----------|
| llama3.2 | 3B | ~2GB | Fast responses, simple tasks |
| llama3.2-vision | 11B | ~8GB | Multimodal (text + images) |
| llama3.1 | 8B | ~5GB | Better reasoning |
| deepseek-coder | 6.7B | ~4GB | Code generation |
| codellama | 7B | ~4GB | Code completion |
| llama3.1:70b-q4 | 70B | ~40GB | Complex reasoning (needs CPU offload) |

## Environment Variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Ollama configuration
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_ORIGINS="*"
export OLLAMA_GPU_LAYER_COUNT=35
```

## Management Commands

```bash
# List installed models
ollama list

# Show model details
ollama show llama3.2

# Update model
ollama pull llama3.2

# Delete model
ollama rm llama3.2

# Stop server
pkill ollama
```

## Troubleshooting

### GPU Not Detected

```bash
# Check driver
nvidia-smi

# Reinstall driver if needed
sudo apt install --reinstall nvidia-driver-535
```

### Out of Memory

```bash
# Use smaller quantization
ollama pull llama3.2:q4_0

# Reduce context window
ollama run llama3.2 --context-window 4096
```

### Slow Inference

```bash
# Verify GPU is being used
nvidia-smi  # Should show ollama process using GPU memory

# Explicitly set GPU layers
ollama run llama3.2 --gpu-layers 35
```

## Recommended Coding Workflow

1. **Primary Model**: `deepseek-coder:6.7b` or `codellama:7b` for code generation
2. **Fast Assistant**: `llama3.2` for quick queries and explanations
3. **Complex Analysis**: `llama3.1:8b` for reasoning tasks

## Security Notes

1. Bind Ollama to localhost only (`OLLAMA_HOST=127.0.0.1:11434`) unless intentionally exposing
2. Verify model sources are from official Ollama library or trusted Hugging Face repositories
3. Implement rate limiting if exposing API publicly

## Next Steps

1. Run `nvidia-smi` to verify GPU detection
2. Install Ollama: `curl -fsSL https://ollama.com/install.sh | sh`
3. Pull model: `ollama pull llama3.2`
4. Test: `ollama run llama3.2 "Write a hello world in Python"`
5. For coding: `ollama pull deepseek-coder:6.7b`
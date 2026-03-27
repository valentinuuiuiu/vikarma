---
name: local-ai-manager
description: Install, configure, and manage local AI models and intelligent assistants. Use this skill when the user mentions local AI, offline models, Ollama, llama.cpp, LocalAI, vLLM, NVIDIA NIM, TensorRT-LLM, GPU acceleration, running LLMs locally, downloading models, or managing local inference servers. Also triggers on queries about model comparison, hardware requirements, or switching between local AI backends.
---

# Local AI Manager

Manage offline AI models and intelligent assistants with full lifecycle support: installation, configuration, GPU acceleration, and monitoring.

## Supported Backends

| Backend | Best For | Status Check |
|---------|----------|--------------|
| **Ollama** | Easiest setup, wide model support | `ollama list` |
| **llama.cpp** | Direct GGUF execution, minimal deps | Binary check |
| **LocalAI** | OpenAI-compatible API, Docker-ready | API health check |
| **vLLM** | High-throughput serving, production use | API health check |
| **NVIDIA NIM** | Optimized inference, enterprise grade | `nvidia-nim list` |
| **TensorRT-LLM** | Maximum NVIDIA GPU performance | Engine compilation |

## Quick Start

### 1. System Check

First, detect available hardware and installed backends:

```bash
# GPU Detection
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

# Check installed backends
which ollama && ollama --version
which llama.cpp || which main (llama.cpp binary)
docker ps | grep -E "localai|vllm"
```

### 2. Install Backend

**Ollama (Recommended for beginners):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
```

**llama.cpp:**
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make
```

**LocalAI (Docker):**
```bash
docker run -d --gpus all -p 8080:8080 \
  -v ~/.localai/models:/models \
  --name localai \
  localai/localai:latest
```

**vLLM:**
```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server --model <model_name>
```

**NVIDIA NIM:**
```bash
pip install nvidia-nim
nim model pull <model_id>
```

### 3. Pull/Download Models

**Ollama:**
```bash
ollama pull llama3.2
ollama pull mistral
ollama pull codellama
ollama pull nvidia/llama-3.1-nemotron-ultra
```

**llama.cpp:**
```bash
# Download GGUF from Hugging Face
wget https://huggingface.co/<model>/resolve/main/model.gguf -O ~/.cache/llama.cpp/model.gguf
```

**NVIDIA NIM:**
```bash
nim model pull nvidia/llama-3.1-nemotron-70b
nim model pull nvidia/mistral-nemo
```

### 4. Run Inference

**Ollama:**
```bash
ollama run llama3.2
ollama run llama3.2 "Your prompt here"
```

**llama.cpp:**
```bash
./main -m ~/.cache/llama.cpp/model.gguf -p "Your prompt" -n 512
```

**API Mode (Ollama/LocalAI/vLLM):**
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello world"
}'
```

## GPU Acceleration

### NVIDIA GPU Setup

1. **Install CUDA Toolkit:**
   ```bash
   # Check CUDA version
   nvcc --version

   # Install if missing (Ubuntu)
   wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
   sudo dpkg -i cuda-keyring_1.1-1_all.deb
   sudo apt update && sudo apt install cuda
   ```

2. **Verify GPU visibility:**
   ```bash
   nvidia-smi
   python -c "import torch; print(torch.cuda.is_available())"
   ```

3. **Backend-specific GPU config:**

   **Ollama:**
   ```bash
   # Auto-detects GPU, configure explicitly:
   OLLAMA_GPU_LAYER_COUNT=35 ollama run llama3.2
   ```

   **llama.cpp:**
   ```bash
   ./main -m model.gguf -ngl 35 -bs 512
   ```

   **vLLM:**
   ```bash
   python -m vllm.entrypoints.openai.api_server \
     --model meta-llama/Llama-3.2-3B \
     --tensor-parallel-size 1 \
     --gpu-memory-utilization 0.9
   ```

### AMD GPU Setup

```bash
# ROCm installation
sudo apt install rocm
export HSA_OVERRIDE_GFX_VERSION=10.3.0  # For some models

# Ollama with ROCm
OLLAMA_GPU=amd ollama serve
```

### Apple Silicon

```bash
# Ollama auto-detects Metal
ollama run llama3.2

# llama.cpp Metal
make METAL=1
./main -m model.gguf -ngl 1
```

## Model Management

### List Installed Models

```bash
# Ollama
ollama list

# LocalAI (via API)
curl http://localhost:8080/v1/models

# vLLM (via API)
curl http://localhost:8000/v1/models

# NVIDIA NIM
nim model list
```

### Model Information

```bash
# Ollama model details
ollama show llama3.2

# Check model size/quantization
ls -lh ~/.ollama/models/
```

### Delete Models

```bash
ollama rm llama3.2
```

### Update Models

```bash
ollama pull llama3.2  # Pulls latest version
```

## API Endpoints

### Ollama API (port 11434)

```bash
# Generate
POST http://localhost:11434/api/generate

# Chat
POST http://localhost:11434/api/chat

# Embeddings
POST http://localhost:11434/api/embeddings
```

### OpenAI-Compatible (LocalAI/vLLM)

```bash
# Chat completions
POST http://localhost:8080/v1/chat/completions

# Embeddings
POST http://localhost:8080/v1/embeddings
```

## Integration with n8n

Connect local models to n8n workflows:

```json
{
  "nodes": [
    {
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://host.docker.internal:11434/api/generate",
        "method": "POST",
        "jsonParameters": true,
        "bodyParameters": {
          "model": "={{$json.model}}",
          "prompt": "={{$json.prompt}}"
        }
      }
    }
  ]
}
```

## Performance Tuning

### GPU Memory Optimization

```bash
# Check VRAM usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Quantized models use less VRAM
ollama pull llama3.2:q4_0   # 4-bit quantization
ollama pull llama3.2:q8_0   # 8-bit quantization
```

### Batch Processing

```bash
# vLLM batch inference
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.2-3B \
  --max-num-seqs 256
```

### Context Length

```bash
# Ollama
ollama run llama3.2 --context-window 8192

# llama.cpp
./main -m model.gguf -c 8192
```

## Troubleshooting

### GPU Not Detected

```bash
# Check driver
nvidia-smi

# Reinstall driver if needed
sudo apt install --reinstall nvidia-driver-535

# Docker GPU access
docker run --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Out of Memory

```bash
# Use smaller quantization
ollama pull llama3.2:q4_0

# Reduce context
ollama run llama3.2 --context-window 4096
```

### Slow Inference

```bash
# Enable GPU offload
ollama run llama3.2 --gpu-layers 35

# Use TensorRT-LLM for NVIDIA
nim model compile --backend tensorrt
```

## Model Recommendations by Use Case

| Use Case | Recommended Models |
|----------|-------------------|
| **Chat/Assistant** | llama3.2, mistral, nvidia/llama-3.1-nemotron |
| **Code Generation** | codellama, deepseek-coder, starcoder2 |
| **Embeddings** | nomic-embed-text, all-minilm |
| **Vision/Multimodal** | llava, bakllava |
| **Large Context** | mistral-nemo (128k), llama3.1 (128k) |

## Environment Variables

```bash
# Ollama
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_ORIGINS="*"
OLLAMA_GPU_LAYER_COUNT=35

# vLLM
VLLM_ATTENTION_BACKEND=FLASHINFER
VLLM_WORKER_MULTIPROC_METHOD=spawn

# LocalAI
LOCALAI_MODELS_PATH=/models
LOCALAI_THREADS=8
```

## Security Considerations

1. **API Exposure**: Bind to localhost only unless intentionally exposing
2. **Model Downloads**: Verify model sources (Hugging Face, official repos)
3. **Container Isolation**: Use Docker for untrusted models
4. **Rate Limiting**: Implement for production API endpoints
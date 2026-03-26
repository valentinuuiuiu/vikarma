# Ollama Comprehensive Guide

Ollama is the recommended backend for most local AI tasks due to its simplicity and robust model support.

## Installation

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Docker
```bash
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

## Model Management

### Common Commands
| Action | Command |
|--------|---------|
| **List** | `ollama list` |
| **Pull/Update** | `ollama pull <model>` |
| **Run** | `ollama run <model>` |
| **Remove** | `ollama rm <model>` |
| **Show Info** | `ollama show <model>` |

### Recommended Models
- **General/Chat**: `llama3.2`, `mistral`, `dolphin-llama3` (abliterated)
- **Coding**: `codellama`, `deepseek-coder:6.7b`
- **Vision**: `llama3.2-vision`, `moondream`
- **Embeddings**: `nomic-embed-text`, `all-minilm`

## Configuration

### Environment Variables
- `OLLAMA_HOST`: Set to `0.0.0.0:11434` to bind to all interfaces.
- `OLLAMA_ORIGINS`: Set to `*` to allow cross-origin requests.
- `OLLAMA_MODELS`: Path to store models (default: `~/.ollama/models`).

### Modelfiles
You can create custom agents using a `Modelfile`.
```docker
FROM llama3.2
SYSTEM "You are a specialized assistant for X."
PARAMETER temperature 0.7
```
Then create with: `ollama create my-agent -f Modelfile`

## GPU Acceleration
Ollama auto-detects NVIDIA and AMD GPUs. To verify:
```bash
nvidia-smi
# Check if 'ollama' is listed in the process table
```

### Manual Layer Offload
```bash
OLLAMA_GPU_LAYER_COUNT=35 ollama run llama3.2
```

## API Usage
Default endpoint: `http://localhost:11434`

### Generate
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Explain quantum physics",
  "stream": false
}'
```

### Chat
```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": false
}'
```

## Troubleshooting
- **Port Conflict**: Check `lsof -i :11434`.
- **GPU Not Found**: Ensure NVIDIA drivers and `nvidia-container-toolkit` are installed.
- **OOM**: Use smaller quantization (e.g., `q4_0`).

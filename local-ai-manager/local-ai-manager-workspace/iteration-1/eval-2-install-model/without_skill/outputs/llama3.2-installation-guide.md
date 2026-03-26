# Llama 3.2 Local Installation Guide for RTX 4090 (24GB VRAM)

## System Requirements Check

Your RTX 4090 with 24GB VRAM is excellent for running Llama 3.2 models. Here's what you can run:

| Model | Parameters | VRAM Required | Recommended for RTX 4090 |
|-------|------------|---------------|--------------------------|
| Llama 3.2 1B | 1B | ~2-3 GB | Fast, lightweight |
| Llama 3.2 3B | 3B | ~6-8 GB | Good balance |
| Llama 3.2 11B | 11B | ~20-24 GB | Full fit in VRAM |
| Llama 3.2 90B | 90B | ~180+ GB | Requires multi-GPU or heavy quantization |

**Recommendation for RTX 4090: Llama 3.2 11B Vision or 3B Text model**

---

## Option 1: Ollama (Recommended - Easiest)

Ollama is the simplest way to run Llama models locally with GPU acceleration.

### Installation

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh

# After installation, Ollama runs as a service
```

### Pull and Run Llama 3.2

```bash
# Pull the model
ollama pull llama3.2:3b

# For the larger instruct model
ollama pull llama3.2:latest

# Run interactively
ollama run llama3.2:3b

# For coding assistance, the instruct variant works well
ollama pull llama3.2:3b-instruct
ollama run llama3.2:3b-instruct
```

### GPU Configuration

Ollama auto-detects NVIDIA GPUs. Verify GPU usage:
```bash
nvidia-smi
# You should see ollama process using GPU memory
```

### API Access for Coding Tools

```bash
# Ollama exposes an API at localhost:11434
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Write a Python function to sort a list"
}'
```

---

## Option 2: LM Studio (GUI-Based)

LM Studio provides a user-friendly interface for running local models.

### Installation

1. Download from: https://lmstudio.ai/
2. Install the Linux AppImage or package
3. Open LM Studio

### Setup

1. Search for "Llama 3.2" in the search bar
2. Download your preferred variant (3B or 11B recommended)
3. Go to the "Chat" tab
4. Select the model from the dropdown
5. Enable GPU acceleration in settings (Settings > GPU)

### Configuration for RTX 4090

- **GPU Layers**: Set to maximum (-1 or all layers)
- **Context Length**: 8192-32768 tokens (adjust based on needs)
- **Batch Size**: 512 (default works well)

---

## Option 3: Using Hugging Face Transformers (Python)

For more control and integration with Python applications.

### Installation

```bash
# Create virtual environment
python -m venv llama-env
source llama-env/bin/activate

# Install dependencies
pip install torch transformers accelerate bitsandbytes
```

### Python Code to Run Llama 3.2

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "meta-llama/Llama-3.2-3B-Instruct"

# Load tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Load model with GPU
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
    attn_implementation="flash_attention_2"  # Faster inference
)

# Example coding prompt
prompt = """
Write a Python function that implements a binary search tree with insert and search operations.
"""

inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(
    **inputs,
    max_new_tokens=2048,
    temperature=0.7,
    top_p=0.9
)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

---

## Option 4: vLLM (High-Performance Inference Server)

Best for production use and serving multiple requests.

### Installation

```bash
pip install vllm
```

### Run Server

```bash
# Start the server
vllm serve meta-llama/Llama-3.2-3B-Instruct --tensor-parallel-size 1

# Or with OpenAI-compatible API
vllm serve meta-llama/Llama-3.2-3B-Instruct --api-key your-key
```

### Use with OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="your-key")

response = client.chat.completions.create(
    model="meta-llama/Llama-3.2-3B-Instruct",
    messages=[{"role": "user", "content": "Write a Python HTTP client"}]
)
print(response.choices[0].message.content)
```

---

## Configuration Tips for RTX 4090

### Optimal Settings

```yaml
# For Ollama modelfile
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
PARAMETER num_gpu 99  # Use all GPU layers
```

### Quantization Options

If you want to run larger models:

```bash
# Q4_K_M quantization (4-bit) - fits 11B model comfortably
ollama pull llama3.2:11b-q4_K_M

# Q8_0 quantization (8-bit) - higher quality, more VRAM
ollama pull llama3.2:11b-q8_0
```

---

## Integration with Coding Tools

### Continue.dev (VS Code Extension)

1. Install Continue extension in VS Code
2. Configure `~/.continue/config.json`:

```json
{
  "models": [
    {
      "title": "Llama 3.2 Local",
      "provider": "ollama",
      "model": "llama3.2:3b"
    }
  ]
}
```

### Aider (CLI Coding Assistant)

```bash
pip install aider-chat

# Use with Ollama
aider --model ollama_chat/llama3.2:3b

# Or with local model
export OLLAMA_API_BASE=http://localhost:11434
aider --model ollama/llama3.2:3b
```

---

## Performance Expectations

| Model | Tokens/sec (RTX 4090) | Quality | Use Case |
|-------|----------------------|---------|----------|
| Llama 3.2 1B | 150-200+ | Basic | Quick completions |
| Llama 3.2 3B | 80-120 | Good | General coding |
| Llama 3.2 11B (Q4) | 40-60 | Excellent | Complex reasoning |

---

## Troubleshooting

### GPU Not Detected

```bash
# Check CUDA
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# For Ollama, set environment
export CUDA_VISIBLE_DEVICES=0
```

### Out of Memory

```bash
# Use smaller context
ollama run llama3.2:3b --num-ctx 4096

# Or use quantized version
ollama pull llama3.2:3b-q4_K_M
```

---

## Quick Start Recommendation

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull recommended model for coding
ollama pull llama3.2:3b-instruct

# 3. Run it
ollama run llama3.2:3b-instruct

# 4. Test coding prompt
>>> Write a Python function to find all prime numbers up to n using the Sieve of Eratosthenes
```

---

## Resources

- Ollama: https://ollama.ai/
- LM Studio: https://lmstudio.ai/
- Llama 3.2 on Hugging Face: https://huggingface.co/meta-llama
- vLLM: https://github.com/vllm-project/vllm
- Continue.dev: https://continue.dev/
- Aider: https://aider.chat/

---

*Guide generated for RTX 4090 (24GB VRAM) system*
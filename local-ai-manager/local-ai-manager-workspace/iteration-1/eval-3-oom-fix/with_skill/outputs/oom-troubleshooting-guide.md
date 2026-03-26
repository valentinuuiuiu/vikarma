# Out of Memory (OOM) Troubleshooting Guide
## RTX 3060 (12GB VRAM) and Llama 3.2 70B

---

## The Problem

You are experiencing OOM errors when trying to run **llama3.2 70B** on an **RTX 3060 (12GB VRAM)**. This is expected behavior because:

| Model | Parameters | FP16 Size | Q4_0 Size | Q8_0 Size |
|-------|------------|-----------|-----------|-----------|
| Llama 3.2 70B | 70 billion | ~140 GB | ~40 GB | ~75 GB |

**Your RTX 3060 has only 12GB VRAM.** Even with extreme quantization, a 70B model requires approximately 35-40GB minimum, which far exceeds your hardware capacity.

---

## Solutions

### Solution 1: Use a Smaller Model (Recommended)

The RTX 3060 12GB is well-suited for models up to 14B parameters with proper quantization. Here are appropriate alternatives:

| Model | Size | VRAM Required (Q4) | Fits RTX 3060? |
|-------|------|-------------------|----------------|
| **Llama 3.2 3B** | 3B | ~2 GB | Yes (plenty of headroom) |
| **Llama 3.2 1B** | 1B | ~0.8 GB | Yes |
| **Llama 3.1 8B** | 8B | ~5 GB | Yes |
| **Mistral 7B** | 7B | ~4.5 GB | Yes |
| **Gemma 2 9B** | 9B | ~6 GB | Yes |
| **Qwen 2.5 7B** | 7B | ~4.5 GB | Yes |
| **Phi-3 Medium** | 14B | ~8-10 GB | Yes (tight fit) |

**Recommended for your GPU:**
```bash
# Best balance of quality and speed
ollama pull llama3.2:3b

# For code generation
ollama pull codellama:7b

# For fast responses
ollama pull llama3.2:1b

# For general chat (excellent quality)
ollama pull mistral:7b
```

### Solution 2: Aggressive Quantization (If You Must Use Larger Models)

If you need to run a model larger than 12GB worth of parameters, use extreme quantization:

```bash
# Use IQ3_XXS or Q2_K quantization (severely degraded quality)
ollama pull llama3.2:iq3_xxs

# Or Q4_0 standard quantization
ollama pull llama3.2:q4_0
```

**Warning:** For 70B models, even Q4_0 requires ~40GB VRAM. This will NOT work on a 12GB card.

### Solution 3: CPU Offloading (llama.cpp)

Use llama.cpp to offload layers to CPU RAM:

```bash
# Build llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make

# Run with GPU/CPU split (some layers on GPU, rest on CPU)
./main -m llama-3.2-70b-q4_0.gguf \
    -ngl 10 \          # Only 10 layers on GPU (adjust based on VRAM)
    --n-gpu-layers 10 \
    -c 4096 \          # Reduced context
    -b 512             # Smaller batch

# Note: This will be SLOW but will run
```

**Tuning GPU layers for 12GB:**
- Start with `-ngl 10` and increase until you hit OOM
- Each layer uses approximately VRAM proportional to model size
- For a 70B model, even 1-2 layers may fill 12GB

### Solution 4: Context Window Reduction

If running a model that barely fits, reduce context:

```bash
# Ollama
ollama run llama3.2:3b --context-window 4096

# llama.cpp
./main -m model.gguf -c 4096
```

### Solution 5: Multi-GPU or Cloud Offloading

For models that exceed your VRAM significantly:

1. **Use cloud inference:**
   ```bash
   # Use Ollama cloud or similar services
   # Or use API-based models (OpenAI, Anthropic, etc.)
   ```

2. **Distributed inference (requires multiple GPUs):**
   ```bash
   # vLLM with tensor parallelism (multiple GPUs needed)
   python -m vllm.entrypoints.openai.api_server \
       --model meta-llama/Llama-3.2-70B \
       --tensor-parallel-size 4  # Requires 4+ GPUs
   ```

---

## Quick Fix Commands for RTX 3060 12GB

### Immediate Solution - Use Appropriate Model

```bash
# Check available models
ollama list

# Pull a model that fits your GPU
ollama pull llama3.2:3b

# Verify GPU is detected
nvidia-smi

# Run the model
ollama run llama3.2:3b
```

### Check VRAM Usage

```bash
# Before running model
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# After running model (in another terminal)
watch -n 1 nvidia-smi
```

---

## Model Size Calculator

Approximate VRAM requirements:

| Quantization | Formula |
|--------------|---------|
| FP16 | `params_billion * 2 GB` |
| Q8_0 | `params_billion * 1 GB` |
| Q6_K | `params_billion * 0.8 GB` |
| Q5_0 | `params_billion * 0.7 GB` |
| Q4_0 | `params_billion * 0.5 GB` |
| Q3_K | `params_billion * 0.4 GB` |
| Q2_K | `params_billion * 0.3 GB` |

**Example:** For 70B model with Q4_0:
`70 * 0.5 = 35 GB VRAM` (plus overhead for context, activations)

---

## Recommended Models for RTX 3060 12GB

### Best Performance/Quality Balance
```bash
ollama pull llama3.2:3b        # Excellent quality, fast
ollama pull mistral:7b         # Great general-purpose model
ollama pull gemma2:9b          # Strong reasoning capabilities
```

### For Code Generation
```bash
ollama pull codellama:7b       # Code-specialized
ollama pull deepseek-coder:6.7b # Excellent code model
ollama pull starcoder2:7b      # Code generation focused
```

### For Fast Responses
```bash
ollama pull llama3.2:1b        # Very fast, acceptable quality
ollama pull phi3:mini          # Microsoft's efficient model
```

---

## Troubleshooting Commands

```bash
# Check GPU status
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv

# Kill runaway processes
pkill -f ollama

# Clear GPU memory
sudo fuser -v /dev/nvidia*  # Find processes using GPU
kill -9 <pid>               # Kill specific process

# Check Ollama logs
journalctl -u ollama -f

# Verify CUDA installation
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'CUDA devices: {torch.cuda.device_count()}')"
```

---

## Summary

**Your RTX 3060 (12GB VRAM) cannot run Llama 3.2 70B.** The model requires approximately 35-40GB even with 4-bit quantization.

**Immediate action:** Switch to a smaller model:
```bash
ollama pull llama3.2:3b    # Fits comfortably with room for context
ollama run llama3.2:3b
```

**If you need larger models:** Consider upgrading to an RTX 4090 (24GB), RTX 3090 (24GB), or using cloud inference services.
# Out of Memory (OOM) Troubleshooting Guide
## Running Llama 3.2 70B on RTX 3060 (12GB VRAM)

---

## The Problem

Your RTX 3060 has 12GB VRAM, but a 70B parameter model requires significantly more memory:

| Precision | Memory Required (70B model) |
|-----------|----------------------------|
| FP32      | ~280 GB                    |
| FP16      | ~140 GB                    |
| INT8      | ~70 GB                     |
| INT4      | ~35-40 GB                  |

**12GB VRAM is insufficient for a 70B model even at 4-bit quantization.**

---

## Solutions

### Solution 1: Use CPU + GPU Offloading (Recommended for your hardware)

Use **llama.cpp** or **Ollama** with CPU offloading to utilize system RAM:

#### Using llama.cpp
```bash
# Build with CUDA support
make LLAMA_CUDA=1

# Run with GPU layers (adjust based on your VRAM)
./main -m llama-3.2-70b-q4_k_m.gguf \
    --n-gpu-layers 20 \
    --ctx-size 4096 \
    --threads 8
```

#### Using Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Run with automatic offloading
ollama run llama3.2:70b

# Force specific GPU layers (if needed)
OLLAMA_NUM_GPU=20 ollama run llama3.2:70b
```

---

### Solution 2: Use a Smaller Model (Best for RTX 3060)

For 12GB VRAM, consider these models instead:

| Model | Size | Memory (INT4) | Notes |
|-------|------|---------------|-------|
| Llama 3.2 3B | 3B | ~2-3 GB | Fits comfortably |
| Llama 3.2 11B | 11B | ~7-8 GB | Good fit with context |
| Llama 3.1 8B | 8B | ~5-6 GB | Excellent choice |
| Mistral 7B | 7B | ~4-5 GB | Fast and capable |
| Mixtral 8x7B | 47B | ~24-26 GB | Needs CPU offload |

```bash
# Recommended for RTX 3060 12GB
ollama run llama3.2:3b
ollama run llama3.1:8b
ollama run mistral:7b
```

---

### Solution 3: Aggressive Quantization

If you must run 70B, use extreme quantization:

```bash
# IQ2_XXS quantization (~20GB total, still needs CPU offload)
./main -m llama-3.2-70b-iq2_xxs.gguf \
    --n-gpu-layers 15 \
    --ctx-size 2048 \
    --threads 8
```

---

### Solution 4: Reduce Context Window

Smaller context means less KV cache memory:

```bash
# Reduce context from default 4096 to 1024 or 2048
./main -m model.gguf --ctx-size 1024
```

---

### Solution 5: Use Multiple GPUs or Cloud

If you need 70B quality:
- **Multi-GPU setup**: 2x RTX 3060 (24GB total) can run INT4 quantized 70B
- **Cloud options**: RunPod, Lambda Labs, AWS, or use free tier of services like Hugging Face Spaces

---

## Quick Reference: Maximum Model Size for 12GB VRAM

| Quantization | Max Parameters | Recommended Model |
|--------------|----------------|-------------------|
| INT4         | ~20-24B        | Llama 3.1 8B, Mistral 7B |
| INT8         | ~10-12B        | Llama 3.2 11B |
| FP16         | ~5-6B          | Llama 3.2 3B |

---

## Ollama GPU Layer Tuning

Fine-tune GPU offloading with these environment variables:

```bash
# Number of layers to offload to GPU (start low, increase until OOM)
OLLAMA_NUM_GPU=15

# Flash attention (reduces memory)
OLLAMA_FLASH_ATTENTION=1

# KV cache quantization
OLLAMA_KV_CACHE_TYPE=q4_0
```

---

## Summary

**For RTX 3060 12GB, your best options are:**

1. **Best Experience**: Use Llama 3.1 8B or Mistral 7B (fits entirely on GPU)
2. **If you need larger models**: Use CPU offloading with llama.cpp/Ollama (slower but works)
3. **For 70B specifically**: Not recommended for 12GB VRAM - consider cloud or smaller quantized models

The 70B model is simply too large for 12GB VRAM, even with aggressive quantization. CPU offloading will work but expect slower inference speeds.
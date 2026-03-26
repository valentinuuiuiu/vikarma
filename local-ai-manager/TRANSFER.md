# Local AI Manager Skill - Quick Install

## One-Line Install (for customers)

```bash
curl -fsSL https://raw.githubusercontent.com/vvvxxx111/vikarma/main/skills/local-ai-manager/install.sh | bash
```

## Manual Install

1. Copy the `local-ai-manager` folder to `~/.claude/plugins/`
2. Restart Claude Code
3. Ask: "Check my local AI setup"

## What This Skill Does

- **GPU Detection**: Auto-detects NVIDIA, AMD, Apple Silicon GPUs
- **Backend Management**: Ollama, llama.cpp, LocalAI, vLLM, NVIDIA NIM
- **Model Installation**: Pull, run, and manage local LLMs
- **Troubleshooting**: OOM fixes, GPU config, performance tuning

## Skill Transfer to Customer VS Code

When you connect to a customer's VS Code instance, Claude Code can transfer skills by:

### Option 1: Copy via MCP/File Access
```bash
# Copy skill to customer's machine
cp -r ~/.claude/plugins/local-ai-manager /customer/workspace/.claude/plugins/
```

### Option 2: Install Script
Run the install script on the customer machine:
```bash
# Customer runs this in their terminal
curl -fsSL https://raw.githubusercontent.com/vvvxxx111/vikarma/main/skills/local-ai-manager/install.sh | bash
```

### Option 3: Inline Skill Definition
If file access is limited, paste the skill content:

```markdown
Copy the contents of SKILL.md and save to:
~/.claude/plugins/local-ai-manager/SKILL.md
```

## Testing the Skill

After installation, test with these queries:

| Test Query | Expected Behavior |
|-----------|-------------------|
| "Check my GPU setup" | Runs `nvidia-smi`, lists installed backends |
| "Install llama3.2 for coding" | Provides Ollama install commands, model recommendations |
| "OOM error with RTX 3060" | Suggests smaller models, quantization, CPU offload |

## Files Structure

```
local-ai-manager/
├── SKILL.md           # Main skill definition
├── install.sh         # Installation script
├── scripts/
│   ├── detect-env.sh  # System detection
│   ├── install-ollama.sh
│   └── benchmark.sh
├── references/        # Additional docs (optional)
└── assets/           # Templates (optional)
```
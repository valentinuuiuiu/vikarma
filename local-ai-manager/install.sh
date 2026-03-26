#!/bin/bash
# Local AI Manager Skill - Installation Script
# Run this to install the skill for Claude Code

set -e

SKILL_DIR="$HOME/.claude/plugins/local-ai-manager"
SKILL_URL="https://github.com/vvvxxx111/vikarma/raw/main/skills/local-ai-manager.tar.gz"

echo "=== Local AI Manager Skill Installer ==="
echo ""

# Check if running in Claude Code environment
if [ ! -d "$HOME/.claude" ]; then
    echo "Creating .claude directory..."
    mkdir -p "$HOME/.claude/plugins"
fi

# Create plugins directory if needed
mkdir -p "$HOME/.claude/plugins"

# Copy skill files
echo "Installing skill to $SKILL_DIR..."
mkdir -p "$SKILL_DIR"
cp -r "$(dirname "$0")/SKILL.md" "$SKILL_DIR/" 2>/dev/null || {
    # If not running from local dir, download
    echo "Downloading from remote..."
    curl -fsSL "$SKILL_URL" | tar -xzf - -C "$HOME/.claude/plugins/"
}

# Make scripts executable
chmod +x "$SKILL_DIR/scripts/"*.sh 2>/dev/null || true

echo ""
echo "✓ Local AI Manager skill installed!"
echo ""
echo "Usage: Simply ask Claude about local AI, Ollama, or GPU models."
echo "Examples:"
echo "  - 'Check my GPU and installed models'"
echo "  - 'Install llama3.2 for coding'"
echo "  - 'Why am I getting out of memory errors?'"
echo ""
echo "To uninstall: rm -rf $SKILL_DIR"
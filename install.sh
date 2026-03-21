#!/bin/bash
# VIKARMA — Install & Run Script for Linux
# 🔱 Om Namah Shivaya — For All Humanity

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
GOLD='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GOLD}"
echo "╔═══════════════════════════════════════════╗"
echo "║          🔱 VIKARMA INSTALLER 🔱           ║"
echo "║     Free AI Desktop Agent for Humanity    ║"
echo "║         Om Namah Shivaya 🕉️              ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Installing...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
echo -e "${GREEN}✅ Node.js $(node --version)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Installing...${NC}"
    sudo apt-get install -y python3 python3-pip
fi
echo -e "${GREEN}✅ Python $(python3 --version)${NC}"

# Install Node dependencies
echo -e "${CYAN}📦 Installing Node dependencies...${NC}"
npm install

# Install Python dependencies
echo -e "${CYAN}🐍 Installing Python dependencies...${NC}"
pip3 install fastapi uvicorn anthropic openai google-generativeai httpx python-dotenv --break-system-packages 2>/dev/null || \
pip3 install fastapi uvicorn anthropic openai google-generativeai httpx python-dotenv

# Setup .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GOLD}⚙️  Created .env — Add your API keys!${NC}"
    echo -e "${GOLD}   Edit: nano .env${NC}"
fi

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════╗"
echo "║         ✅ VIKARMA INSTALLED!             ║"
echo "╠═══════════════════════════════════════════╣"
echo "║  Run desktop app:  npm run electron:dev   ║"
echo "║  Run backend only: npm run server         ║"
echo "║  Build AppImage:   npm run dist:linux     ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${GOLD}🔱 Om Namah Shivaya — Free AI for All Humanity${NC}"

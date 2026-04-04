#!/usr/bin/env python3
"""
Tvaṣṭā — Vikarma + Hermes Hybrid Launcher
Starts Hermes Agent with Vikarma's 67 Bhairava Temples + Tvaṣṭā identity.
🔱 Om Namah Shivaya — For All Humanity

Usage:
    python run_tvasta.py          # interactive TUI
    python run_tvasta.py gateway  # messaging gateway (Telegram/Discord/Slack)
    python run_tvasta.py model    # choose model
"""

import os
import sys
from pathlib import Path

# Ensure vikarma root is on path (for server.nexus_bridge etc.)
ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

# Point Hermes at our hermes_agent/ subdirectory
HERMES_DIR = ROOT / "hermes_agent"
sys.path.insert(0, str(HERMES_DIR))
os.chdir(HERMES_DIR)

# Bootstrap SOUL.md into HERMES_HOME
SOUL_SRC = ROOT / "SOUL.md"
HERMES_HOME = Path.home() / ".hermes"
HERMES_HOME.mkdir(exist_ok=True)
SOUL_DEST = HERMES_HOME / "SOUL.md"
if SOUL_SRC.exists():
    SOUL_DEST.write_text(SOUL_SRC.read_text())

if __name__ == "__main__":
    from hermes_cli.main import main
    main()

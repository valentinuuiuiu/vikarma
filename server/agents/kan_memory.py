"""
VIKARMA — KAN (Knowledge Augmented Network) Memory
Persistent memory that survives between sessions.
The sacred mind that never forgets.
🔱 Om Namah Shivaya — For All Humanity
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Optional, Any
from datetime import datetime


class KANMemory:
    """
    Knowledge Augmented Network — persistent memory for Vikarma.
    
    Three memory tiers:
    - Short-term: current session (RAM)
    - Long-term: facts, preferences, knowledge (disk JSON)
    - Episodic: conversation history (disk JSON)
    """

    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or os.path.expanduser("~/.vikarma/memory"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.facts_file = self.storage_dir / "facts.json"
        self.episodes_file = self.storage_dir / "episodes.json"
        self.prefs_file = self.storage_dir / "preferences.json"

        # Short-term (RAM)
        self.short_term: list[dict] = []
        self.MAX_SHORT_TERM = 50

        # Load long-term from disk
        self.facts: dict = self._load(self.facts_file, {})
        self.preferences: dict = self._load(self.prefs_file, {})
        self.episodes: list = self._load(self.episodes_file, [])

    # ── Short-term Memory ──────────────────────────────────────────────────

    def remember_now(self, content: str, role: str = "user", metadata: dict = None) -> None:
        """Add to short-term memory (current session)"""
        entry = {
            "content": content,
            "role": role,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        self.short_term.append(entry)
        if len(self.short_term) > self.MAX_SHORT_TERM:
            self.short_term.pop(0)

    def get_recent(self, n: int = 10) -> list[dict]:
        """Get n most recent short-term memories"""
        return self.short_term[-n:]

    def get_context_window(self, n: int = 20) -> list[dict]:
        """Get formatted context for AI (role + content pairs)"""
        recent = self.get_recent(n)
        return [{"role": m["role"], "content": m["content"]} for m in recent]

    # ── Long-term Facts ────────────────────────────────────────────────────

    def remember_fact(self, key: str, value: Any, category: str = "general") -> dict:
        """Store a long-term fact"""
        fact_id = hashlib.md5(key.encode()).hexdigest()[:8]
        self.facts[fact_id] = {
            "key": key,
            "value": value,
            "category": category,
            "created": time.time(),
            "updated": time.time(),
            "accessed": 0,
        }
        self._save(self.facts_file, self.facts)
        return {"stored": True, "id": fact_id, "key": key}

    def recall_fact(self, query: str) -> list[dict]:
        """Search facts by keyword"""
        query_lower = query.lower()
        results = []
        for fact_id, fact in self.facts.items():
            key_match = query_lower in fact["key"].lower()
            val_match = query_lower in str(fact["value"]).lower()
            if key_match or val_match:
                fact["id"] = fact_id
                fact["accessed"] += 1
                results.append(fact)
        if results:
            self._save(self.facts_file, self.facts)
        return results

    def forget_fact(self, fact_id: str) -> dict:
        """Remove a fact"""
        if fact_id in self.facts:
            del self.facts[fact_id]
            self._save(self.facts_file, self.facts)
            return {"deleted": True, "id": fact_id}
        return {"error": f"Fact {fact_id} not found"}

    def list_facts(self, category: str = None) -> list[dict]:
        """List all facts, optionally filtered by category"""
        facts = list(self.facts.values())
        if category:
            facts = [f for f in facts if f.get("category") == category]
        return sorted(facts, key=lambda x: x.get("updated", 0), reverse=True)

    # ── Preferences ────────────────────────────────────────────────────────

    def set_preference(self, key: str, value: Any) -> dict:
        """Store user preference"""
        self.preferences[key] = {"value": value, "updated": time.time()}
        self._save(self.prefs_file, self.preferences)
        return {"stored": True, "key": key, "value": value}

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        pref = self.preferences.get(key)
        return pref["value"] if pref else default

    def get_all_preferences(self) -> dict:
        """Get all preferences as key:value dict"""
        return {k: v["value"] for k, v in self.preferences.items()}

    # ── Episodic Memory ────────────────────────────────────────────────────

    def save_episode(self, title: str, summary: str, messages: list, provider: str = "claude") -> dict:
        """Save a conversation episode to long-term episodic memory"""
        episode = {
            "id": hashlib.md5(f"{title}{time.time()}".encode()).hexdigest()[:8],
            "title": title,
            "summary": summary,
            "provider": provider,
            "message_count": len(messages),
            "created": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "messages": messages[-5:],  # Keep last 5 messages of episode
        }
        self.episodes.append(episode)
        # Keep last 100 episodes
        if len(self.episodes) > 100:
            self.episodes = self.episodes[-100:]
        self._save(self.episodes_file, self.episodes)
        return {"saved": True, "id": episode["id"], "title": title}

    def search_episodes(self, query: str) -> list[dict]:
        """Search episodic memory"""
        query_lower = query.lower()
        results = []
        for ep in self.episodes:
            if (query_lower in ep.get("title", "").lower() or
                query_lower in ep.get("summary", "").lower()):
                results.append(ep)
        return results[-10:]  # Return max 10

    def get_recent_episodes(self, n: int = 5) -> list[dict]:
        """Get n most recent episodes"""
        return self.episodes[-n:]

    # ── Memory Summary for AI Context ──────────────────────────────────────

    def build_context_summary(self) -> str:
        """Build a memory summary to inject into AI context"""
        lines = ["🧠 VIKARMA KAN Memory Context:"]

        # Preferences
        prefs = self.get_all_preferences()
        if prefs:
            lines.append(f"\n📌 User Preferences:")
            for k, v in list(prefs.items())[:5]:
                lines.append(f"  • {k}: {v}")

        # Recent facts
        facts = self.list_facts()[:5]
        if facts:
            lines.append(f"\n💡 Known Facts:")
            for f in facts:
                lines.append(f"  • {f['key']}: {f['value']}")

        # Recent episodes
        episodes = self.get_recent_episodes(3)
        if episodes:
            lines.append(f"\n📚 Recent Conversations:")
            for ep in episodes:
                lines.append(f"  • [{ep['date']}] {ep['title']}: {ep['summary'][:60]}")

        return "\n".join(lines) if len(lines) > 1 else ""

    def get_stats(self) -> dict:
        """Get memory statistics"""
        return {
            "short_term": len(self.short_term),
            "facts": len(self.facts),
            "preferences": len(self.preferences),
            "episodes": len(self.episodes),
            "storage_dir": str(self.storage_dir),
        }

    # ── Persistence ────────────────────────────────────────────────────────

    def _load(self, path: Path, default: Any) -> Any:
        try:
            if path.exists():
                return json.loads(path.read_text())
            return default
        except Exception:
            return default

    def _save(self, path: Path, data: Any) -> None:
        try:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            pass

    def export_all(self) -> dict:
        """Export all memory"""
        return {
            "facts": self.facts,
            "preferences": self.preferences,
            "episodes": self.episodes,
            "short_term": self.short_term,
            "stats": self.get_stats(),
        }

    def clear_all(self) -> dict:
        """Clear all memory (dangerous!)"""
        self.short_term.clear()
        self.facts.clear()
        self.preferences.clear()
        self.episodes.clear()
        self._save(self.facts_file, {})
        self._save(self.prefs_file, {})
        self._save(self.episodes_file, [])
        return {"cleared": True}

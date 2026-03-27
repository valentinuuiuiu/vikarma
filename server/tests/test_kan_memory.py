"""
Tests for KANMemory — VIKARMA Knowledge Augmented Network Memory
"""

import json
import pytest
import tempfile
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from server.agents.kan_memory import KANMemory


@pytest.fixture
def mem(tmp_path):
    """Fresh KANMemory backed by a temp directory."""
    return KANMemory(storage_dir=str(tmp_path))


# ── Short-term memory ──────────────────────────────────────────────────────────

class TestShortTermMemory:
    def test_remember_now_adds_entry(self, mem):
        mem.remember_now("hello world", role="user")
        assert len(mem.short_term) == 1
        assert mem.short_term[0]["content"] == "hello world"
        assert mem.short_term[0]["role"] == "user"

    def test_remember_now_stores_timestamp(self, mem):
        before = time.time()
        mem.remember_now("msg")
        after = time.time()
        ts = mem.short_term[0]["timestamp"]
        assert before <= ts <= after

    def test_max_short_term_evicts_oldest(self, mem):
        for i in range(55):
            mem.remember_now(f"msg-{i}")
        assert len(mem.short_term) == mem.MAX_SHORT_TERM
        # Oldest entries are gone, newest survive
        assert mem.short_term[-1]["content"] == "msg-54"

    def test_get_recent_returns_n_entries(self, mem):
        for i in range(20):
            mem.remember_now(f"m{i}")
        recent = mem.get_recent(5)
        assert len(recent) == 5
        assert recent[-1]["content"] == "m19"

    def test_get_context_window_formats_for_ai(self, mem):
        mem.remember_now("question", role="user")
        mem.remember_now("answer", role="assistant")
        ctx = mem.get_context_window(10)
        assert ctx == [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "answer"},
        ]

    def test_get_context_window_respects_limit(self, mem):
        for i in range(30):
            mem.remember_now(f"m{i}", role="user")
        ctx = mem.get_context_window(5)
        assert len(ctx) == 5


# ── Long-term facts ────────────────────────────────────────────────────────────

class TestLongTermFacts:
    def test_remember_fact_stores_and_persists(self, mem, tmp_path):
        result = mem.remember_fact("user_name", "Alice")
        assert result["stored"] is True
        assert "id" in result

        # Reload from disk
        mem2 = KANMemory(storage_dir=str(tmp_path))
        facts = mem2.list_facts()
        assert any(f["key"] == "user_name" for f in facts)

    def test_remember_fact_returns_id(self, mem):
        r = mem.remember_fact("color", "blue")
        assert len(r["id"]) == 8  # MD5 truncated to 8 chars

    def test_recall_fact_by_key(self, mem):
        mem.remember_fact("project_name", "vikarma")
        results = mem.recall_fact("project")
        assert len(results) >= 1
        assert results[0]["key"] == "project_name"

    def test_recall_fact_by_value(self, mem):
        mem.remember_fact("lang", "python3")
        results = mem.recall_fact("python3")
        assert len(results) >= 1

    def test_recall_fact_case_insensitive(self, mem):
        mem.remember_fact("Framework", "FastAPI")
        results = mem.recall_fact("fastapi")
        assert len(results) >= 1

    def test_recall_fact_increments_accessed(self, mem):
        r = mem.remember_fact("k", "v")
        fid = r["id"]
        mem.recall_fact("k")
        mem.recall_fact("k")
        assert mem.facts[fid]["accessed"] == 2

    def test_recall_no_match_returns_empty(self, mem):
        mem.remember_fact("foo", "bar")
        assert mem.recall_fact("zzznomatch") == []

    def test_forget_fact_removes_entry(self, mem):
        r = mem.remember_fact("temp", "delete_me")
        fid = r["id"]
        result = mem.forget_fact(fid)
        assert result["deleted"] is True
        assert fid not in mem.facts

    def test_forget_nonexistent_fact_returns_error(self, mem):
        result = mem.forget_fact("nonexistent")
        assert "error" in result

    def test_list_facts_sorted_by_updated(self, mem):
        mem.remember_fact("old", "value1")
        time.sleep(0.01)
        mem.remember_fact("new", "value2")
        facts = mem.list_facts()
        assert facts[0]["key"] == "new"

    def test_list_facts_category_filter(self, mem):
        mem.remember_fact("k1", "v1", category="tech")
        mem.remember_fact("k2", "v2", category="personal")
        tech = mem.list_facts(category="tech")
        assert len(tech) == 1
        assert tech[0]["key"] == "k1"


# ── Preferences ────────────────────────────────────────────────────────────────

class TestPreferences:
    def test_set_and_get_preference(self, mem):
        mem.set_preference("theme", "dark")
        assert mem.get_preference("theme") == "dark"

    def test_get_preference_default(self, mem):
        assert mem.get_preference("nonexistent", default="light") == "light"

    def test_preferences_persist(self, mem, tmp_path):
        mem.set_preference("lang", "en")
        mem2 = KANMemory(storage_dir=str(tmp_path))
        assert mem2.get_preference("lang") == "en"

    def test_get_all_preferences(self, mem):
        mem.set_preference("a", 1)
        mem.set_preference("b", 2)
        prefs = mem.get_all_preferences()
        assert prefs == {"a": 1, "b": 2}

    def test_overwrite_preference(self, mem):
        mem.set_preference("x", "old")
        mem.set_preference("x", "new")
        assert mem.get_preference("x") == "new"


# ── Episodic memory ────────────────────────────────────────────────────────────

class TestEpisodicMemory:
    def test_save_episode(self, mem):
        result = mem.save_episode(
            title="Test task",
            summary="Did something",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert result["saved"] is True
        assert len(mem.episodes) == 1

    def test_episode_keeps_last_5_messages(self, mem):
        msgs = [{"role": "user", "content": f"m{i}"} for i in range(10)]
        mem.save_episode("t", "s", msgs)
        saved = mem.episodes[0]["messages"]
        assert len(saved) == 5
        assert saved[-1]["content"] == "m9"

    def test_episodes_capped_at_100(self, mem):
        for i in range(105):
            mem.save_episode(f"ep{i}", "summary", [])
        assert len(mem.episodes) == 100
        assert mem.episodes[-1]["title"] == "ep104"

    def test_search_episodes_by_title(self, mem):
        mem.save_episode("deploy vikarma", "deployed", [])
        mem.save_episode("fix bug", "fixed", [])
        results = mem.search_episodes("vikarma")
        assert len(results) == 1
        assert results[0]["title"] == "deploy vikarma"

    def test_search_episodes_by_summary(self, mem):
        mem.save_episode("task", "summary with keyword xyz", [])
        results = mem.search_episodes("xyz")
        assert len(results) == 1

    def test_get_recent_episodes(self, mem):
        for i in range(10):
            mem.save_episode(f"ep{i}", "s", [])
        recent = mem.get_recent_episodes(3)
        assert len(recent) == 3
        assert recent[-1]["title"] == "ep9"

    def test_episodes_persist(self, mem, tmp_path):
        mem.save_episode("persisted", "yes", [])
        mem2 = KANMemory(storage_dir=str(tmp_path))
        assert len(mem2.episodes) == 1
        assert mem2.episodes[0]["title"] == "persisted"


# ── Context summary ────────────────────────────────────────────────────────────

class TestContextSummary:
    def test_empty_memory_returns_empty_string(self, mem):
        assert mem.build_context_summary() == ""

    def test_summary_includes_preferences(self, mem):
        mem.set_preference("name", "Alice")
        summary = mem.build_context_summary()
        assert "Alice" in summary

    def test_summary_includes_facts(self, mem):
        mem.remember_fact("project", "vikarma")
        summary = mem.build_context_summary()
        assert "vikarma" in summary

    def test_summary_includes_recent_episodes(self, mem):
        mem.save_episode("my episode title", "summary text", [])
        summary = mem.build_context_summary()
        assert "my episode title" in summary


# ── Stats & export ─────────────────────────────────────────────────────────────

class TestStatsAndExport:
    def test_get_stats(self, mem):
        mem.remember_now("msg")
        mem.remember_fact("k", "v")
        mem.set_preference("p", "q")
        mem.save_episode("ep", "s", [])
        stats = mem.get_stats()
        assert stats["short_term"] == 1
        assert stats["facts"] == 1
        assert stats["preferences"] == 1
        assert stats["episodes"] == 1

    def test_export_all(self, mem):
        mem.remember_fact("x", "y")
        export = mem.export_all()
        assert "facts" in export
        assert "preferences" in export
        assert "episodes" in export
        assert "short_term" in export

    def test_clear_all(self, mem):
        mem.remember_now("msg")
        mem.remember_fact("k", "v")
        mem.set_preference("p", "q")
        mem.save_episode("ep", "s", [])
        result = mem.clear_all()
        assert result["cleared"] is True
        stats = mem.get_stats()
        assert stats["short_term"] == 0
        assert stats["facts"] == 0
        assert stats["preferences"] == 0
        assert stats["episodes"] == 0

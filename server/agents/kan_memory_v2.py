"""
VIKARMA — KAN Memory v2
Hierarchical Knowledge Structure: Epic → Story → Task
Like Jira but sacred — like Mahabharata

The whole Epic = Mahabharata
Chapters = Stories (Parvas)  
Moments = Tasks (memories)
Each piece knows the others — puzzle 🧩

🔱 Om Namah Shivaya — For All Humanity
"""

import json
import os
import time
import hashlib
from pathlib import Path
from typing import Optional, Any
from datetime import datetime


class KANEpic:
    """The full Mahabharata — the overarching story"""
    def __init__(self, epic_id: str, title: str, description: str = "", metadata: dict = None):
        self.epic_id = epic_id
        self.title = title
        self.description = description
        self.metadata = metadata or {}
        self.created = time.time()
        self.updated = time.time()
        self.stories: list[str] = []  # story IDs

    def to_dict(self) -> dict:
        return {
            "epic_id": self.epic_id,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata,
            "created": self.created,
            "updated": self.updated,
            "stories": self.stories,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "KANEpic":
        e = cls(d["epic_id"], d["title"], d.get("description",""), d.get("metadata",{}))
        e.created = d.get("created", time.time())
        e.updated = d.get("updated", time.time())
        e.stories = d.get("stories", [])
        return e


class KANStory:
    """A Parva — a chapter in the Epic"""
    def __init__(self, story_id: str, epic_id: str, title: str, summary: str = "", metadata: dict = None):
        self.story_id = story_id
        self.epic_id = epic_id  # belongs to this epic
        self.title = title
        self.summary = summary
        self.metadata = metadata or {}
        self.created = time.time()
        self.updated = time.time()
        self.tasks: list[str] = []  # task IDs
        self.linked_stories: list[str] = []  # puzzle connections to other stories

    def to_dict(self) -> dict:
        return {
            "story_id": self.story_id,
            "epic_id": self.epic_id,
            "title": self.title,
            "summary": self.summary,
            "metadata": self.metadata,
            "created": self.created,
            "updated": self.updated,
            "tasks": self.tasks,
            "linked_stories": self.linked_stories,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "KANStory":
        s = cls(d["story_id"], d["epic_id"], d["title"], d.get("summary",""), d.get("metadata",{}))
        s.created = d.get("created", time.time())
        s.updated = d.get("updated", time.time())
        s.tasks = d.get("tasks", [])
        s.linked_stories = d.get("linked_stories", [])
        return s


class KANTask:
    """A single memory moment — the atomic unit"""
    def __init__(
        self,
        task_id: str,
        story_id: str,
        epic_id: str,
        content: str,
        role: str = "assistant",
        task_type: str = "memory",
        metadata: dict = None,
    ):
        self.task_id = task_id
        self.story_id = story_id  # belongs to this story
        self.epic_id = epic_id    # belongs to this epic
        self.content = content
        self.role = role
        self.task_type = task_type  # memory, fact, action, insight
        self.metadata = metadata or {}
        self.created = time.time()
        self.linked_tasks: list[str] = []  # puzzle connections

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "story_id": self.story_id,
            "epic_id": self.epic_id,
            "content": self.content,
            "role": self.role,
            "task_type": self.task_type,
            "metadata": self.metadata,
            "created": self.created,
            "linked_tasks": self.linked_tasks,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "KANTask":
        t = cls(
            d["task_id"], d["story_id"], d["epic_id"],
            d["content"], d.get("role","assistant"),
            d.get("task_type","memory"), d.get("metadata",{})
        )
        t.created = d.get("created", time.time())
        t.linked_tasks = d.get("linked_tasks", [])
        return t


class KANMemoryV2:
    """
    Knowledge Augmented Network — Hierarchical Memory
    
    Structure:
    Epic (Mahabharata) 
      → Story (Parva/Chapter)
        → Task (Memory moment)
    
    Each piece knows the others — puzzle connections 🧩
    KAN sees each chapter as its own Epic but also as part of the whole.
    """

    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or os.path.expanduser("~/.vikarma/kan_v2"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.epics_file = self.storage_dir / "epics.json"
        self.stories_file = self.storage_dir / "stories.json"
        self.tasks_file = self.storage_dir / "tasks.json"
        self.prefs_file = self.storage_dir / "preferences.json"
        self.short_term_file = self.storage_dir / "short_term.json"

        # Load all
        self._epics: dict[str, KANEpic] = self._load_epics()
        self._stories: dict[str, KANStory] = self._load_stories()
        self._tasks: dict[str, KANTask] = self._load_tasks()
        self._preferences: dict = self._load_json(self.prefs_file, {})
        self._short_term: list[dict] = self._load_json(self.short_term_file, [])

        # Auto-create default epic if none exists
        if not self._epics:
            self.create_epic("vikarma-main", "NewZyon / PAI-KAN", "The sacred journey of building Vikarma for all humanity")

    # ── ID Generation ──────────────────────────────────────────────────────

    def _make_id(self, prefix: str, text: str) -> str:
        h = hashlib.md5(f"{text}{time.time()}".encode()).hexdigest()[:8]
        return f"{prefix}_{h}"

    # ── EPIC Operations ────────────────────────────────────────────────────

    def create_epic(self, epic_id: str = None, title: str = "", description: str = "", metadata: dict = None) -> KANEpic:
        """Create a new Epic (the whole Mahabharata)"""
        eid = epic_id or self._make_id("epic", title)
        epic = KANEpic(eid, title, description, metadata)
        self._epics[eid] = epic
        self._save_epics()
        return epic

    def get_epic(self, epic_id: str) -> Optional[KANEpic]:
        return self._epics.get(epic_id)

    def list_epics(self) -> list[KANEpic]:
        return sorted(self._epics.values(), key=lambda e: e.updated, reverse=True)

    def get_default_epic_id(self) -> str:
        if self._epics:
            return list(self._epics.keys())[0]
        e = self.create_epic(title="Default")
        return e.epic_id

    # ── STORY Operations ───────────────────────────────────────────────────

    def create_story(self, title: str, epic_id: str = None, summary: str = "", metadata: dict = None) -> KANStory:
        """Create a new Story/Chapter (a Parva)"""
        eid = epic_id or self.get_default_epic_id()
        sid = self._make_id("story", title)
        story = KANStory(sid, eid, title, summary, metadata)
        self._stories[sid] = story

        # Link to epic
        if eid in self._epics:
            self._epics[eid].stories.append(sid)
            self._epics[eid].updated = time.time()
            self._save_epics()

        self._save_stories()
        return story

    def get_story(self, story_id: str) -> Optional[KANStory]:
        return self._stories.get(story_id)

    def link_stories(self, story_id_1: str, story_id_2: str) -> dict:
        """Create puzzle connection between two stories"""
        s1 = self._stories.get(story_id_1)
        s2 = self._stories.get(story_id_2)
        if not s1 or not s2:
            return {"error": "Story not found"}
        if story_id_2 not in s1.linked_stories:
            s1.linked_stories.append(story_id_2)
        if story_id_1 not in s2.linked_stories:
            s2.linked_stories.append(story_id_1)
        self._save_stories()
        return {"linked": True, "stories": [story_id_1, story_id_2]}

    def get_stories_for_epic(self, epic_id: str) -> list[KANStory]:
        return [s for s in self._stories.values() if s.epic_id == epic_id]

    # ── TASK/MEMORY Operations ─────────────────────────────────────────────

    def remember(
        self,
        content: str,
        role: str = "user",
        story_id: str = None,
        epic_id: str = None,
        task_type: str = "memory",
        metadata: dict = None,
        auto_story: bool = True,
    ) -> KANTask:
        """
        Store a memory moment as a Task.
        Auto-creates story if needed.
        """
        eid = epic_id or self.get_default_epic_id()

        # Auto-create story if none provided
        if not story_id and auto_story:
            today = datetime.now().strftime("%Y-%m-%d")
            existing = [s for s in self._stories.values() if s.epic_id == eid and today in s.title]
            if existing:
                sid = existing[0].story_id
            else:
                story = self.create_story(f"Session {today}", eid, f"Auto-created session for {today}")
                sid = story.story_id
        else:
            sid = story_id or "default"

        tid = self._make_id("task", content[:20])
        task = KANTask(tid, sid, eid, content, role, task_type, metadata)
        self._tasks[tid] = task

        # Link to story
        if sid in self._stories:
            self._stories[sid].tasks.append(tid)
            self._stories[sid].updated = time.time()
            self._save_stories()

        # Also add to short-term
        self._short_term.append({"content": content, "role": role, "task_id": tid, "timestamp": time.time()})
        if len(self._short_term) > 50:
            self._short_term = self._short_term[-50:]

        self._save_tasks()
        self._save_json(self.short_term_file, self._short_term)
        return task

    def recall(self, query: str, limit: int = 10) -> list[KANTask]:
        """Search across all tasks"""
        q = query.lower()
        results = []
        for task in self._tasks.values():
            if q in task.content.lower() or q in str(task.metadata).lower():
                results.append(task)
        return sorted(results, key=lambda t: t.created, reverse=True)[:limit]

    def get_tasks_for_story(self, story_id: str) -> list[KANTask]:
        return [t for t in self._tasks.values() if t.story_id == story_id]

    def link_tasks(self, task_id_1: str, task_id_2: str) -> dict:
        """Puzzle connection between tasks"""
        t1 = self._tasks.get(task_id_1)
        t2 = self._tasks.get(task_id_2)
        if not t1 or not t2:
            return {"error": "Task not found"}
        if task_id_2 not in t1.linked_tasks:
            t1.linked_tasks.append(task_id_2)
        if task_id_1 not in t2.linked_tasks:
            t2.linked_tasks.append(task_id_1)
        self._save_tasks()
        return {"linked": True, "tasks": [task_id_1, task_id_2]}

    # ── Short-term ─────────────────────────────────────────────────────────

    def get_recent(self, n: int = 10) -> list[dict]:
        return self._short_term[-n:]

    def get_context_window(self, n: int = 20) -> list[dict]:
        return [{"role": m["role"], "content": m["content"]} for m in self._short_term[-n:]]

    # ── Preferences ────────────────────────────────────────────────────────

    def set_preference(self, key: str, value: Any) -> dict:
        self._preferences[key] = {"value": value, "updated": time.time()}
        self._save_json(self.prefs_file, self._preferences)
        return {"stored": True, "key": key}

    def get_preference(self, key: str, default: Any = None) -> Any:
        p = self._preferences.get(key)
        return p["value"] if p else default

    # ── Context Summary for AI ─────────────────────────────────────────────

    def build_context_summary(self, epic_id: str = None) -> str:
        """Build hierarchical memory context for AI injection"""
        eid = epic_id or self.get_default_epic_id()
        epic = self._epics.get(eid)
        if not epic:
            return ""

        lines = [f"🧠 KAN Memory — Epic: {epic.title}"]

        # Preferences
        prefs = {k: v["value"] for k, v in self._preferences.items()}
        if prefs:
            lines.append(f"\n📌 Preferences: {', '.join(f'{k}={v}' for k,v in list(prefs.items())[:3])}")

        # Recent stories
        stories = sorted(self.get_stories_for_epic(eid), key=lambda s: s.updated, reverse=True)[:3]
        if stories:
            lines.append(f"\n📚 Recent Chapters ({len(self.get_stories_for_epic(eid))} total):")
            for story in stories:
                tasks = self.get_tasks_for_story(story.story_id)
                lines.append(f"  📖 {story.title} ({len(tasks)} memories)")
                if story.linked_stories:
                    linked = [self._stories[s].title for s in story.linked_stories[:2] if s in self._stories]
                    if linked:
                        lines.append(f"     🧩 Linked to: {', '.join(linked)}")

        # Recent tasks
        recent_tasks = sorted(self._tasks.values(), key=lambda t: t.created, reverse=True)[:5]
        if recent_tasks:
            lines.append(f"\n💭 Recent Memories:")
            for t in recent_tasks:
                lines.append(f"  • [{t.role}] {t.content[:80]}...")

        return "\n".join(lines)

    def get_epic_overview(self, epic_id: str = None) -> dict:
        """Full overview of an epic and all its stories/tasks"""
        eid = epic_id or self.get_default_epic_id()
        epic = self._epics.get(eid)
        if not epic:
            return {"error": "Epic not found"}

        stories = self.get_stories_for_epic(eid)
        overview = {
            "epic": epic.to_dict(),
            "stories": [],
            "total_memories": 0,
        }

        for story in stories:
            tasks = self.get_tasks_for_story(story.story_id)
            overview["stories"].append({
                "story": story.to_dict(),
                "task_count": len(tasks),
                "recent_tasks": [t.to_dict() for t in sorted(tasks, key=lambda x: x.created, reverse=True)[:3]],
            })
            overview["total_memories"] += len(tasks)

        return overview

    def get_stats(self) -> dict:
        return {
            "epics": len(self._epics),
            "stories": len(self._stories),
            "tasks": len(self._tasks),
            "short_term": len(self._short_term),
            "preferences": len(self._preferences),
            "storage": str(self.storage_dir),
        }

    # ── Persistence ────────────────────────────────────────────────────────

    def _load_epics(self) -> dict:
        data = self._load_json(self.epics_file, {})
        return {k: KANEpic.from_dict(v) for k, v in data.items()}

    def _load_stories(self) -> dict:
        data = self._load_json(self.stories_file, {})
        return {k: KANStory.from_dict(v) for k, v in data.items()}

    def _load_tasks(self) -> dict:
        data = self._load_json(self.tasks_file, {})
        return {k: KANTask.from_dict(v) for k, v in data.items()}

    def _save_epics(self):
        self._save_json(self.epics_file, {k: v.to_dict() for k, v in self._epics.items()})

    def _save_stories(self):
        self._save_json(self.stories_file, {k: v.to_dict() for k, v in self._stories.items()})

    def _save_tasks(self):
        self._save_json(self.tasks_file, {k: v.to_dict() for k, v in self._tasks.items()})

    def _load_json(self, path: Path, default: Any) -> Any:
        try:
            if path.exists():
                return json.loads(path.read_text())
            return default
        except:
            return default

    def _save_json(self, path: Path, data: Any):
        try:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except:
            pass

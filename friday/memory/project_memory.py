import json, logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
logger = logging.getLogger("friday.project_memory")
class ProjectMemory:
    _instance = None
    def __new__(cls):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self):
        if hasattr(self, "_projects"): return
        self._projects: dict[str, dict] = {}
    def create_project(self, name: str, description: str = "") -> str:
        pid = str(uuid4()); now = datetime.now(timezone.utc).isoformat()
        self._projects[pid] = {"id": pid, "name": name, "description": description, "created_at": now, "updated_at": now, "files": [], "tags": []}
        return pid
    def get_project(self, pid: str): return self._projects.get(pid)
    def find_by_name(self, name: str):
        nl = name.lower()
        for p in self._projects.values():
            if p["name"].lower() == nl: return p
        return None
    def list_projects(self): return list(self._projects.values())
    def update_project(self, pid: str, updates: dict) -> bool:
        p = self._projects.get(pid)
        if p is None: return False
        updates["updated_at"] = datetime.now(timezone.utc).isoformat(); p.update(updates); return True
    def delete_project(self, pid: str) -> bool:
        if pid in self._projects: del self._projects[pid]; return True
        return False
    def save(self, path):
        p = Path(path) if isinstance(path, str) else path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(self._projects, indent=2))
    def load(self, path):
        p = Path(path) if isinstance(path, str) else path
        if p.exists(): self._projects = json.loads(p.read_text())

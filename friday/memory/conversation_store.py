import json, logging
from datetime import datetime, timezone
from typing import Any
logger = logging.getLogger("friday.conversation_store")
class ConversationStore:
    def __init__(self, db_path: str = "data/conversations.db"):
        self.db_path = db_path; self._conn: Any = None
    async def _ensure_db(self):
        if self._conn is not None: return
        import aiosqlite
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL, content TEXT NOT NULL, metadata TEXT DEFAULT '{}', created_at TEXT NOT NULL)")
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)")
        await self._conn.commit()
    async def add_message(self, role: str, content: str, metadata: dict | None = None) -> int:
        await self._ensure_db()
        now = datetime.now(timezone.utc).isoformat()
        c = await self._conn.execute("INSERT INTO messages (role, content, metadata, created_at) VALUES (?, ?, ?, ?)", [role, content, json.dumps(metadata or {}), now])
        await self._conn.commit(); return c.lastrowid or 0
    async def get_history(self, limit: int = 50) -> list[dict]:
        await self._ensure_db()
        c = await self._conn.execute("SELECT * FROM messages ORDER BY created_at DESC LIMIT ?", [limit])
        rows = await c.fetchall()
        return [{"id": r["id"], "role": r["role"], "content": r["content"], "metadata": json.loads(r["metadata"]), "created_at": r["created_at"]} for r in reversed(rows)]
    async def search(self, query: str) -> list[dict]:
        await self._ensure_db()
        c = await self._conn.execute("SELECT * FROM messages WHERE content LIKE ? ORDER BY created_at DESC LIMIT 20", [f"%{query}%"])
        return [{"id": r["id"], "role": r["role"], "content": r["content"], "metadata": json.loads(r["metadata"]), "created_at": r["created_at"]} for r in await c.fetchall()]
    async def clear(self):
        await self._ensure_db(); await self._conn.execute("DELETE FROM messages"); await self._conn.commit()
    async def close(self):
        if self._conn: await self._conn.close(); self._conn = None

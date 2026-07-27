import json
import pytest
from unittest.mock import AsyncMock, patch
from friday.memory.knowledge_graph import KnowledgeGraph
from friday.memory.user_profile import UserProfile
from friday.memory.project_memory import ProjectMemory
from friday.memory.entity_extractor import EntityExtractor
from friday.memory.conversation_store import ConversationStore
from friday.memory.semantic_store import SemanticStore
from friday.memory.embedding_service import EmbeddingService


# --- KnowledgeGraph ---

@pytest.fixture(autouse=True)
def reset_singletons():
    KnowledgeGraph._instance = None
    UserProfile._instance = None
    ProjectMemory._instance = None
    yield


class TestKnowledgeGraph:
    def test_add_and_query_entity(self):
        kg = KnowledgeGraph()
        kg.add_entity("py", "language", {"name": "Python"})
        assert kg.query_entity("py") == {"id": "py", "type": "language", "properties": {"name": "Python"}}

    def test_add_relation(self):
        kg = KnowledgeGraph()
        kg.add_entity("a", "thing")
        kg.add_entity("b", "thing")
        kg.add_relation("a", "b", "connects_to")
        rels = kg.get_relations()
        assert len(rels) == 1
        assert rels[0] == {"source": "a", "target": "b", "relation": "connects_to"}

    def test_search(self):
        kg = KnowledgeGraph()
        kg.add_entity("python", "language", {"name": "Python"})
        kg.add_entity("java", "language", {"name": "Java"})
        results = kg.search("python")
        assert len(results) == 1
        assert results[0]["id"] == "python"

    def test_save_load(self, tmp_path):
        kg = KnowledgeGraph()
        kg.add_entity("x", "test", {"val": 1})
        path = tmp_path / "kg.json"
        kg.save(str(path))
        kg2 = KnowledgeGraph()
        kg2.load(str(path))
        assert kg2.query_entity("x") is not None

    def test_singleton(self):
        assert KnowledgeGraph() is KnowledgeGraph()


# --- UserProfile ---

class TestUserProfile:
    def test_default_profile(self):
        p = UserProfile()
        prof = p.get_profile()
        assert prof["name"] == "Architect"
        assert prof["title"] == "sir"

    def test_update_profile(self):
        p = UserProfile()
        p.update_profile({"name": "TestUser"})
        assert p.get_profile()["name"] == "TestUser"

    def test_save_load(self, tmp_path):
        p = UserProfile()
        p.update_profile({"name": "SavedUser"})
        path = tmp_path / "profile.json"
        p.save(str(path))
        p2 = UserProfile()
        p2.load(str(path))
        assert p2.get_profile()["name"] == "SavedUser"

    def test_nested_dict_update(self):
        p = UserProfile()
        p.update_profile({"coding_style": {"language_preference": "rust", "line_length": 100}})
        prof = p.get_profile()
        assert prof["coding_style"]["language_preference"] == "rust"
        assert prof["coding_style"]["line_length"] == 100
        assert prof["coding_style"]["indent_style"] == "spaces"

    def test_writing_style_default(self):
        p = UserProfile()
        prof = p.get_profile()
        assert "writing_style" in prof
        assert prof["writing_style"]["tone"] == "technical"
        assert prof["writing_style"]["citation_format"] == "APA"

    def test_new_keys_added(self):
        p = UserProfile()
        p.update_profile({"custom_key": "custom_value"})
        assert p.get_profile()["custom_key"] == "custom_value"

    def test_load_nonexistent(self):
        p = UserProfile()
        from pathlib import Path
        p.load(Path("/nonexistent/path.json"))
        assert p.get_profile()["name"] == "Architect"

    def test_singleton(self):
        assert UserProfile() is UserProfile()


# --- ProjectMemory ---

class TestProjectMemory:
    def test_create_project(self):
        pm = ProjectMemory()
        pid = pm.create_project("Test", "A test project")
        proj = pm.get_project(pid)
        assert proj["name"] == "Test"
        assert proj["description"] == "A test project"

    def test_find_by_name(self):
        pm = ProjectMemory()
        pm.create_project("UniqueName")
        assert pm.find_by_name("UniqueName") is not None
        assert pm.find_by_name("nonexistent") is None

    def test_delete_project(self):
        pm = ProjectMemory()
        pid = pm.create_project("ToDelete")
        assert pm.delete_project(pid) is True
        assert pm.get_project(pid) is None
        assert pm.delete_project("fake") is False

    def test_save_load(self, tmp_path):
        pm = ProjectMemory()
        pm.create_project("SaveTest")
        path = tmp_path / "projects.json"
        pm.save(str(path))
        pm2 = ProjectMemory()
        pm2.load(str(path))
        assert len(pm2.list_projects()) == 1

    def test_update_project(self):
        pm = ProjectMemory()
        pid = pm.create_project("UpdateTest")
        assert pm.update_project(pid, {"description": "Updated desc"}) is True
        assert pm.get_project(pid)["description"] == "Updated desc"
        assert pm.update_project("fake", {}) is False

    def test_list_projects_returns_all(self):
        pm = ProjectMemory()
        pm.create_project("A")
        pm.create_project("B")
        assert len(pm.list_projects()) == 2

    def test_singleton(self):
        assert ProjectMemory() is ProjectMemory()


# --- EntityExtractor ---

class TestEntityExtractor:
    def test_extract_regex(self):
        ee = EntityExtractor()
        results = ee.extract_regex("I love Python and Docker on Arch Linux")
        types = {r["type"] for r in results}
        assert "technology" in types
        assert "platform" in types


# --- ConversationStore ---

@pytest.mark.asyncio
class TestConversationStore:
    async def test_add_and_history(self, tmp_path):
        db = tmp_path / "conv.db"
        cs = ConversationStore(db_path=str(db))
        await cs.add_message("user", "hello")
        await cs.add_message("assistant", "hi there")
        history = await cs.get_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "hello"

    async def test_search(self, tmp_path):
        db = tmp_path / "conv2.db"
        cs = ConversationStore(db_path=str(db))
        await cs.add_message("user", "search term here")
        await cs.add_message("assistant", "other stuff")
        results = await cs.search("search")
        assert len(results) == 1

    async def test_clear(self, tmp_path):
        db = tmp_path / "conv3.db"
        cs = ConversationStore(db_path=str(db))
        await cs.add_message("user", "x")
        await cs.clear()
        assert len(await cs.get_history()) == 0


# --- SemanticStore (integration with mock embedding) ---

@pytest.mark.asyncio
class TestSemanticStore:
    async def test_add_and_search(self):
        ss = SemanticStore()
        with patch.object(ss, "_emb") as mock_emb:
            mock_emb.embed = AsyncMock(side_effect=lambda t: {
                "hello world": [1.0, 0.0],
                "goodbye world": [0.0, 1.0],
                "hello there": [1.0, 0.1],
            }.get(t, []))
            await ss.add_entry("1", "hello world")
            await ss.add_entry("2", "goodbye world")
            results = await ss.search("hello world")
            assert len(results) >= 1
            assert results[0]["id"] == "1"

    async def test_empty_store_returns_empty(self):
        ss = SemanticStore()
        assert await ss.count() == 0
        results = await ss.search("anything")
        assert results == []


# --- EmbeddingService ---

@pytest.mark.asyncio
class TestEmbeddingService:
    async def test_is_available_false_when_offline(self):
        emb = EmbeddingService(base_url="http://127.0.0.1:19999")
        assert await emb.is_available() is False

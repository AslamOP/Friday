import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from friday.memory.vector_store import VectorStore
from friday.memory.semantic_store import SemanticStore


@pytest.fixture(autouse=True)
def reset_vector_store():
    VectorStore._instance = None
    yield
    VectorStore._instance = None


@pytest.mark.asyncio
async def test_vector_store_add_and_search():
    vs = VectorStore()
    vs._store = AsyncMock(spec=SemanticStore)
    vs._embeddings = AsyncMock()
    vs._embeddings.is_available = AsyncMock(return_value=True)

    await vs.add_entry("1", "hello world", {"source": "test"})
    vs._store.add_entry.assert_called_once_with("1", "hello world", {"source": "test"})

    vs._store.search.return_value = [
        {"id": "1", "text": "hello world", "score": 0.9, "metadata": {"source": "test"}}
    ]
    results = await vs.search("hello")
    assert len(results) == 1
    assert results[0]["id"] == "1"

    vs._store.count.return_value = 1
    assert await vs.count() == 1


@pytest.mark.asyncio
async def test_vector_store_embeddings_unavailable():
    vs = VectorStore()
    vs._embeddings = AsyncMock()
    vs._embeddings.is_available = AsyncMock(return_value=False)
    results = await vs.search("anything")
    assert results == []


@pytest.mark.asyncio
async def test_vector_store_singleton():
    a = VectorStore()
    b = VectorStore()
    assert a is b

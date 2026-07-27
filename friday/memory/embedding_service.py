import asyncio
import logging
import httpx
logger = logging.getLogger("friday.embedding_service")
_DEFAULT_MODEL = "nomic-embed-text"; _DEFAULT_URL = "http://127.0.0.1:11434"
class EmbeddingService:
    def __init__(self, model: str = _DEFAULT_MODEL, base_url: str = _DEFAULT_URL):
        self.model = model; self.base_url = base_url.rstrip("/"); self._client: httpx.AsyncClient | None = None
    async def _get_client(self):
        if self._client is None: self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    async def embed(self, text: str) -> list[float]:
        client = await self._get_client()
        try:
            r = await client.post(f"{self.base_url}/api/embeddings", json={"model": self.model, "prompt": text}); r.raise_for_status()
            return r.json().get("embedding", [])
        except Exception as e: logger.warning("Embed failed: %s", e); return []
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = await asyncio.gather(*[self.embed(t) for t in texts], return_exceptions=True)
        out = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning("Batch embed failed: %s", r)
                out.append([])
            else:
                out.append(r)
        return out
    async def is_available(self) -> bool:
        try:
            r = await (await self._get_client()).get(f"{self.base_url}/api/tags"); return r.status_code == 200
        except Exception: return False
    async def close(self):
        if self._client: await self._client.aclose(); self._client = None

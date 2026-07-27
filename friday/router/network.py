import asyncio, logging
logger = logging.getLogger("friday.network")
async def is_online(host: str = "8.8.8.8", port: int = 53, timeout: float = 2.0) -> bool:
    try:
        _, w = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
        w.close(); await w.wait_closed(); return True
    except: return False
async def check_openrouter(api_key: str, timeout: float = 3.0) -> bool:
    if not api_key: return False
    try:
        import httpx
        r = await httpx.AsyncClient(timeout=timeout).get("https://openrouter.ai/api/v1/auth/key", headers={"Authorization": f"Bearer {api_key}"})
        return r.status_code == 200
    except: return False

async def check_zen(api_key: str, timeout: float = 3.0) -> bool:
    if not api_key: return False
    try:
        import httpx
        r = await httpx.AsyncClient(timeout=timeout).get("https://opencode.ai/zen/v1/models", headers={"Authorization": f"Bearer {api_key}"})
        return r.status_code == 200
    except: return False

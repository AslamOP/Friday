import pytest
from friday.router.provider_registry import ProviderRegistry, ProviderConfig


@pytest.fixture(autouse=True)
def reset():
    ProviderRegistry._instance = None
    yield
    ProviderRegistry._instance = None


class TestProviderConfig:
    def test_default_provider_config(self):
        p = ProviderConfig(name="test", type="cloud")
        assert p.name == "test"
        assert p.type == "cloud"
        assert p.priority == 10
        assert p.enabled is True


class TestProviderRegistry:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        ProviderRegistry._instance = None
        self._path = tmp_path / "providers.json"
        self.reg = ProviderRegistry(path=str(self._path))

    def test_default_providers_loaded(self):
        providers = self.reg.list_providers()
        names = [p.name for p in providers]
        for n in ("zen", "openrouter", "openai", "anthropic", "google", "github-copilot", "ollama"):
            assert n in names

    @pytest.mark.asyncio
    async def test_add_provider(self):
        await self.reg.add_provider("custom", "cloud", endpoint="https://api.example.com",
                                    models=["gpt-4"], priority=5)
        p = self.reg.get_provider("custom")
        assert p is not None
        assert p.endpoint == "https://api.example.com"
        assert p.models == ["gpt-4"]

    @pytest.mark.asyncio
    async def test_remove_provider(self):
        await self.reg.add_provider("test-provider", "local")
        assert self.reg.get_provider("test-provider") is not None
        assert await self.reg.remove_provider("test-provider") is True
        assert self.reg.get_provider("test-provider") is None

    @pytest.mark.asyncio
    async def test_cannot_remove_defaults(self):
        for name in ("zen", "openrouter", "openai", "anthropic", "google", "github-copilot", "ollama"):
            assert await self.reg.remove_provider(name) is False

    @pytest.mark.asyncio
    async def test_set_key(self):
        await self.reg.set_key("zen", "sk-test")
        assert self.reg.get_provider("zen").api_key == "sk-test"

    @pytest.mark.asyncio
    async def test_set_enabled(self):
        await self.reg.set_enabled("ollama", False)
        assert self.reg.get_provider("ollama").enabled is False

    def test_get_online_providers_empty_initially(self):
        online = self.reg.get_online_providers()
        assert online == []

    @pytest.mark.asyncio
    async def test_persistence(self):
        await self.reg.add_provider("persist-test", "local")
        ProviderRegistry._instance = None
        reg2 = ProviderRegistry(path=str(self._path))
        assert reg2.get_provider("persist-test") is not None

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        await self.reg.add_provider("low-pri", "local", priority=100)
        await self.reg.add_provider("high-pri", "local", priority=1)
        providers = self.reg.list_providers()
        idx_high = next(i for i, p in enumerate(providers) if p.name == "high-pri")
        idx_low = next(i for i, p in enumerate(providers) if p.name == "low-pri")
        assert idx_high < idx_low

    @pytest.mark.asyncio
    async def test_check_status_local_offline(self):
        await self.reg.add_provider("fake-local", "local", endpoint="http://127.0.0.1:19999")
        status = await self.reg.check_status("fake-local")
        assert status == "offline"

    @pytest.mark.asyncio
    async def test_check_status_cloud_no_key(self):
        status = await self.reg.check_status("zen")
        assert status in ("online", "offline")

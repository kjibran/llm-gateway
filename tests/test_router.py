import pytest

from llm_gateway.providers import Provider, ProviderError
from llm_gateway.router import AllProvidersFailed, Router

MESSAGES = [{"role": "user", "content": "hi"}]


class FakeProvider(Provider):
    """Behaves like a provider but never touches the network."""

    def __init__(self, name, fail=False):
        super().__init__(
            name=name, base_url="http://fake", api_key="key", model="model"
        )
        self.fail = fail
        self.calls = 0

    async def chat(self, messages, timeout):
        self.calls += 1
        if self.fail:
            raise ProviderError(f"{self.name}: simulated failure")
        return {"choices": [{"message": {"content": f"answer from {self.name}"}}]}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_first_provider_answers_and_others_are_not_called():
    a, b = FakeProvider("a"), FakeProvider("b")
    result = await Router([a, b], timeout=1).chat(MESSAGES)
    assert result.provider == "a"
    assert b.calls == 0


@pytest.mark.anyio
async def test_falls_back_when_first_provider_fails():
    a, b = FakeProvider("a", fail=True), FakeProvider("b")
    result = await Router([a, b], timeout=1).chat(MESSAGES)
    assert result.provider == "b"
    assert len(result.attempts) == 2
    assert result.attempts[0].ok is False
    assert "simulated failure" in result.attempts[0].error


@pytest.mark.anyio
async def test_raises_with_all_attempts_when_every_provider_fails():
    providers = [FakeProvider("a", fail=True), FakeProvider("b", fail=True)]
    with pytest.raises(AllProvidersFailed) as exc_info:
        await Router(providers, timeout=1).chat(MESSAGES)
    assert [a.provider for a in exc_info.value.attempts] == ["a", "b"]


def test_providers_without_key_are_skipped():
    configured = FakeProvider("a")
    missing_key = Provider(name="b", base_url="http://fake", api_key="", model="model")
    router = Router([configured, missing_key], timeout=1)
    assert [p.name for p in router.providers] == ["a"]

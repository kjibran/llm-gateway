import logging
import time
from dataclasses import dataclass, field

from llm_gateway.providers import Provider, ProviderError

logger = logging.getLogger(__name__)


@dataclass
class Attempt:
    provider: str
    ok: bool
    latency_ms: float
    error: str | None = None


@dataclass
class RouterResult:
    provider: str
    response: dict
    attempts: list[Attempt] = field(default_factory=list)


class AllProvidersFailed(Exception):
    def __init__(self, attempts: list[Attempt]):
        super().__init__("All providers failed")
        self.attempts = attempts


class Router:
    def __init__(self, providers: list[Provider], timeout: float):
        # Skip providers without a key or model, so a missing key never crashes the gateway
        self.providers = [p for p in providers if p.api_key and p.model]
        self.timeout = timeout

    async def chat(self, messages: list[dict]) -> RouterResult:
        attempts: list[Attempt] = []
        for provider in self.providers:
            start = time.perf_counter()
            try:
                response = await provider.chat(messages, timeout=self.timeout)
            except ProviderError as exc:
                latency = (time.perf_counter() - start) * 1000
                attempts.append(Attempt(provider.name, False, latency, str(exc)))
                logger.warning("Provider failed, falling back: %s", exc)
                continue
            latency = (time.perf_counter() - start) * 1000
            attempts.append(Attempt(provider.name, True, latency))
            logger.info("Answered by %s in %.0f ms", provider.name, latency)
            return RouterResult(provider.name, response, attempts)
        raise AllProvidersFailed(attempts)

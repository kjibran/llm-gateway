from dataclasses import dataclass

import httpx


class ProviderError(Exception):
    """A provider failure that should trigger fallback to the next provider."""


@dataclass
class Provider:
    name: str
    base_url: str
    api_key: str
    model: str

    async def chat(self, messages: list[dict], timeout: float) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": messages}
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
        
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"{self.name}: {type(exc).__name__}: {exc}"
            ) from exc

        if response.status_code != 200:
            raise ProviderError(
                f"{self.name}: HTTP {response.status_code}: {response.text[:200]}"
            )
        return response.json()
    

def build_providers(settings) -> list[Provider]:
    """All configured providers, in fallback order."""
    return [
        Provider(
            name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        ),
        Provider(
            name="gemini",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        ),
        Provider(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        ),
    ]
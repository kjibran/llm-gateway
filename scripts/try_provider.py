import asyncio

from llm_gateway.config import settings
from llm_gateway.providers import ProviderError, build_providers


async def main():
    messages = [{"role": "user", "content": "Say hello in one short sentence."}]
    for provider in build_providers(settings):
        try:
            result = await provider.chat(messages, timeout=settings.request_timeout)
            print(f"OK     {provider.name}: {result['choices'][0]['message']['content']}")
        except ProviderError as exc:
            print(f"FAILED {exc}")


asyncio.run(main())
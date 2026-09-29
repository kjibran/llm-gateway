import logging
from dataclasses import asdict

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from llm_gateway.config import settings
from llm_gateway.providers import build_providers
from llm_gateway.router import AllProvidersFailed, Router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="LLM Gateway")
gateway = Router(build_providers(settings), timeout=settings.request_timeout)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None  # accepted for OpenAI compatibility, the router decides


@app.get("/health")
def health():
    return {"status": "ok", "providers": [p.name for p in gateway.providers]}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, response: Response):
    messages = [m.model_dump() for m in request.messages]
    try:
        result = await gateway.chat(messages)
    except AllProvidersFailed as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "all providers failed",
                "attempts": [asdict(a) for a in exc.attempts],
            },
        )
    response.headers["X-Gateway-Provider"] = result.provider
    response.headers["X-Gateway-Attempts"] = str(len(result.attempts))
    return result.response
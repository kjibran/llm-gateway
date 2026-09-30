import logging
from dataclasses import asdict

from fastapi.responses import RedirectResponse
from fastapi import Depends, FastAPI, Header, HTTPException, Response
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


def require_api_key(authorization: str | None = Header(default=None)):
    """Protect the gateway when GATEWAY_API_KEY is set. Open when unset, for local dev."""
    expected = settings.gateway_api_key
    if expected and authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="invalid or missing API key")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
def health():
    return {"status": "ok", "providers": [p.name for p in gateway.providers]}


@app.post("/v1/chat/completions", dependencies=[Depends(require_api_key)])
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

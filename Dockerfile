FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 7860
CMD ["sh", "-c", "uvicorn llm_gateway.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /workspace

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/
COPY api/pyproject.toml api/uv.lock ./api/
COPY db/pyproject.toml ./db/
COPY db/src ./db/src
RUN cd api && uv sync --frozen --no-install-project --dev

COPY api ./api
COPY db ./db
RUN cd api && uv sync --frozen --dev

WORKDIR /workspace/api

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "platewise_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

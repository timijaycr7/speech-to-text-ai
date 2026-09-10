FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.12 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-install-project

COPY . .

RUN uv sync --locked --no-dev

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "speech.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
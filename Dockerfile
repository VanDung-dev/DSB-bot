FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv export --frozen --no-dev --no-emit-project > /tmp/requirements.txt && \
    uv pip install --system -r /tmp/requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

CMD ["python", "main.py"]

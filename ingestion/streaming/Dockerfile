FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml uv.lock .python-version .
RUN pip install uv && uv sync --frozen

COPY src ./src

CMD ["uv", "run", "python", "src/event_consumer.py"]

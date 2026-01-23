FROM python:3.11-slim
WORKDIR /app

COPY pyproject.toml uv.lock .python-version .
RUN pip install uv && uv sync --frozen

COPY src ./src
COPY checkpoint.txt .
COPY credit_card_transactions_events.csv .

CMD ["uv", "run", "python", "src/generate.py"]

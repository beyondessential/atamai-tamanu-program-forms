# Stage 1: Generate BAML Python bindings (requires Node)
FROM node:20-slim AS baml-generator
WORKDIR /app
COPY baml_src/ ./baml_src/
RUN npx --yes @boundaryml/baml@0.216.0 generate

# Stage 2: Python runtime
FROM python:3.11-slim
WORKDIR /app

COPY --from=baml-generator /app/baml_client ./baml_client
COPY pyproject.toml .
COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 8080
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]

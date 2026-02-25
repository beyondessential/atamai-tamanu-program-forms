# Atamai — Tamanu Program Form Builder

A conversational AI tool that helps Tamanu implementers build program form XLSX files
for import via Tamanu's program importer.

## What it does

Chat with the assistant to describe a survey. It asks clarifying questions, then generates
a downloadable XLSX file in the exact format expected by Tamanu's program importer.

## Running locally

```bash
uv sync
npx @boundaryml/baml@0.216.0 generate
cp .env.example .env   # add your ANTHROPIC_API_KEY
streamlit run app.py
```

## Docker

```bash
docker compose up --build
```

App runs at http://localhost:8080

## Switching LLM provider

Edit `baml_src/clients.baml` and set the corresponding API key in `.env`.
No Python changes required.

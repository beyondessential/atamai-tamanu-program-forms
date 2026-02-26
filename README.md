# Atamai — Tamanu Program & Registry Builder

A conversational AI tool that helps Tamanu implementers build program form and registry
XLSX files for import via Tamanu's program importer.

## What it does

Chat with the assistant to describe your program form. It asks clarifying questions, then
generates a downloadable XLSX file in the exact format expected by Tamanu's program importer.

Supports the full program structure:
- **Surveys** — programs, vitals, referrals, charts
- **Patient registry** — clinical statuses, tracked conditions, condition categories

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

## Kubernetes

The image is built and pushed to `ghcr.io/beyondessential/atamai-tamanu-program-forms` automatically by GitHub Actions on every push to `main`.

To deploy manually:

```bash
# 1. Create the secret from your .env file (first time only)
kubectl create secret generic app-secrets \
  --from-env-file=.env \
  -n tinker

# 2. Apply the manifest
kubectl apply -f atamai-tamanu-program-forms.yaml
```

The app will be available inside the cluster at `http://atamai-tamanu-program-forms.tinker.svc.cluster.local`.

To access it locally, use port-forward:

```bash
kubectl port-forward svc/atamai-tamanu-program-forms 8080:80 -n tinker
```

Then open http://localhost:8080.

## Switching LLM provider

Edit `baml_src/clients.baml` and set the corresponding API key in `.env`.
No Python changes required.

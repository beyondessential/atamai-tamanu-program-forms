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

```bash
# 1. Build the image
docker build -t atamai-tamanu-program-forms:latest .

# 2. Create the secret from your .env file
kubectl create secret generic app-secrets \
  --from-env-file=.env \
  -n atamai-tamanu-program-forms

# 3. Apply the manifest
kubectl apply -f k8s.yaml
```

The app will be available inside the cluster at `http://atamai-tamanu-program-forms.atamai-tamanu-program-forms.svc.cluster.local`.

To expose it externally, either change the `Service` type to `LoadBalancer` in [k8s.yaml](k8s.yaml),
or add an `Ingress` resource pointing at the service on port 80.

## Switching LLM provider

Edit `baml_src/clients.baml` and set the corresponding API key in `.env`.
No Python changes required.

# Atamai — Tamanu Assistant

A conversational AI assistant for Tamanu implementers. Describe what you need and Atamai
figures out which tool to use — no manual switching required.

Three skills are available:

- **Program Builder** — create, modify, and export Tamanu program form XLSX files. Supports all
  survey types, all question types, patient registries, conditional logic, and calculated questions.
  Upload an existing XLSX to modify it, a PDF spec, or a photo of a paper form.
- **Lab Builder** — build lab test reference data XLSXs (categories, tests, panels) compatible
  with Tamanu's reference data importer.
- **Questions** — ask anything about Tamanu; searches the codebase for accurate answers.

Use slash commands to switch directly (`/program`, `/lab`, `/q`), or just type naturally.

## Running locally

```bash
uv sync
uv run baml-cli generate
cp .env.example .env   # add your ANTHROPIC_API_KEY
uv run streamlit run app.py
```

App runs at http://localhost:8501

## Docker

```bash
docker compose up --build
```

App runs at http://localhost:8080

## Kubernetes

The image is built and pushed to `ghcr.io/beyondessential/atamai-tamanu-program-forms`
automatically by GitHub Actions on every push to `main`.

To deploy manually:

```bash
# 1. Create a GitHub PAT with read:packages scope, then create the image pull secret (first time only)
kubectl create secret docker-registry ghcr-credentials \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_PAT \
  -n tinker

# 2. Create the app secret from your .env file (first time only)
kubectl create secret generic app-secrets \
  --from-env-file=.env \
  -n tinker

# 3. Apply the manifest
kubectl apply -f atamai-tamanu-program-forms.yaml
```

The app is available on the Tailscale network at `http://tinker-atamai-tamanu-program-forms`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | Anthropic API key — powers all three skills |
| `RAG_MCP_URL` | No | URL of a shared github-repo-rag MCP server (Questions skill, HTTP mode) |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | No | Path to a service account key file for MCP server auth |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | No | Service account JSON as a string (alternative to the file) |

## Questions skill — RAG configuration

The Questions skill searches the Tamanu codebase to answer questions accurately. It connects to
a `github-repo-rag` MCP server in one of two ways:

**HTTP mode (shared server)** — set `RAG_MCP_URL` to point to a running MCP server instance,
and configure `GOOGLE_SERVICE_ACCOUNT_FILE` or `GOOGLE_SERVICE_ACCOUNT_JSON` for authentication.

**stdio mode (local)** — leave `RAG_MCP_URL` unset. The skill spawns the MCP server as a
subprocess. The `github-repo-rag` repo must be checked out as a sibling directory:

```
parent/
  atamai-tamanu-program-forms-builder/   ← this repo
  github-repo-rag/                       ← sibling repo (required for stdio mode)
```

If neither mode is configured, the Questions skill is disabled and shows a warning.

## Post-generation validation

`program_validator.py` runs automatically after every XLSX generation and surfaces warnings
in the UI. To run it directly against a parsed XLSX:

```python
from xlsx_parser import parse_xlsx
from program_validator import validate_program_data

_, program_data, _ = parse_xlsx(open("my_program.xlsx", "rb").read())
warnings = validate_program_data(program_data)
for w in warnings:
    print(w)
```

Checks performed:

- Duplicate question codes within a survey
- Question code doesn't match expected pattern (`surveyCodeNNN`)
- Question code contains a period (Tamanu rejects these)
- Empty question text
- Select / Radio / MultiSelect questions missing options
- Binary / Checkbox questions with options set (Tamanu's schema rejects this)
- CalculatedQuestion missing a calculation formula
- Invalid JSON in `visibilityCriteria`, `validationCriteria`, or `config`
- Registry missing clinical statuses or conditions

## Regenerating BAML bindings

Only needed after editing files in `baml_src/`:

```bash
uv run baml-cli generate
```

## Switching LLM provider

Edit `baml_src/clients.baml` and set the corresponding API key in `.env`.
No Python changes required.

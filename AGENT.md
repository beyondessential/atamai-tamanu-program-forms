@./.maui/knowledge/AGENT.base.md
@./.maui/knowledge/standards/git-conventions.md
@./.maui/knowledge/standards/python-conventions.md
@./.maui/knowledge/standards/tamanu-conventions.md

## Repository: atamai-tamanu-program-forms

Atamai — Tamanu. A conversational AI tool that helps Tamanu
implementers build program form and registry XLSX files for import via Tamanu's program importer.

## Architecture

- `app.py` — Streamlit UI with multi-skill routing via BAML
- `baml_src/` — BAML AI function definitions (`survey_builder.baml`, `clients.baml`)
- `baml_client/` — Auto-generated BAML Python bindings (**never commit**)
- `skills/` — Skill modules (`program_builder`, `lab_builder`, `questions`)
- `xlsx_generator.py` — XLSX file generation for Tamanu program importer
- `xlsx_parser.py` — XLSX file parsing and validation
- `program_validator.py` — Program data validation
- `program_merger.py` — Delta merge for program updates
- `export_generator.py` — Human-readable question export

## Project Rules

### Security

- `.env` must never be committed — `.gitignore` must include it
- `baml_client/` must never be committed — auto-generated and gitignored
- No hardcoded API keys, tokens, or credentials anywhere in the codebase

### BAML

- All LLM interactions must go through BAML functions — no direct `anthropic.Anthropic()` calls
- Import BAML's sync client explicitly: `from baml_client.sync_client import b`
- Provider configuration lives exclusively in `baml_src/clients.baml`
- After any `.baml` file change, `baml_client/` must be regenerated before the app will work
- BAML types must stay in sync with `xlsx_generator.py`
- BAML enum names must be PascalCase; use `@alias("value")` for LLM-facing strings;
  use `_enum_str()` in `xlsx_generator.py` to convert back to Tamanu values
- `xlsx_generator.py` must never reference Tamanu string values directly for enum fields —
  always use `_enum_str()` so the mapping stays in one place

### XLSX Output — Tamanu Importer Compatibility

@./xlsx-format.md

### Python

- Type hints required on all function signatures
- No bare `except:` — always catch a specific exception type
- `openpyxl` is the only library for XLSX generation
- `load_dotenv()` must be called in `app.py` before any BAML or environment access

## Style

Use Australian English throughout all code, documentation, and comments.
Be concise — prefer a clear, short statement over a lengthy justification.

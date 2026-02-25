# Project Rules — atamai-tamanu-program-forms

Rules for code review and validation. Flag any violation as a blocking issue.

## Security

- `.env` must never be committed — `.gitignore` must include it
- `baml_client/` must never be committed — it is auto-generated and must be gitignored
- No hardcoded API keys, tokens, or credentials anywhere in the codebase

## BAML

- All LLM interactions must go through BAML functions — no direct `anthropic.Anthropic()` calls in `app.py` or `xlsx_generator.py`
- Import BAML's sync client explicitly: `from baml_client.sync_client import b` — `baml_client.__init__` exports the async client
- Provider configuration lives exclusively in `baml_src/clients.baml` — not in Python code or environment reads outside of BAML
- After any `.baml` file change, `baml_client/` must be regenerated before the app will work — call this out in PR review if `.baml` files changed but there is no note about regenerating
- BAML types must stay in sync with `xlsx_generator.py` — if a field is added to a BAML class, the generator must handle it
- BAML enum names must be PascalCase (BAML requirement); use `@alias("value")` to define the LLM-facing string; use `_enum_str()` in `xlsx_generator.py` to convert back to the Tamanu camelCase/lowercase value
- `xlsx_generator.py` must never reference Tamanu string values directly for enum fields — always use `_enum_str()` so the mapping stays in one place

## XLSX Output — Tamanu Importer Compatibility

These rules are critical. Invalid output will fail silently or cause import errors in Tamanu.

### Metadata sheet
- Must be named exactly `Metadata`
- Key-value rows (programCode, programName, country) must come before the survey table
- The survey table header row must start with `code` or `name` — the importer scans for this to detect the header
- Valid `surveyType` values: `programs`, `vitals`, `referral`, `simpleChart`, `complexChart`, `complexChartCore`, `obsolete`
- Valid `status` values: `publish`, `draft`, `hidden`

### Survey question sheets
- Sheet name must exactly match `SurveyMetadata.name` — not the code
- `newScreen` column must use the string `"yes"` or empty string — not `True`/`False`/`1`/`0`
- `type` column must use Tamanu's string literals exactly: `FreeText`, `Multiline`, `Number`, `Select`, `Radio`, `MultiSelect`, `Binary`, `Checkbox`, `Date`, `DateTime`, `Autocomplete`, `Instruction`, `CalculatedQuestion`, `PatientData`, `UserData`, `Photo`, `Geolocate`, `Result`, `ConditionQuestion`, `PatientIssue`, `SurveyLink`, `SurveyAnswer`, `SurveyResult`, `SubmissionDate`, `ComplexChartInstanceName`, `ComplexChartDate`, `ComplexChartType`, `ComplexChartSubtype`
- `visibilityCriteria` and `validationCriteria` must be valid JSON strings or empty — never Python dicts serialised with `str()`
- `isSensitive` and `notifiable` must be boolean (`TRUE`/`FALSE`) — not `yes`/`no` strings (Yup boolean schema rejects `yes`/`no`)
- Code naming conventions (all enforced by the generator except question codes which are AI-generated):
  - `programCode`: lowercase no separators from program name — `ncdscreening`
  - Survey `code`: lowercase no separators from survey name — `ncdscreening`
  - Question `code`: surveyCode + 3-digit incrementing number, reset per survey — `ncdscreening001`
  - Registry `registryCode`: lowercase no separators from registry name — `ncdregistry`
  - Clinical status `code`: registryCode + `-` + lowercase name no spaces — `ncdregistry-active`
  - Condition `code`: registryCode + `-` + lowercase name no spaces — `ncdregistry-type2diabetes`
  - Condition category `code`: lowercase name no spaces — `inremission`
- Question codes become `pde-{code}` internally in Tamanu
- `SurveySheet.survey_name` must match its corresponding `SurveyMetadata.name` exactly — a mismatch produces an empty sheet with no questions

## Python

- Type hints required on all function signatures
- No bare `except:` — always catch a specific exception type
- `openpyxl` is the only library for XLSX generation — do not introduce `xlsxwriter` or `pandas` for this purpose
- `load_dotenv()` must be called in `app.py` before any BAML or environment access

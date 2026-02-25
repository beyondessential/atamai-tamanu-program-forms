# Tamanu Program Importer XLSX Format

Source-verified reference for the XLSX format accepted by Tamanu's program importer.
Covers all sheets, fields, valid values, defaults, and cross-field rules.

---

## File Structure

| Sheet | Purpose |
|---|---|
| `Metadata` | Program info + survey list |
| `{Survey Name}` | One sheet per survey, named exactly after the survey `name` |
| `Registry` | Optional — program registry definition |
| `Registry Conditions` | Optional — registry condition list |
| `Registry Condition Categories` | Optional — custom condition categories |

---

## Code Naming Conventions

All codes except question codes are **enforced by the generator** — the AI-provided value is ignored and the code is re-derived from the display name at generation time.

| Code | Rule | Example |
|---|---|---|
| `programCode` | `_flat_lower(programName)` — lowercase, strip all non-alphanumeric | `"NCD Screening"` → `ncdscreening` |
| Survey `code` | `_flat_lower(surveyName)` — same rule | `"NCD Screening"` → `ncdscreening` |
| Question `code` | `{surveyCode}` + 3-digit incrementing number, reset per survey — **AI-generated, not enforced** | `ncdscreening001`, `ncdscreening002` |
| `registryCode` | `_flat_lower(registryName)` | `"NCD Registry"` → `ncdregistry` |
| Clinical status `code` | `{registryCode}-{_flat_lower(statusName)}` | `ncdregistry-active`, `ncdregistry-losttofollowup` |
| Condition `code` | `{registryCode}-{_flat_lower(conditionName)}` | `ncdregistry-type2diabetes` |
| Condition category `code` | `_flat_lower(categoryName)` | `"In Remission"` → `inremission` |

Question codes are AI-generated (not enforced) because they appear inside `visibilityCriteria` JSON as `pde-{code}` references — overriding them would silently break conditional logic.

---

## Metadata Sheet

### Section 1 — Program Key-Value Rows

Rows at the top of the sheet: key in column A, value in column B.
Read until the importer encounters a row where column A is `code` or `name`.

| Key | Required | Default | Notes |
|---|---|---|---|
| `programCode` | **Yes** | — | Lowercase, no separators, derived from `programName`. Generates ID as `program-{code}`. |
| `programName` | **Yes** | — | Display name. |
| `homeServer` | No | — | If provided, validates the import target matches this URL. |
| `country` | No | — | ISO country code e.g. `FJ`. If set and importing to a non-home server, prefixes survey/question names with `(Country)`. |

### Section 2 — Survey Table

The first row with `code` in column A is treated as the header.
One row per survey follows.

| Column | Required | Default | Notes |
|---|---|---|---|
| `code` | **Yes** | — | Lowercase, no separators, derived from survey `name`. |
| `name` | **Yes** | — | Must exactly match the corresponding sheet name (punctuation stripped for matching). |
| `surveyType` | **Yes** | — | See [Survey Types](#survey-types) |
| `status` | No | `draft` | `publish` · `draft` · `hidden` |
| `isSensitive` | **Yes** | — | Boolean (`TRUE`/`FALSE`). Cannot be `TRUE` for vitals or charting surveys. |
| `visibilityStatus` | No | `current` | `current` · `historical`. Setting `historical` marks the survey as deleted. |
| `notifiable` | No | `FALSE` | Boolean (`TRUE`/`FALSE`). Set to `TRUE` to enable notifiable disease reporting. |
| `notifyEmailAddresses` | No | `[]` | Comma- or newline-separated email addresses. Only used when `notifiable` is `TRUE`. |

**Status import behaviour:**
- `publish` — imported to all servers
- `draft` — imported to dev/staging only (non-home servers)
- `hidden` — never imported

---

## Survey Question Sheet

Sheet name must exactly match the survey's `name` from the Metadata table.
First row is the header. One data row per question.
Rows without a `code` value are skipped.

| Column | Required | Default | Notes |
|---|---|---|---|
| `code` | **Yes** | — | `{surveyCode}` + 3-digit incrementing number, reset per survey e.g. `ncdscreening001`. Generates `pde-{code}` internally. |
| `type` | **Yes** | — | See [Question Types](#question-types) |
| `name` | No | — | Internal display name; convention is to match `code`. |
| `text` | No | — | Label shown to the user. |
| `detail` | No | — | Secondary help text. Max 255 chars. |
| `newScreen` | No | `false` | `yes` to start a new screen; anything else is false. |
| `options` | No¹ | — | Comma- or newline-separated option values e.g. `Yes,No,Unknown`. |
| `optionLabels` | No | — | Comma- or newline-separated display labels matching `options`. Omit if labels equal values. |
| `visibilityStatus` | No | `current` | `current` · `historical`. Setting `historical` marks the question as deleted. |
| `visibilityCriteria` | No | — | JSON — conditions for showing this question. See [Visibility Criteria](#visibility-criteria). |
| `validationCriteria` | No | — | JSON — validation rules. See [Validation Criteria](#validation-criteria). |
| `visualisationConfig` | No | — | JSON — chart y-axis config for vitals surveys. Not allowed on complex chart surveys. |
| `calculation` | No¹ | — | math.js expression for `CalculatedQuestion` type, referencing `pde-{code}` identifiers. |
| `config` | No | — | JSON — type-specific config e.g. `{"column":"age"}` for `PatientData`. |
| `indicator` | No | — | Indicator name for reporting. |

¹ Required for the relevant question type (`options` for Select/Radio/MultiSelect; `calculation` for CalculatedQuestion).

---

## Reference Values

### Survey Types

| Value | Notes |
|---|---|
| `programs` | Standard data collection — use for most surveys. |
| `vitals` | Clinical vitals. Must contain exactly the 10 required question IDs (see below). Cannot be `isSensitive`. |
| `referral` | Referral form. |
| `simpleChart` | Simple chart. First question must be `DateTime` type with code `PatientChartingDate`. Cannot be `isSensitive`. |
| `complexChart` | Complex chart. Requires a matching `complexChartCore` survey in the same program. Cannot be `isSensitive`. |
| `complexChartCore` | Core dataset for a complex chart. Must have exactly 4 questions in the required order (see below). Cannot be `isSensitive`. |
| `obsolete` | No questions imported; sheet is optional. |

**Vitals — required question codes (all 10 must be present):**
`PatientVitalsDate`, `PatientVitalsTemperature`, `PatientVitalsWeight`, `PatientVitalsHeight`,
`PatientVitalsSBP`, `PatientVitalsDBP`, `PatientVitalsHeartRate`, `PatientVitalsRespiratoryRate`,
`PatientVitalsSPO2`, `PatientVitalsAVPU`

**ComplexChartCore — required questions in exact order:**
1. `ComplexChartInstanceName` (type `ComplexChartInstanceName`)
2. `ComplexChartDate` (type `ComplexChartDate`)
3. `ComplexChartType` (type `ComplexChartType`)
4. `ComplexChartSubtype` (type `ComplexChartSubtype`)

### Question Types

| Value | Description |
|---|---|
| `FreeText` | Single-line text |
| `Multiline` | Multi-line text |
| `Number` | Numeric input |
| `Date` | Date picker |
| `DateTime` | Date and time picker |
| `SubmissionDate` | Auto-filled with submission date |
| `Select` | Dropdown (single choice) — requires `options` |
| `Radio` | Radio buttons (single choice) — requires `options` |
| `MultiSelect` | Checkbox list (multiple choices) — requires `options` |
| `Binary` | Yes/No toggle |
| `Checkbox` | Single checkbox |
| `Autocomplete` | Typeahead search against reference data |
| `Instruction` | Read-only instructional text (non-answerable) |
| `CalculatedQuestion` | Formula-based — requires `calculation` |
| `Result` | Display-only formula result (non-answerable) |
| `SurveyAnswer` | References an answer from another survey |
| `SurveyResult` | References a result from another survey |
| `SurveyLink` | Links to another survey |
| `PatientData` | Reads/writes patient demographic fields — requires `config` |
| `UserData` | Reads current user info |
| `Photo` | Photo capture |
| `Geolocate` | GPS coordinates |
| `PatientIssue` | Records a patient issue/condition |
| `ConditionQuestion` | Records a patient condition |
| `ComplexChartInstanceName` | Required in `complexChartCore` surveys |
| `ComplexChartDate` | Required in `complexChartCore` surveys |
| `ComplexChartType` | Required in `complexChartCore` surveys |
| `ComplexChartSubtype` | Required in `complexChartCore` surveys |

---

## JSON Field Formats

### Visibility Criteria

```json
{
  "_conjunction": "and",
  "conditions": [
    {
      "_type": "answer",
      "questionId": "pde-ncdscreening003",
      "_value": "Yes",
      "_comparison": "="
    }
  ]
}
```

### Validation Criteria

```json
{ "mandatory": true }
{ "mandatory": true, "min": 0, "max": 300 }
```

### Config (PatientData)

```json
{ "column": "age" }
{ "column": "firstName" }
```

### Visualisation Config (vitals charts)

```json
{
  "yAxis": {
    "graphRange": { "min": 0, "max": 200 },
    "interval": 20
  }
}
```

---

## Registry Sheet (Optional)

Sheet must be named exactly `Registry`.

### Section 1 — Registry Key-Value Rows

| Key | Required | Notes |
|---|---|---|
| `registryCode` | **Yes** | Lowercase, no separators, derived from `registryName`. Generates ID as `programRegistry-{code}`. |
| `registryName` | **Yes** | Must be unique across the system. |
| `currentlyAtType` | **Yes** | `village` · `facility`. Cannot be changed after data exists. |
| `visibilityStatus` | No | `current` (default) · `historical` |

### Section 2 — Clinical Statuses Table

Header row must include `code`. Valid columns:

| Column | Required | Notes |
|---|---|---|
| `code` | **Yes** | `{registryCode}-{_flat_lower(statusName)}` e.g. `ncdregistry-active`. |
| `name` | **Yes** | Display name. |
| `color` | **Yes** | `purple` · `pink` · `orange` · `yellow` · `blue` · `green` · `grey` · `red` · `brown` · `teal` |
| `visibilityStatus` | No | `current` · `historical` · `merged` |

---

## Registry Conditions Sheet (Optional)

Sheet must be named exactly `Registry Conditions`.

| Column | Required | Notes |
|---|---|---|
| `code` | **Yes** | `{registryCode}-{_flat_lower(conditionName)}` e.g. `ncdregistry-type2diabetes`. |
| `name` | **Yes** | Display name e.g. `Type 2 Diabetes`. |
| `visibilityStatus` | No | `current` · `historical` |

---

## Registry Condition Categories Sheet (Optional)

Sheet must be named exactly `Registry Condition Categories`.
Omit entirely to use Tamanu defaults: `unknown`, `disproven`, `resolved`, `recordedInError`.

| Column | Required | Notes |
|---|---|---|
| `code` | **Yes** | `_flat_lower(categoryName)` — lowercase, no separators e.g. `inremission`. |
| `name` | **Yes** | Display name e.g. `In Remission`. |
| `visibilityStatus` | No | `current` · `historical` |

---

## Minimal Working Example

**Metadata sheet:**

```
programCode    diabetesscreening
programName    Diabetes Screening
country        FJ

code                    name                surveyType  status  isSensitive
diabetesscreening       Diabetes Screening  programs    draft   FALSE
```

**Diabetes Screening sheet:**

```
code                    type      name                    text                                          newScreen  validationCriteria
diabetesscreening001    Number    diabetesscreening001    Patient age (years)                           yes        {"mandatory":true,"min":0,"max":120}
diabetesscreening002    Number    diabetesscreening002    Fasting glucose (mmol/L)                                 {"mandatory":true,"min":0,"max":50}
diabetesscreening003    Binary    diabetesscreening003    Has the patient been diagnosed with diabetes?
diabetesscreening004    FreeText  diabetesscreening004    Notes
```

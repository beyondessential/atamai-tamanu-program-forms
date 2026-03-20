@./.maui/REVIEW.md

---

## Project-specific checks

**BAML**
- No direct `anthropic.Anthropic()` calls — all LLM interactions go through BAML functions
- Sync client imported correctly: `from baml_client.sync_client import b`
- If any `.baml` file changed: note in PR that `baml_client/` must be regenerated (`npx @boundaryml/baml generate`)
- BAML types in sync with `xlsx_generator.py` — new BAML fields must be handled in the generator
- Enum values use `@alias()` for LLM-facing strings; `_enum_str()` used in generator for conversion

**XLSX output — Tamanu importer compatibility**
- `isSensitive` and `notifiable` are boolean cells (`TRUE`/`FALSE`) — not strings
- `newScreen` column uses `"yes"` or empty string — not `True`/`False`
- `visibilityCriteria` and `validationCriteria` are valid JSON strings or empty
- Survey sheet name exactly matches `SurveyMetadata.name`
- Metadata sheet has key-value rows before the survey table header

**Security (BLOCK)**
- `baml_client/` committed to the repository (auto-generated, must be gitignored)
- `.env` or secrets files committed

## PR title

Review the PR title. If vague or auto-generated, update it:
`gh pr edit NUMBER --title 'improved title here'`

## Regression testing checklist

Include in the summary a checklist of what needs testing:
- BAML changes: regenerate bindings (`npx @boundaryml/baml generate`) and verify app runs
- `xlsx_generator.py` changes: verify output imports successfully into a Tamanu dev instance
- `app.py` changes: verify chat flow, file uploads, and skill routing work end-to-end

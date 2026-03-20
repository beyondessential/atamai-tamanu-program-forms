"""
Validates Tamanu program definitions before XLSX download and generates summaries
for the auto-fix loop.

validate_program()      — validates a BAML ProgramDefinition (used for the export path)
validate_program_data() — validates a raw dict program_data (used for batch/delta paths)
program_to_summary()    — generates a text summary of a program_data dict for FixProgramErrors

Warnings are non-blocking — the XLSX is still offered for download,
but issues are surfaced to the implementer.
"""

import json
import re

from baml_client.types import ProgramDefinition, QuestionType

_TYPES_REQUIRING_OPTIONS = {QuestionType.Select, QuestionType.Radio, QuestionType.MultiSelect}
_TYPES_FORBIDDING_OPTIONS = {QuestionType.Binary, QuestionType.Checkbox}


def _is_valid_json(value: str) -> bool:
    if not value:
        return True
    try:
        json.loads(value)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def _flat_lower(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def validate_program(program: ProgramDefinition) -> list[str]:
    """Validate a ProgramDefinition and return a list of human-readable warnings."""
    warnings: list[str] = []

    # ── Survey ↔ sheet alignment ───────────────────────────────────────────────

    survey_names = {s.name for s in program.surveys}
    sheet_survey_names = {s.survey_name for s in program.survey_sheets}

    for name in survey_names - sheet_survey_names:
        warnings.append(
            f"Survey '{name}': no matching SurveySheet — "
            "name mismatch will produce an empty sheet on import"
        )
    for name in sheet_survey_names - survey_names:
        warnings.append(
            f"SurveySheet '{name}': no matching survey in Metadata — sheet will be ignored"
        )

    # ── Questions ─────────────────────────────────────────────────────────────

    for sheet in program.survey_sheets:
        survey_name = sheet.survey_name
        expected_code_prefix = _flat_lower(survey_name)
        seen_codes: set[str] = set()

        for q in sheet.questions:
            loc = f"Survey '{survey_name}', question '{q.code}'"

            # Duplicate codes within a survey
            if q.code in seen_codes:
                warnings.append(f"{loc}: duplicate question code")
            seen_codes.add(q.code)

            # Code naming convention: surveyCodeNNN
            if not re.match(rf"^{re.escape(expected_code_prefix)}\d{{3}}$", q.code):
                warnings.append(
                    f"{loc}: code doesn't match expected pattern "
                    f"'{expected_code_prefix}NNN' (e.g. {expected_code_prefix}001)"
                )

            # Periods break Tamanu's internal pde- prefixed lookups
            if "." in q.code:
                warnings.append(f"{loc}: code contains a period (not allowed in Tamanu)")

            # Empty question text
            if not (q.text or "").strip():
                warnings.append(f"{loc} ({q.type.value}): question text is empty")

            # Type-specific option checks
            if q.type in _TYPES_REQUIRING_OPTIONS and not q.options:
                warnings.append(f"{loc}: {q.type.value} question has no options defined")
            if q.type in _TYPES_FORBIDDING_OPTIONS and q.options:
                warnings.append(
                    f"{loc}: {q.type.value} question must not have options "
                    "(Tamanu's schema rejects this)"
                )

            # CalculatedQuestion needs a formula
            if q.type == QuestionType.CalculatedQuestion and not q.calculation:
                warnings.append(f"{loc}: CalculatedQuestion has no calculation formula")

            # JSON fields
            for field, value in [
                ("visibilityCriteria", q.visibility_criteria),
                ("validationCriteria", q.validation_criteria),
                ("config", q.config),
            ]:
                if not _is_valid_json(value or ""):
                    warnings.append(f"{loc}: {field} is not valid JSON — {value!r}")

    # ── Registry ──────────────────────────────────────────────────────────────

    if program.registry:
        reg = program.registry
        if not reg.clinical_statuses:
            warnings.append("Registry: no clinical statuses defined (at least one required)")
        if not reg.conditions:
            warnings.append("Registry: no conditions defined")

    return warnings


# ── Dict-based validation (for batch/delta generation paths) ──────────────────

_TYPES_REQUIRING_OPTIONS_STR = {"Select", "Radio", "MultiSelect"}
_TYPES_FORBIDDING_OPTIONS_STR = {"Binary", "Checkbox"}


def validate_program_data(program_data: dict) -> list[str]:
    """
    Validate a program_data dict (from xlsx_parser or batch generation) and
    return a list of human-readable warnings.
    """
    warnings: list[str] = []

    for survey in program_data.get("surveys", []):
        survey_name = survey.get("name", "")
        expected_prefix = _flat_lower(survey_name)
        seen_codes: set[str] = set()

        for q in survey.get("questions", []):
            code = q.get("code", "")
            q_type = q.get("type", "")
            loc = f"Survey '{survey_name}', question '{code}'"

            if code in seen_codes:
                warnings.append(f"{loc}: duplicate question code")
            seen_codes.add(code)

            if not re.match(rf"^{re.escape(expected_prefix)}\d{{3}}$", code):
                warnings.append(
                    f"{loc}: code doesn't match expected pattern "
                    f"'{expected_prefix}NNN' (e.g. {expected_prefix}001)"
                )

            if "." in code:
                warnings.append(f"{loc}: code contains a period (not allowed in Tamanu)")

            if not (q.get("text") or "").strip():
                warnings.append(f"{loc} ({q_type}): question text is empty")

            if q_type in _TYPES_REQUIRING_OPTIONS_STR and not q.get("options"):
                warnings.append(f"{loc}: {q_type} question has no options defined")
            if q_type in _TYPES_FORBIDDING_OPTIONS_STR and q.get("options"):
                warnings.append(
                    f"{loc}: {q_type} question must not have options "
                    "(Tamanu's schema rejects this)"
                )

            if q_type == "CalculatedQuestion" and not q.get("calculation"):
                warnings.append(f"{loc}: CalculatedQuestion has no calculation formula")

            for field in ("visibilityCriteria", "validationCriteria", "config"):
                val = q.get(field, "")
                if not _is_valid_json(val):
                    warnings.append(f"{loc}: {field} is not valid JSON — {val!r}")

    return warnings


def program_to_summary(program_data: dict) -> str:
    """
    Generate a text summary of a program_data dict for use with FixProgramErrors.
    Includes all surveys and their questions (code, type, text).
    """
    lines = [
        f"Program: {program_data.get('program_name', '')} ({program_data.get('program_code', '')})"
    ]
    for survey in program_data.get("surveys", []):
        questions = survey.get("questions", [])
        lines.append(
            f"\nSurvey: {survey.get('name', '')} ({survey.get('code', '')}) — "
            f"type: {survey.get('surveyType', '')}, status: {survey.get('status', '')}"
        )
        lines.append(f"  Questions ({len(questions)}):")
        for q in questions:
            desc = f"  - {q.get('code', '')}: {q.get('type', '')} — {q.get('text', '') or q.get('name', '')}"
            if q.get("options"):
                desc += f" [options: {q['options']}]"
            if q.get("validationCriteria"):
                desc += f" [validation: {q['validationCriteria']}]"
            if q.get("visibilityCriteria"):
                desc += f" [visible when: {q['visibilityCriteria']}]"
            if q.get("calculation"):
                desc += f" [calculation: {q['calculation']}]"
            lines.append(desc)
    return "\n".join(lines)

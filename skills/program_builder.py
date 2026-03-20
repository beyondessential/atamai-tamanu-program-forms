"""Program Builder skill -- creates, modifies, validates, and exports Tamanu program form XLSX files."""

import re

import streamlit as st

from baml_client.sync_client import b
from export_generator import generate_questions_export
from program_merger import ai_question_to_dict, apply_program_update
from program_validator import validate_program_data, program_to_summary
from xlsx_generator import _enum_str, _flat_lower, generate_xlsx_from_program_data

TITLE = "Program Builder"
ICON = "🏥"
DESCRIPTION = "Create, modify, validate, and export Tamanu program forms and patient registries."

_BATCH_SIZE = 15
_MAX_FIX_ATTEMPTS = 3

_MANUAL = """
## What can this tool do?

Atamai is an AI assistant that builds Tamanu program form XLSX files through conversation.
Upload a file or just start typing to begin.

---

### Create a new program

Describe the program you need -- its name, surveys, and questions.
The AI will ask clarifying questions then generate a ready-to-import XLSX.

**Tips:**
- Mention the country code if this is a country-specific program (e.g. "country: FJ")
- Specify which questions are mandatory or conditional
- Say if the program needs a patient registry

---

### Modify an existing program

Upload a Tamanu program XLSX export, then describe your changes.

**Examples:**
- "Add a mandatory Date of Birth question after the first question"
- "Change the options for 'Referral outcome' to Accepted, Declined, Pending"
- "Mark the HIV status question as sensitive"
- "Add a new survey called 'Follow-up' with three questions"

---

### Generate from a form image

Upload a photo or scan of a paper form, whiteboard diagram, or screenshot.
The AI will extract the fields and build a program from them.

**Tips:**
- Clear, well-lit photos work best
- Include all pages if the form spans multiple sheets

---

### Generate from a PDF

Upload a program specification document or data dictionary.
The AI will read the content and propose a matching program structure.

---

### Export questions for review

Ask the AI to "show me the questions" or "give me a spreadsheet of questions and options".
It produces a simple human-readable Excel (one sheet per survey) with question text, type,
answer options, mandatory flags, validation constraints, and visibility conditions.

---

### Patient registry

A patient registry tracks which patients are enrolled in a program and their clinical status over time.
Tell the AI your program needs a registry, then provide the following details.

**Registry basics**
- Registry name (e.g. "NCD Registry") -- the code is derived automatically
- Whether patients are tracked at **village** or **facility** level

**Clinical statuses**
The states a patient can be in. Every registry needs at least one.

| Name | Colour |
|---|---|
| Active | Green |
| Discharged | Grey |
| Lost to follow-up | Orange |

Available colours: Purple, Pink, Orange, Yellow, Blue, Green, Grey, Red, Brown, Teal

**Conditions tracked**
The diseases or conditions managed by this registry (e.g. Type 2 Diabetes, Hypertension, Obesity).

**Condition categories** *(optional)*
Custom categories beyond the defaults (Unknown, Disproven, Resolved, Recorded in error).

---

### Supported survey types

| Type | Use |
|---|---|
| `programs` | Standard data collection (use for most surveys) |
| `vitals` | Clinical vitals -- requires the 10 standard vital question codes |
| `referral` | Referral form |
| `simpleChart` | Simple chart/graph |
| `complexChart` | Complex chart -- requires a matching `complexChartCore` survey |
| `complexChartCore` | Core dataset for a complex chart |
| `obsolete` | Retired survey |

---

### Supported question types

FreeText, Multiline, Number, Date, DateTime, SubmissionDate,
Select, Radio, MultiSelect, Binary, Checkbox,
Autocomplete, Instruction, CalculatedQuestion, Result,
PatientData, UserData, Photo, Geolocate,
PatientIssue, ConditionQuestion, SurveyAnswer, SurveyResult, SurveyLink

---

### File types you can upload

- **XLSX** -- existing Tamanu program export to modify
- **PDF** -- program specification or data dictionary
- **Image** (PNG, JPG, WEBP) -- paper form or diagram
"""


@st.dialog("Help & Manual", width="large")
def _show_manual() -> None:
    st.markdown(_MANUAL)


def init_state() -> None:
    defaults = {
        "pb_xlsx_data": None,
        "pb_program_name": "program",
        "pb_validation_warnings": [],
        "pb_is_export": False,
        "pb_program_data": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def reset_state() -> None:
    st.session_state.pb_xlsx_data = None
    st.session_state.pb_program_name = "program"
    st.session_state.pb_validation_warnings = []
    st.session_state.pb_is_export = False
    st.session_state.pb_program_data = None


def render_sidebar() -> None:
    if st.button("Help & Manual", icon="📖", use_container_width=True):
        _show_manual()


def render_outputs() -> None:
    if not st.session_state.pb_xlsx_data:
        return

    if st.session_state.pb_is_export:
        st.success("Your questions export is ready to download.")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.download_button(
                label="Download questions export",
                data=st.session_state.pb_xlsx_data,
                file_name=f"{st.session_state.pb_program_name}-questions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="pb_dl_export",
            )
        with col2:
            if st.button("Start new program", use_container_width=True, key="pb_new_export"):
                reset_state()
                st.session_state.messages = []
                st.rerun()
    else:
        for w in st.session_state.pb_validation_warnings:
            st.warning(w)
        st.success("Your program XLSX is ready to download.")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.download_button(
                label="Download program XLSX",
                data=st.session_state.pb_xlsx_data,
                file_name=f"{st.session_state.pb_program_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="pb_dl_program",
            )
        with col2:
            if st.button("Start new program", use_container_width=True, key="pb_new_program"):
                reset_state()
                st.session_state.messages = []
                st.rerun()


def handle_message(user_input: str, conversation_history: str) -> None:
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = b.ProcessMessage(conversation_history)

        st.write(result.message)
        st.session_state.messages.append({"role": "assistant", "content": result.message})

        if result.ready_to_export:
            try:
                with st.spinner("Generating program definition..."):
                    program = b.BuildSurveyDefinition(conversation_history)
                with st.spinner("Building questions export..."):
                    xlsx_bytes = generate_questions_export(program)
                st.session_state.pb_xlsx_data = xlsx_bytes
                st.session_state.pb_program_name = program.program_code.lower()
                st.session_state.pb_validation_warnings = []
                st.session_state.pb_is_export = True
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate export: {e}")

        elif result.ready_to_generate:
            try:
                original_data = st.session_state.get("upload_program_data")

                if original_data:
                    # Delta path: AI generates only the changes, Python merges
                    with st.spinner("Generating program changes..."):
                        update = b.BuildProgramUpdate(conversation_history)
                    with st.spinner("Applying changes..."):
                        updated_surveys = apply_program_update(original_data["surveys"], update)
                    program_data = {**original_data, "surveys": updated_surveys}
                else:
                    # Batch path: plan first, then generate questions in batches
                    program_data = _build_program_from_plan(conversation_history)

                program_data, warnings = _autofix_program_data(program_data)

                with st.spinner("Building XLSX..."):
                    xlsx_bytes = generate_xlsx_from_program_data(program_data)

                st.session_state.pb_xlsx_data = xlsx_bytes
                st.session_state.pb_program_name = re.sub(
                    r"[^a-z0-9-]", "-", program_data.get("program_code", "program").lower()
                ).strip("-")
                st.session_state.pb_program_data = program_data
                st.session_state.pb_validation_warnings = warnings
                st.session_state.pb_is_export = False
                st.rerun()
            except Exception as e:
                st.error(f"Failed to generate file: {e}")


# -- Private helpers -----------------------------------------------------------

def _build_program_from_plan(conversation_history: str) -> dict:
    """Build a program_data dict via plan + batched question generation."""
    with st.spinner("Planning program structure..."):
        plan = b.BuildProgramPlan(conversation_history)

    surveys = []
    for entry in plan.surveys:
        total = entry.total_questions
        all_questions = []

        for start in range(0, total, _BATCH_SIZE):
            end = min(start + _BATCH_SIZE, total)
            count = end - start
            start_code = f"{entry.survey_code}{start + 1:03d}"
            end_code = f"{entry.survey_code}{end:03d}"
            range_desc = (
                f"questions {start + 1}-{end} of {total} total. "
                f"Codes {start_code} through {end_code}. "
                f"Generate exactly {count} questions."
            )

            prev_summary = ""
            if all_questions:
                last = all_questions[-3:]
                prev_lines = [
                    f"- {q.code} ({q.type.value if hasattr(q.type, 'value') else q.type}): {q.text}"
                    for q in last
                ]
                prev_summary = (
                    "Previously generated (last 3 questions -- continue from here):\n"
                    + "\n".join(prev_lines)
                )

            label = (
                f"Building questions {start + 1}-{end} of {total}"
                + (f" ({entry.survey_name})" if len(plan.surveys) > 1 else "")
                + "..."
            )
            with st.spinner(label):
                batch = b.BuildProgramQuestionsRange(
                    conversation_history,
                    entry.survey_code,
                    entry.survey_name,
                    range_desc,
                    prev_summary,
                )

            # Top-up retry: if the AI returned fewer questions than requested,
            # generate the remaining ones starting from where it stopped.
            if len(batch) < count:
                actual_got = len(batch)
                remaining = count - actual_got
                retry_start = start + actual_got
                retry_start_code = f"{entry.survey_code}{retry_start + 1:03d}"
                retry_end_code = f"{entry.survey_code}{end:03d}"
                retry_range_desc = (
                    f"questions {retry_start + 1}-{end} of {total} total. "
                    f"Codes {retry_start_code} through {retry_end_code}. "
                    f"Generate exactly {remaining} questions."
                )
                retry_last = batch[-3:] if batch else []
                retry_prev_lines = [
                    f"- {q.code} ({q.type.value if hasattr(q.type, 'value') else q.type}): {q.text}"
                    for q in retry_last
                ]
                retry_prev = (
                    "Previously generated (last questions -- continue from here):\n"
                    + "\n".join(retry_prev_lines)
                ) if retry_prev_lines else ""
                retry_label = (
                    f"Completing questions {retry_start + 1}-{end} of {total}"
                    + (f" ({entry.survey_name})" if len(plan.surveys) > 1 else "")
                    + "..."
                )
                with st.spinner(retry_label):
                    retry_batch = b.BuildProgramQuestionsRange(
                        conversation_history,
                        entry.survey_code,
                        entry.survey_name,
                        retry_range_desc,
                        retry_prev,
                    )
                batch = list(batch) + list(retry_batch)

            all_questions.extend(batch)

        # Tail check: catch any questions the plan undercounted.
        # Ask the AI for anything beyond the last generated code; it returns []
        # if the survey is already complete.
        if all_questions:
            last_q = all_questions[-1]
            last_code = last_q.code if hasattr(last_q, "code") else ""
            tail_prev_lines = [
                f"- {q.code} ({q.type.value if hasattr(q.type, 'value') else q.type}): {q.text}"
                for q in all_questions[-3:]
            ]
            tail_prev = (
                "Previously generated (last 3 questions):\n"
                + "\n".join(tail_prev_lines)
            )
            tail_range_desc = (
                f"any remaining questions beyond {last_code}. "
                f"Return an empty array if all questions have been generated."
            )
            tail_label = (
                "Checking for remaining questions"
                + (f" ({entry.survey_name})" if len(plan.surveys) > 1 else "")
                + "..."
            )
            with st.spinner(tail_label):
                tail_batch = b.BuildProgramQuestionsRange(
                    conversation_history,
                    entry.survey_code,
                    entry.survey_name,
                    tail_range_desc,
                    tail_prev,
                )
            if tail_batch:
                all_questions.extend(tail_batch)

        surveys.append({
            "code": entry.survey_code,
            "name": entry.survey_name,
            "surveyType": _enum_str(entry.survey_type),
            "status": _enum_str(entry.status),
            "isSensitive": bool(entry.is_sensitive),
            "visibilityStatus": "current",
            "notifiable": bool(entry.notifiable),
            "notifyEmailAddresses": entry.notify_email_addresses or "",
            "questions": [ai_question_to_dict(q) for q in all_questions],
        })

    registry = _registry_to_dict(plan.registry) if plan.registry else None

    return {
        "program_code": plan.program_code,
        "program_name": plan.program_name,
        "country": plan.country or "",
        "surveys": surveys,
        "registry": registry,
    }


def _registry_to_dict(registry) -> dict:
    """Convert a BAML ProgramRegistry to the program_data registry dict format."""
    reg_code = _flat_lower(registry.registry_name)
    kv = {
        "registryCode": reg_code,
        "registryName": registry.registry_name,
        "currentlyAtType": _enum_str(registry.currently_at_type),
    }
    if registry.visibility_status:
        kv["visibilityStatus"] = _enum_str(registry.visibility_status)

    statuses = [
        {
            "code": f"{reg_code}-{_flat_lower(s.name)}",
            "name": s.name,
            "color": _enum_str(s.color),
            "visibilityStatus": _enum_str(s.visibility_status) if s.visibility_status else "current",
        }
        for s in registry.clinical_statuses
    ]

    conditions = [
        {
            "code": f"{reg_code}-{_flat_lower(c.name)}",
            "name": c.name,
            "visibilityStatus": _enum_str(c.visibility_status) if c.visibility_status else "current",
        }
        for c in registry.conditions
    ]

    condition_categories = [
        {
            "code": _flat_lower(cat.name),
            "name": cat.name,
            "visibilityStatus": _enum_str(cat.visibility_status) if cat.visibility_status else "current",
        }
        for cat in (registry.condition_categories or [])
    ]

    return {
        "kv": kv,
        "statuses": statuses,
        "conditions": conditions,
        "condition_categories": condition_categories,
    }


def _autofix_program_data(program_data: dict) -> tuple[dict, list[str]]:
    """Run up to _MAX_FIX_ATTEMPTS validation+fix cycles. Returns (program_data, warnings)."""
    for attempt in range(1, _MAX_FIX_ATTEMPTS + 1):
        warnings = validate_program_data(program_data)
        if not warnings:
            return program_data, []

        n = len(warnings)
        label = (
            f"Fixing {n} validation issue{'s' if n != 1 else ''} "
            f"(attempt {attempt}/{_MAX_FIX_ATTEMPTS})..."
        )
        try:
            with st.spinner(label):
                summary = program_to_summary(program_data)
                errors_text = "\n".join(f"- {w}" for w in warnings)
                fix = b.FixProgramErrors(summary, errors_text)
                updated_surveys = apply_program_update(program_data["surveys"], fix)
                program_data = {**program_data, "surveys": updated_surveys}
        except Exception:
            break

    return program_data, validate_program_data(program_data)

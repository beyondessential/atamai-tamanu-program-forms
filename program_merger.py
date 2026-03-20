"""
Merges a ProgramDefinitionUpdate (AI-generated delta) with the original survey data
(raw XLSX row dicts) to produce a complete list of surveys ready for XLSX generation.

This avoids asking the AI to reproduce unchanged questions, and preserves XLSX columns
that the SurveyQuestion type doesn't model (indicator, visualisationConfig, etc.).
"""

from baml_client.types import ProgramDefinitionUpdate


def ai_question_to_dict(q) -> dict:
    """Convert a BAML SurveyQuestion to a raw XLSX row dict."""
    q_type = q.type.value if hasattr(q.type, "value") else str(q.type)
    vis_status = ""
    if q.visibility_status:
        vis_status = q.visibility_status.value if hasattr(q.visibility_status, "value") else str(q.visibility_status)
    return {
        "code": q.code,
        "type": q_type,
        "name": q.name,
        "text": q.text,
        "detail": q.detail or "",
        "newScreen": "yes" if q.new_screen else "",
        "options": q.options or "",
        "optionLabels": q.option_labels or "",
        "visibilityCriteria": q.visibility_criteria or "",
        "validationCriteria": q.validation_criteria or "",
        "calculation": q.calculation or "",
        "config": q.config or "",
        "visibilityStatus": vis_status or "current",
    }


def _merge_question(original: dict, ai_q) -> dict:
    """
    Overlay AI-provided fields over an existing question dict.
    Preserves columns not modelled in SurveyQuestion (indicator, visualisationConfig, etc.)
    from the original.
    """
    q_type = ai_q.type.value if hasattr(ai_q.type, "value") else str(ai_q.type)
    vis_status = ""
    if ai_q.visibility_status:
        vis_status = ai_q.visibility_status.value if hasattr(ai_q.visibility_status, "value") else str(ai_q.visibility_status)
    merged = dict(original)
    merged.update({
        "code": ai_q.code,
        "type": q_type,
        "name": ai_q.name,
        "text": ai_q.text,
        "detail": ai_q.detail or "",
        "newScreen": "yes" if ai_q.new_screen else "",
        "options": ai_q.options or "",
        "optionLabels": ai_q.option_labels if ai_q.option_labels is not None else original.get("optionLabels", ""),
        "visibilityCriteria": ai_q.visibility_criteria or "",
        "validationCriteria": ai_q.validation_criteria or "",
        "calculation": ai_q.calculation or "",
        "config": ai_q.config or "",
        "visibilityStatus": vis_status or original.get("visibilityStatus", "current"),
    })
    return merged


def _apply_single_survey_update(original: dict, survey_upd) -> dict:
    """Apply one SurveyUpdate to an existing survey dict."""
    questions = list(original.get("questions", []))
    delete_codes = set(survey_upd.question_codes_to_delete or [])

    questions = [q for q in questions if q.get("code") not in delete_codes]

    for upsert in (survey_upd.upserts or []):
        ai_q = upsert.question
        existing_idx = next(
            (i for i, q in enumerate(questions) if q.get("code") == ai_q.code),
            None,
        )
        if existing_idx is not None:
            questions[existing_idx] = _merge_question(questions[existing_idx], ai_q)
        else:
            new_q = ai_question_to_dict(ai_q)
            insert_after = getattr(upsert, "insert_after", None)
            if insert_after:
                insert_idx = next(
                    (i + 1 for i, q in enumerate(questions) if q.get("code") == insert_after),
                    len(questions),
                )
                questions.insert(insert_idx, new_q)
            else:
                questions.append(new_q)

    return {**original, "questions": questions}


def apply_program_update(original_surveys: list[dict], update: ProgramDefinitionUpdate) -> list[dict]:
    """
    Apply a ProgramDefinitionUpdate delta to the original survey list.

    Iterates original surveys in order, applying updates where they match.
    Original surveys with no matching update are preserved unchanged.
    Surveys in the update that don't match any original are appended as new surveys.

    Each survey dict must contain at least: "name", "code", "questions".
    The "name" key is used for matching (matches survey_name in the update).
    """
    updates_by_name = {u.survey_name: u for u in (update.survey_updates or [])}
    result = []

    # Process originals in order — apply update if one exists, otherwise pass through
    for original in original_surveys:
        survey_name = original.get("name", "")
        if survey_name in updates_by_name:
            result.append(_apply_single_survey_update(original, updates_by_name.pop(survey_name)))
        else:
            result.append(original)

    # Any remaining updates are new surveys not present in the original
    for survey_upd in updates_by_name.values():
        result.append({
            "code": survey_upd.survey_code,
            "name": survey_upd.survey_name,
            "surveyType": "programs",
            "status": "draft",
            "isSensitive": False,
            "visibilityStatus": "current",
            "notifiable": False,
            "notifyEmailAddresses": "",
            "questions": [ai_question_to_dict(u.question) for u in (survey_upd.upserts or [])],
        })

    return result

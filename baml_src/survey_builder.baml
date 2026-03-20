// Tamanu Program Form Builder - BAML AI functions

// ── Types ────────────────────────────────────────────────────────────────────

class SurveyQuestion {
  // Prefixed with surveyCode + 3-digit incrementing number.
  // e.g. surveyCode "ncdscreening" → "ncdscreening001", "ncdscreening002"
  // Becomes pde-{code} internally in Tamanu.
  code string

  // Question type - see QuestionType enum for valid values
  type QuestionType

  // Internal name (often same as code, used for reference)
  name string

  // Text displayed to the user filling in the survey
  text string

  // Whether this question starts a new screen/page (true = new screen)
  new_screen bool

  // For Select, Radio, MultiSelect: comma-separated option values
  // e.g. "Yes,No,Unknown" or "Mild,Moderate,Severe"
  options string?

  // Human-readable labels matching each option (comma-separated)
  // Leave null if labels are the same as option values
  option_labels string?

  // Additional explanatory text shown below the question
  detail string?

  // JSON string: conditions under which this question is visible.
  // e.g. {"_conjunction":"and","conditions":[{"_type":"answer","questionId":"pde-has-diabetes","_value":"Yes","_comparison":"="}]}
  // Leave null if always visible.
  visibility_criteria string?

  // JSON string: validation rules.
  // e.g. {"mandatory":true} or {"mandatory":true,"min":0,"max":300}
  // Leave null if no validation needed.
  validation_criteria string?

  // Formula for CalculatedQuestion type, referencing other question codes
  // e.g. "pde-weight / (pde-height * pde-height)"
  calculation string?

  // JSON string: additional type-specific configuration
  config string?

  // "current" = active, "historical" = mark as deleted - defaults to current
  // Set to "historical" to remove a question that was previously imported
  visibility_status VisibilityStatus?
}

class SurveyMetadata {
  // Lowercase, no separators, derived from the survey name.
  // e.g. "NCD Screening" → "ncdscreening"
  code string

  // Display name shown in Tamanu, e.g. "NCD Screening"
  // This also becomes the sheet name in the XLSX
  name string

  // Survey type - almost always "programs" for standard forms
  survey_type SurveyType

  // "publish" = live, "draft" = dev/staging only, "hidden" = never imported
  status SurveyStatus

  // Whether this survey contains sensitive data - defaults to false
  // Cannot be true for vitals or charting survey types
  is_sensitive bool?

  // "current" = active, "historical" = mark as deleted - defaults to current
  visibility_status VisibilityStatus?

  // Whether this survey triggers notifiable disease reporting
  notifiable bool?

  // Comma-separated email addresses to notify (only used when notifiable is true)
  notify_email_addresses string?
}

class SurveySheet {
  // Must exactly match the corresponding SurveyMetadata.name
  survey_name string
  questions SurveyQuestion[]
}

class RegistryClinicalStatus {
  // Registry code + hyphen + lowercase name with no spaces.
  // e.g. registryCode "ncdregistry", name "Lost to Follow Up" → "ncdregistry-losttofollowup"
  code string

  // Display name shown in Tamanu, e.g. "Active", "Lost to follow-up"
  name string

  // Colour used to display this status in the UI
  color RegistryStatusColor

  // "current" = active, "historical" = mark as deleted - defaults to current
  visibility_status VisibilityStatus?
}

class RegistryCondition {
  // Registry code + hyphen + lowercase name with no spaces.
  // e.g. registryCode "ncdregistry", name "Type 2 Diabetes" → "ncdregistry-type2diabetes"
  code string

  // Display name, e.g. "Type 2 Diabetes"
  name string

  // "current" = active, "historical" = mark as deleted - defaults to current
  visibility_status VisibilityStatus?
}

class RegistryConditionCategory {
  // Lowercase name with no spaces or separators.
  // e.g. name "In Remission" → "inremission"
  // Note: unknown, disproven, resolved, recordedInError are auto-created by default
  code string

  // Display name, e.g. "In remission"
  name string

  // "current" = active, "historical" = mark as deleted - defaults to current
  visibility_status VisibilityStatus?
}

class ProgramRegistry {
  // Lowercase, no separators, derived from the registry name.
  // e.g. "NCD Registry" → "ncdregistry"
  registry_code string

  // Display name, e.g. "NCD Registry"
  registry_name string

  // Whether patients in this registry are tracked at village or facility level
  currently_at_type CurrentlyAtType

  // Clinical statuses a patient can be in, e.g. Active, Discharged, Lost to follow-up
  // Every registry needs at least one status
  clinical_statuses RegistryClinicalStatus[]

  // Conditions/diseases tracked in this registry, e.g. Type 2 Diabetes, Hypertension
  conditions RegistryCondition[]

  // Custom condition categories - omit to use the Tamanu defaults:
  // unknown, disproven, resolved, recordedInError
  condition_categories RegistryConditionCategory[]?

  // "current" = active, "historical" = mark as deleted - defaults to current
  visibility_status VisibilityStatus?
}

class ProgramDefinition {
  // Lowercase, no separators, derived from the program name.
  // e.g. "NCD Screening" → "ncdscreening"
  program_code string

  // Full display name, e.g. "NCD Screening"
  program_name string

  // Optional ISO country code, e.g. "FJ", "WS", "TO"
  country string?

  // One entry per survey in the program (goes in Metadata sheet)
  surveys SurveyMetadata[]

  // One entry per survey with its questions (each becomes a sheet)
  survey_sheets SurveySheet[]

  // Optional patient registry for this program
  registry ProgramRegistry?
}

class ConversationResponse {
  // Message to display to the user
  message string

  // True when enough information has been gathered to generate the importable program XLSX
  ready_to_generate bool

  // True when the user asks for a human-readable questions export (not for Tamanu import)
  // e.g. "show me the questions", "export questions for review", "give me a spreadsheet"
  ready_to_export bool
}

// ── Delta update types ────────────────────────────────────────────────────────

// A single question to add or modify in an existing survey.
// Used by BuildProgramUpdate — the AI outputs only changed questions, not all of them.
class SurveyQuestionUpsert {
  // Full question data as it should appear in the final file
  question SurveyQuestion

  // For new questions only: insert after this question code.
  // Omit to append at the end of the survey.
  insert_after string?
}

// Changes to apply to one survey in an existing program XLSX.
class SurveyUpdate {
  // Must match the existing survey sheet name exactly
  survey_name string

  // Must match the existing survey code exactly (used as question code prefix)
  survey_code string

  // Questions to add or modify. Provide full question data for each.
  upserts SurveyQuestionUpsert[]?

  // Codes of questions to remove from this survey
  question_codes_to_delete string[]?
}

// Delta output from BuildProgramUpdate — only the changed surveys.
// Python merges this with the original parsed data.
class ProgramDefinitionUpdate {
  // One entry per survey being changed; unmodified surveys are omitted
  survey_updates SurveyUpdate[]?
}

// ── Batched generation types ──────────────────────────────────────────────────

// Metadata for one survey in the plan (no question content).
class SurveyPlanEntry {
  // Lowercase, no separators, from survey name
  survey_code string

  // Full display name, e.g. "NCD Screening"
  survey_name string

  // Survey type — almost always "programs"
  survey_type SurveyType

  // Workflow status
  status SurveyStatus

  // Exact number of questions this survey will have
  total_questions int

  // Whether this survey contains sensitive patient data
  is_sensitive bool?

  // Whether this survey triggers notifiable disease reporting
  notifiable bool?

  // Comma-separated email addresses for notifiable disease alerts
  notify_email_addresses string?
}

// Plan output — program metadata plus question counts per survey.
// Question content is NOT included; it is generated per-batch by BuildProgramQuestionsRange.
class ProgramCollectionPlan {
  // Lowercase, no separators, from program name
  program_code string

  // Full display name, e.g. "NCD Screening"
  program_name string

  // Optional ISO country code, e.g. "FJ"
  country string?

  // One entry per survey (metadata only, no questions)
  surveys SurveyPlanEntry[]

  // Optional patient registry — full definition
  registry ProgramRegistry?
}

// ── Enums ────────────────────────────────────────────────────────────────────

enum QuestionType {
  // Free text input
  FreeText
  // Multi-line text input
  Multiline
  // Numeric input (supports min/max validation)
  Number
  // Date picker
  Date
  // Date and time picker
  DateTime
  // Auto-filled with submission date
  SubmissionDate
  // Dropdown select (single choice)
  Select
  // Radio buttons (single choice, options always visible)
  Radio
  // Checkbox list (multiple choices)
  MultiSelect
  // Yes/No toggle
  Binary
  // Checkbox (true/false)
  Checkbox
  // Typeahead search against reference data
  Autocomplete
  // Read-only instructional text (not answered)
  Instruction
  // Calculated from other answers
  CalculatedQuestion
  // References answer from another survey
  SurveyAnswer
  // References result from another survey
  SurveyResult
  // Links to another survey
  SurveyLink
  // Reads/writes patient demographic fields
  PatientData
  // Reads current user information
  UserData
  // Photo capture
  Photo
  // GPS coordinates
  Geolocate
  // Computed result display (not answered)
  Result
  // Records a patient issue/condition
  PatientIssue
  // Records a patient condition
  ConditionQuestion
  // Required question types for complexChartCore surveys (use in that order)
  ComplexChartInstanceName
  ComplexChartDate
  ComplexChartType
  ComplexChartSubtype
}

enum SurveyType {
  // Standard program data collection form (use this for most surveys)
  Programs @alias("programs")
  // Clinical vitals (special validation rules apply)
  Vitals @alias("vitals")
  // Referral form
  Referral @alias("referral")
  // Simple chart/graph
  SimpleChart @alias("simpleChart")
  // Complex chart (requires a matching complexChartCore survey)
  ComplexChart @alias("complexChart")
  // Core dataset for a complex chart
  ComplexChartCore @alias("complexChartCore")
  // Retired survey - no questions imported; sheet is optional
  Obsolete @alias("obsolete")
}

enum VisibilityStatus {
  // Active record (default)
  Current @alias("current")
  // Mark as deleted on import
  Historical @alias("historical")
}

enum CurrentlyAtType {
  Village @alias("village")
  Facility @alias("facility")
}

enum RegistryStatusColor {
  Purple @alias("purple")
  Pink @alias("pink")
  Orange @alias("orange")
  Yellow @alias("yellow")
  Blue @alias("blue")
  Green @alias("green")
  Grey @alias("grey")
  Red @alias("red")
  Brown @alias("brown")
  Teal @alias("teal")
}

enum SurveyStatus {
  // Live - imported to all servers
  Publish @alias("publish")
  // Draft - imported to dev/staging servers only
  Draft @alias("draft")
  // Hidden - never imported
  Hidden @alias("hidden")
}

// ── Functions ────────────────────────────────────────────────────────────────

// Interprets an uploaded image (paper form, screenshot, whiteboard, etc.) and extracts
// enough detail to pre-fill a Tamanu program form conversation.
function InterpretFormImage(image: image) -> string {
  client DefaultClient
  prompt #"
    Examine this image — it may be a paper form, whiteboard diagram, screenshot,
    or photograph related to a clinical program form.

    Extract and describe in detail:
    - All field names and question labels
    - Input types where apparent (text, number, date, yes/no, dropdown, checkbox, etc.)
    - Option lists for multi-choice fields
    - Section headings and page/screen boundaries
    - Any conditional logic or branching visible
    - Any notes about mandatory fields or sensitive data

    Format your response as a structured plain-text description
    that can be used to build a Tamanu program form.

    {{ image }}
  "#
}

// Handles each turn of the conversation.
// Asks clarifying questions until enough information is gathered,
// then signals that we are ready to generate.
function ProcessMessage(conversation_history: string) -> ConversationResponse {
  client DefaultClient
  prompt #"
    You are an expert assistant helping implementers build Tamanu program forms.
    Tamanu is a healthcare management system.
    Program forms are surveys used to collect clinical data from patients.

    Your job is to gather enough information to generate a complete, importable
    XLSX file. Be concise — ask one question or a small related group at a time.

    Gather before generating:
    - Program name and country (optional)
    - For each survey: name, purpose, and questions (text, type, options if select/radio,
      mandatory flag, conditional logic, new screen boundaries)
    - Whether the program includes a patient registry. If yes:
      - Registry name and code
      - Whether patients are tracked at village or facility level
      - Clinical statuses (the states a patient can be in, e.g. Active, Discharged,
        Lost to follow-up) — need a name and colour for each
      - Conditions tracked in the registry (e.g. Type 2 Diabetes, Hypertension)
      - Whether custom condition categories are needed beyond the defaults
        (defaults: Unknown, Disproven, Resolved, Recorded in error)
    - Before finishing: confirm whether any survey contains sensitive patient data
      (e.g. mental health, HIV) and whether it records notifiable diseases requiring
      email alerts (if so, which addresses)

    If the conversation starts with [EXISTING PROGRAM LOADED], an existing XLSX has been
    uploaded. List ALL surveys loaded (name, type, number of questions), then ask what
    changes the user wants to make. Do not re-ask for information already present.

    If the conversation starts with [FORM IMAGE INTERPRETED], a form image has been
    analysed. Use the extracted description to pre-fill program details, confirm with
    the user, and ask for anything missing before generating.

    If the conversation starts with [PDF DOCUMENT LOADED], a PDF document has been
    uploaded (e.g. a program specification or data dictionary). Use the content to
    pre-fill program details, confirm with the user, and ask for anything missing.

    When referencing codes (program code, survey code, question codes, registry code, etc.)
    always present them in lowercase as they appear in the XLSX, e.g. "ncdscreening" not "NCDSCREENING".

    If the user asks to "show me the questions", "export questions for review",
    "give me a spreadsheet of questions", or similar — set ready_to_export to true.
    This produces a human-readable Excel (not a Tamanu import file).

    When ready to generate the importable Tamanu XLSX, set ready_to_generate to true
    and summarise what you are about to generate.

    Conversation so far:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

// Generates the full structured program definition from the conversation.
// Called once ProcessMessage returns ready_to_generate = true.
function BuildSurveyDefinition(conversation_history: string) -> ProgramDefinition {
  client DefaultClient
  prompt #"
    You are an expert at building Tamanu program form definitions.
    Based on the conversation below, generate a complete ProgramDefinition
    that can be converted into an importable XLSX file.

    Code naming rules (applied consistently across all sheets):
    - program_code: lowercase, no separators, from program name. e.g. "NCD Screening" → "ncdscreening"
    - survey code: lowercase, no separators, from survey name. e.g. "NCD Screening" → "ncdscreening"
    - question code: surveyCode + 3-digit incrementing number, reset per survey. e.g. surveyCode "ncdscreening" → "ncdscreening001", "ncdscreening002"
    - question.name: same as code
    - registry_code: lowercase, no separators, from registry name. e.g. "NCD Registry" → "ncdregistry"
    - clinical status code: registryCode + "-" + lowercase name no spaces. e.g. "ncdregistry-active"
    - condition code: registryCode + "-" + lowercase name no spaces. e.g. "ncdregistry-type2diabetes"
    - condition category code: lowercase name no spaces. e.g. "inremission"

    Other rules:
    - new_screen: set to true for the first question of each logical section/screen
    - For Select/Radio/MultiSelect: always provide the options field
    - For mandatory questions: set validation_criteria to {"mandatory":true}
    - For number questions with a range: {"mandatory":true,"min":X,"max":Y}
    - For number questions with a normal/reference range: add "normalRange":{"min":X,"max":Y} (valid on Number, CalculatedQuestion, Result)
    - For visibility_criteria use this JSON format:
      {"_conjunction":"and","conditions":[{"_type":"answer","questionId":"pde-QUESTION-CODE","_value":"VALUE","_comparison":"="}]}
    - survey_type should be "programs" unless there is a specific reason otherwise
    - status should be "draft" unless the implementer confirmed it is ready for production
    - is_sensitive: set to true only if the implementer explicitly says the survey contains sensitive data; omit otherwise
    - visibility_status: omit unless removing a previously imported survey/question (set to "historical")
    - notifiable / notify_email_addresses: omit unless the implementer mentions notifiable disease reporting
    - registry: only set if the program uses a patient registry
      - clinical_statuses: every registry needs at least one; pick a fitting colour for each
      - conditions: list all diseases/conditions the registry tracks
      - condition_categories: omit unless the implementer needs custom categories beyond the defaults

    When the conversation starts with [EXISTING PROGRAM LOADED], you MUST include ALL
    surveys and their questions from the loaded program summary in your output — not just
    the ones explicitly discussed. Apply only the changes the user requested on top of the
    existing content. Do not drop or omit any survey or question that was in the original.

    Conversation:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

// ── Pass 1 of N: plan ─────────────────────────────────────────────────────────
// Returns program/survey metadata and exact question counts — no question content.
// Question content is generated in batches by BuildProgramQuestionsRange.
function BuildProgramPlan(conversation_history: string) -> ProgramCollectionPlan {
  client DefaultClient
  prompt #"
    Plan the complete Tamanu program structure from the conversation.
    Output program/survey metadata and exact question counts ONLY.
    Do NOT output any question content.

    Code naming rules:
    - program_code: lowercase, no separators, from program name. e.g. "NCD Screening" → "ncdscreening"
    - survey_code: lowercase, no separators, from survey name. e.g. "NCD Screening" → "ncdscreening"
    - survey_type: "programs" unless specified otherwise
    - status: "draft" unless the implementer confirmed production-ready

    For each survey, set total_questions to the EXACT count of all questions needed.
    Count every question individually: data fields, instruction text, calculated questions,
    date/number/select fields — everything mentioned in the conversation.
    Do not round; do not estimate. If you are unsure, count every field you intend to generate.
    Include a registry definition (with full ProgramRegistry data) if the program uses one.

    Conversation:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

// ── Pass 2 of N: ranged question generation ───────────────────────────────────
// Generates full question details for a specific numbered range within one survey.
// Python controls the exact range so the AI never has to enumerate the full list.
function BuildProgramQuestionsRange(
  conversation_history: string,
  survey_code: string,
  survey_name: string,
  range_description: string,
  previous_batch_summary: string,
) -> SurveyQuestion[] {
  client DefaultClient
  prompt #"
    Generate a specific batch of questions for the Tamanu survey "{{ survey_name }}"
    (survey code: {{ survey_code }}).

    Batch: {{ range_description }}

    {{ previous_batch_summary }}

    Code naming rules:
    - question code: survey_code + 3-digit number as specified in the batch description
      e.g. survey_code "ncdscreening" + number 1 → "ncdscreening001"
    - question.name: same as code

    For each question in this batch:
    - code, type, name, text: required
    - new_screen: true for first question of each new screen/section
    - options: for Select, Radio, MultiSelect — comma-separated values e.g. "Yes,No,Unknown"
    - option_labels: only if display labels differ from option values
    - detail: help text if any
    - validation_criteria: JSON string e.g. {"mandatory":true} or {"mandatory":true,"min":0,"max":300}
    - visibility_criteria: JSON string with pde- prefixed questionIds:
      {"_conjunction":"and","conditions":[{"_type":"answer","questionId":"pde-QUESTION-CODE","_value":"Yes","_comparison":"="}]}
    - calculation: for CalculatedQuestion, referencing pde-{code} question IDs
    - config: JSON string for type-specific configuration
    - visibility_status: omit unless removing a previously imported question
    Leave fields null if not applicable.

    Conversation (survey context):
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

// ── Delta update: generate only changes ───────────────────────────────────────
// Called instead of BuildProgramPlan when an existing XLSX was uploaded.
// Python merges the delta with the original data — unchanged questions are NOT output here.
function BuildProgramUpdate(conversation_history: string) -> ProgramDefinitionUpdate {
  client DefaultClient
  prompt #"
    You are applying changes to an existing Tamanu program XLSX.
    The original program is described at the start of the conversation
    (lines beginning with [EXISTING PROGRAM LOADED]).

    Output ONLY the surveys and questions that need to be added or modified.
    Do NOT reproduce surveys or questions that are unchanged — Python preserves them automatically.

    For each survey being changed:
    - upserts: list every question to add (new code) or modify (existing code).
      Provide the full question data as it should appear in the final file.
      For new questions, set insert_after to the code of the question it follows
      (omit to append at the end of the survey).
    - question_codes_to_delete: list codes of questions to remove.

    Code naming rules:
    - survey_name: must match the existing sheet name exactly
    - survey_code: lowercase, no separators, matching the existing code
    - For modified questions: keep the original code unchanged
    - For new questions: survey_code + next available 3-digit number
    - question.name: same as code
    - visibility_criteria JSON format:
      {"_conjunction":"and","conditions":[{"_type":"answer","questionId":"pde-QUESTION-CODE","_value":"VALUE","_comparison":"="}]}
    - validation_criteria JSON format: {"mandatory":true} or {"mandatory":true,"min":0,"max":300}

    Conversation:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

// ── Post-generation error fixer ───────────────────────────────────────────────
// Called automatically when validate_program_data() finds issues after generation.
// Returns only the delta needed to fix the listed errors — unchanged questions
// are NOT reproduced; Python merges them via apply_program_update.
function FixProgramErrors(
  program_summary: string,
  errors: string,
) -> ProgramDefinitionUpdate {
  client DefaultClient
  prompt #"
    You are fixing validation errors in a Tamanu program form.

    Output ONLY the questions that need to change to fix the listed errors.
    Do NOT reproduce unchanged questions — Python preserves them automatically.

    CRITICAL: NEVER change a question's type when fixing errors. Fix only the specific
    field mentioned in the error while keeping the original type intact.

    How to fix each error type:
    - "Binary/Checkbox: options field is set" → clear the options field; keep the type
    - "Select/Radio/MultiSelect: no options defined" → add comma-separated options; keep the type
    - "CalculatedQuestion: no calculation formula" → add the formula; keep type as CalculatedQuestion
    - "visibilityCriteria is not valid JSON" → fix the JSON or clear the field
    - "validationCriteria is not valid JSON" → fix the JSON or clear the field
    - "config is not valid JSON" → fix the JSON or clear the field
    - "duplicate question code" → rename the second occurrence to the next available number

    Current program state:
    {{ program_summary }}

    Errors to fix:
    {{ errors }}

    {{ ctx.output_format }}
  "#
}

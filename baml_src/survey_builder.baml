// Tamanu Program Form Builder - BAML AI functions

// ── Types ────────────────────────────────────────────────────────────────────

class SurveyQuestion {
  // Prefixed with programCode + 3-digit incrementing number.
  // e.g. programCode "ncdscreening" → "ncdscreening001", "ncdscreening002"
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

  // True when enough information has been gathered to generate the survey
  ready_to_generate bool
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
    - Program name, short code, and country (optional)
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

    When ready, set ready_to_generate to true and summarise what you are about to generate.

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
    - question code: programCode + 3-digit incrementing number. e.g. "ncdscreening001", "ncdscreening002"
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

    Conversation:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

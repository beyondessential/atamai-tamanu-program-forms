// Tamanu Lab Test Reference Data Builder — BAML types and functions
//
// Generates an XLSX compatible with Tamanu's referenceDataImporter.
// Sheets produced: Lab Test Categories, Lab Test Types,
//                  Lab Test Panels (optional), Lab Test Panel Lab Test Types (optional)

class LabCategory {
  // Display name, e.g. "Haematology", "Biochemistry", "Urinalysis"
  name string

  // Code — lowercase, no spaces or separators, e.g. "haematology", "fbc", "ue"
  code string
}

class LabTestType {
  // Display name, e.g. "Haemoglobin"
  name string

  // Code — lowercase, no spaces or separators, e.g. "hgb", "wbc", "creatinine"
  code string

  // Code of the category this test belongs to — must match a LabCategory.code
  category_code string

  // Result type — Number for numeric results, FreeText for free-text, Select for option lists
  result_type string

  // Unit of measurement, e.g. "g/dL", "mmol/L", "x10^9/L" — omit if not applicable
  unit string?

  // Male reference range — null means no reference range for males
  male_min float?
  male_max float?

  // Female reference range — null means no reference range for females
  female_min float?
  female_max float?

  // Comma-separated option list for Select type, e.g. "Positive, Negative, Indeterminate"
  options string?

  // Whether this test is sensitive and should be hidden from non-privileged users
  is_sensitive bool
}

class LabPanel {
  // Display name, e.g. "Full Blood Count"
  name string

  // Code — lowercase, no spaces, e.g. "fbc", "lft", "bmp"
  code string

  // Category code this panel belongs to — must match a LabCategory.code
  category_code string
}

class PanelTestLink {
  // Panel code — must match a LabPanel.code
  panel_code string

  // Test code — must match a LabTestType.code
  test_code string
}

class LabDefinition {
  // Descriptive name for this dataset, e.g. "Pacific Lab Reference Data"
  name string

  // All test categories (required — every test must belong to a category)
  categories LabCategory[]

  // All test types
  tests LabTestType[]

  // Optional panels — use only when the user wants grouped test ordering
  panels LabPanel[]

  // Links between panels and test types (required when panels is non-empty)
  panel_test_links PanelTestLink[]
}

class LabConversationResponse {
  // Message to display to the user
  message string

  // True when enough information has been gathered to generate the XLSX
  ready_to_generate bool
}

// ── Batched generation types ──────────────────────────────────────────────────

// Metadata for one category in the plan (no test content).
class LabCategoryPlan {
  // Display name, e.g. "Haematology"
  name string

  // Code — lowercase, no spaces, e.g. "haematology"
  code string

  // Exact number of tests in this category
  total_tests int
}

// Plan output — structure and counts only.
// Test content is generated per-category by BuildLabTestsForCategory.
class LabPlan {
  // Descriptive name for this dataset, e.g. "Pacific Lab Reference Data"
  name string

  // One entry per category (metadata + count, no test data)
  categories LabCategoryPlan[]

  // Panels in full (these are few and can be planned upfront)
  panels LabPanel[]

  // Panel↔test links in full
  panel_test_links PanelTestLink[]
}

// ── Functions ────────────────────────────────────────────────────────────────

function ProcessLabMessage(conversation_history: string) -> LabConversationResponse {
  client DefaultClient
  prompt #"
    You are an expert assistant helping implementers build Tamanu lab test reference data.
    Lab reference data defines the test types available in Tamanu and their normal reference ranges.

    Gather the following before generating:

    **For each test category:**
    - Category name (e.g. Haematology, Biochemistry, Urinalysis, Immunology)
    - Category code (lowercase, no spaces — derive from name if not given)

    **For each test type:**
    - Test name and code (lowercase, no spaces, abbreviated — e.g. "hgb" for Haemoglobin)
    - Which category it belongs to
    - Result type: Number (default for measurable tests), FreeText, or Select
      - If Select: the list of options
    - Unit of measurement (for Number type, e.g. g/dL, mmol/L, x10^9/L)
    - Reference ranges — Tamanu supports male and female ranges only (no age banding)
      - Ask whether ranges differ by sex
      - If sex-specific: ask for male min/max and female min/max separately
      - If same for all: use the same values for both male and female
      - If a range has no lower bound, set min to null; if no upper bound, set max to null
      - Omit ranges entirely if the test doesn't have reference ranges (e.g. FreeText tests)
    - Whether the test is sensitive (default: false)

    **Panels (optional):**
    - Ask whether the user wants to define panels (grouped sets of tests for ordering together)
    - If yes: panel name, code, category, and which tests belong to it

    Ask one group of related questions at a time. Do not ask about age-banded ranges — Tamanu does
    not support them for lab tests. Once all tests and their ranges are confirmed, set
    ready_to_generate to true and summarise what you are about to generate.

    Conversation so far:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

// ── Pass 1 of N: plan ─────────────────────────────────────────────────────────
// Returns dataset name, category metadata with exact test counts, and full panel data.
// Test content is generated per-category by BuildLabTestsForCategory.
function BuildLabPlan(conversation_history: string) -> LabPlan {
  client DefaultClient
  prompt #"
    Plan the Tamanu lab test reference data structure from the conversation.
    Output category metadata and exact test counts ONLY — do NOT output test details.

    For each category, set total_tests to the EXACT count of tests in that category.
    Count every test individually. Do not round or estimate.

    Also output panels and panel_test_links in full — they are few and belong in the plan.

    Code naming rules:
    - Category code: lowercase, no spaces, abbreviated from name.
      e.g. "Haematology" → "haematology", "U&E" → "ue"
    - Panel code: lowercase, no spaces, abbreviated from name.
      e.g. "Full Blood Count" → "fbc"

    Conversation:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

// ── Pass 2 of N: per-category test generation ─────────────────────────────────
// Generates all test types for a single category.
function BuildLabTestsForCategory(
  conversation_history: string,
  category_code: string,
  category_name: string,
  total_tests: int,
) -> LabTestType[] {
  client DefaultClient
  prompt #"
    Generate all {{ total_tests }} test types for the lab category
    "{{ category_name }}" (code: {{ category_code }}).

    IMPORTANT: You MUST generate exactly {{ total_tests }} tests.

    For each test:
    - code: lowercase, no spaces, abbreviated from name (e.g. "hgb", "wbc", "creatinine")
    - name: full display name
    - category_code: must be "{{ category_code }}"
    - result_type: "Number" for measurable tests (default), "FreeText", or "Select"
    - unit: unit of measurement for Number tests (e.g. "g/dL", "mmol/L") — omit if not applicable
    - male_min, male_max: male reference range (null if not applicable or no range)
    - female_min, female_max: female reference range (null if same logic applies)
    - options: comma-separated for Select type (e.g. "Positive, Negative, Indeterminate")
    - is_sensitive: whether this test is sensitive (default: false)

    If ranges are the same for male and female, set both identically.
    Omit ranges (null) for FreeText or Select tests unless they have reference ranges.

    Conversation:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

function BuildLabDefinition(conversation_history: string) -> LabDefinition {
  client DefaultClient
  prompt #"
    You are an expert at building Tamanu lab test reference data.
    Based on the conversation below, generate a complete LabDefinition.

    Code naming rules:
    - Category code: lowercase, no spaces, abbreviated from the category name.
      e.g. "Haematology" → "haematology", "U&E" → "ue", "Full Blood Count" → "fbc"
    - Test code: lowercase, no spaces, abbreviated from the test name.
      e.g. "Haemoglobin" → "hgb", "White Blood Cell Count" → "wbc", "Creatinine" → "creatinine"
    - Panel code: lowercase, no spaces, abbreviated from the panel name.

    Result type rules:
    - Use "Number" for all measurable numeric tests (default)
    - Use "FreeText" only for tests where the result is free-form text
    - Use "Select" only when the test has a fixed list of options

    Reference range rules:
    - Only male/female ranges are supported — do not create age-banded ranges
    - If ranges are the same for male and female, set both male and female values identically
    - Set male_min/male_max to null if there is no male-specific range
    - Set female_min/female_max to null if there is no female-specific range
    - Omit both min and max if the test has no reference ranges

    Panel rules:
    - Only include panels if the user explicitly asked for them
    - Each panel must reference a valid category_code

    Conversation:
    {{ conversation_history }}

    {{ ctx.output_format }}
  "#
}

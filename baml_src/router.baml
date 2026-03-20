// Message router — determines which skill should handle a user message.

enum Skill {
  ProgramBuilder @description("Building, modifying, validating, reviewing, or exporting Tamanu program forms, surveys, or patient registries")
  LabBuilder @description("Building or modifying Tamanu lab test reference data, reference ranges, lab panels, or test categories")
  Questions @description("General questions about how Tamanu works, configuration, troubleshooting, or best practices")
  OffTopic @description("Completely unrelated to Tamanu")
}

class MessageRoute {
  skill Skill
}

function RouteMessage(message: string) -> MessageRoute {
  client FastClient
  prompt #"
    Route the user's message to the appropriate Tamanu tool.

    - ProgramBuilder: building, editing, modifying, validating, reviewing, or exporting Tamanu
      program forms, surveys, registries, or XLSX import files — question types, survey codes,
      visibility criteria, patient registries, clinical statuses, etc.
    - LabBuilder: building or modifying lab test reference data — test panels, test codes,
      reference ranges, units, sample types, or age/sex-banded normal ranges.
    - Questions: general questions about how Tamanu works, how to configure it, troubleshooting,
      or best practices. Use this for "how does X work" or conceptual questions.
    - OffTopic: the message is completely unrelated to Tamanu (e.g. general coding, weather).

    If the message is about a specific build/edit task, prefer ProgramBuilder or LabBuilder over Questions.
    If the message is a general "how does X work" question, prefer Questions.

    {{ ctx.output_format }}

    User message: {{ message }}
  "#
}

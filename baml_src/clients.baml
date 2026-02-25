generator python_client {
  output_type "python/pydantic"
  output_dir "../"
  version "0.216.0"
}

// LLM client configuration
// To switch providers, update the client block below and set the
// corresponding API key in your .env file.

client<llm> DefaultClient {
  provider anthropic
  options {
    model "claude-sonnet-4-6"
    api_key env.ANTHROPIC_API_KEY
  }
}

client<llm> FastClient {
  provider anthropic
  options {
    model "claude-haiku-4-5-20251001"
    api_key env.ANTHROPIC_API_KEY
  }
}

// Uncomment to switch to OpenAI:
// client<llm> DefaultClient {
//   provider openai
//   options {
//     model "gpt-4o"
//     api_key env.OPENAI_API_KEY
//   }
// }

---
name: tool-use-schema-writer
description: Takes a function description (name, purpose, parameters) and writes a valid Anthropic tool_use JSON schema, with type annotations, required fields, and a description for each parameter. Produces a Python usage snippet for client.messages.create(tools=[...]). Use when wiring a Claude agent to a function or API, designing tools for a multi-agent system, or documenting an existing tool for agent consumption.
---

# tool-use-schema-writer

Converts a natural-language function description into a valid Anthropic `tool_use` definition. The output is ready to paste into `client.messages.create(tools=[...])`. This skill enforces the two constraints that cause most tool-use bugs: descriptions that are too vague for the model to choose the right tool, and missing `required` arrays that cause the model to omit non-optional fields.

## How to respond

**Four rules come before the steps and outrank them:**

- **Answer what was asked, first.** Open with the answer, the decision or the artifact, in plain words. Scores, matrices, frameworks and tags come after it, and anything that doesn't change the answer is cut.
- **Use only what you were given.** Don't add facts, names, numbers, incidents, history, steps or sections the input doesn't contain. What you need and don't have is left out of the artifact and listed once at the end under "To confirm".
- **Deliver from what you have.** When the request gives you something to work on, state your assumptions in a line and produce the result. When it gives you nothing to work on, ask for it in one or two plain sentences and say what you will do once you have it.
- **Write for someone who has never heard of this skill.** No skill names, no paths or scripts from this folder, no internal terms, and nothing about how the run was set up. A next step is one plain sentence at the end that describes the work.
- **For this skill:** Deliver the tool definition that was asked for. Encode every range, format, enum and default the source states, and add no behaviour the source doesn't state. No usage example unless asked.

### Step 1 — Intake

Ask the user to describe the function. Collect:
- **Name** (snake_case preferred; the model uses this to call the tool)
- **Purpose** (one sentence: what does this function do and when should the model call it?)
- **Parameters**: for each — name, type, what it means, whether it's required
- **Return value** (optional — for documentation purposes only; the model doesn't see it)

If they share existing code (Python, TypeScript, etc.), read the function signature and docstring directly.

### Step 2 — Write the tool definition

Produce a valid Anthropic tool definition:

```json
{
  "name": "function_name",
  "description": "One to three sentences. State what the function does, when the model should call it (the decision condition), and what it returns. Avoid vague descriptions like 'performs an operation' — the model reads this to decide whether to call the tool.",
  "input_schema": {
    "type": "object",
    "properties": {
      "param_name": {
        "type": "string",
        "description": "What this parameter controls and what values are valid. Include the unit if numeric (e.g., 'timeout in seconds, 1–300')."
      },
      "another_param": {
        "type": "integer",
        "description": "..."
      },
      "enum_param": {
        "type": "string",
        "enum": ["value_a", "value_b"],
        "description": "Which mode to use. value_a does X; value_b does Y."
      }
    },
    "required": ["param_name"]
  }
}
```

Valid JSON Schema types for Anthropic tool parameters: `"string"`, `"integer"`, `"number"`, `"boolean"`, `"array"`, `"object"`, `"null"`. Arrays need `"items"`. Objects need `"properties"` and their own `"required"`.

### Step 3 — Validate

Check the definition against these rules before outputting:
- Every parameter in `"required"` exists in `"properties"`
- No parameter has an empty `"description"` — the model needs these to fill values correctly
- The top-level `"description"` names a decision condition ("call this when X"), not just what it does
- Enum values are listed in the parameter description with a one-phrase explanation each
- Nested objects have their own `"required"` arrays

### Step 4 — Python usage snippet

Produce the Python snippet:

```python
import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "function_name",
        "description": "...",
        "input_schema": { ... }
    }
]

response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Your prompt here"}]
)

# Handle tool use
if response.stop_reason == "tool_use":
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    tool_input = tool_use_block.input  # dict matching your schema
    result = function_name(**tool_input)
    # Send result back in a follow-up message
```

### Step 5 — Multi-tool note

If the user describes multiple functions, produce one JSON array with all tools and remind them: the model chooses among all tools on each turn, so descriptions must be distinct enough to make the right call unambiguous. If two tools do similar things, the description must name the exact condition that separates them.

## Anti-patterns

- **Descriptions that restate the function name.** `"Gets the weather"` for a function named `get_weather` tells the model nothing about when to call it. Descriptions must name the decision condition.
- **Omitting the `required` array.** Without `required`, all fields are optional — the model will skip non-optional parameters, causing runtime errors.
- **Enum values without descriptions.** `"enum": ["asc", "desc"]` without explanation leaves the model guessing; it will sometimes pick the wrong value.

For the agent loop that calls these tools, see `agent-loop-design`. For orchestrating multiple agents that each expose tool schemas, see `subagent-design`.

## Quality bar

- **Descriptions are decision conditions, not function names restated.** `"Gets the weather"` is not a description — `"Returns the current temperature and conditions for a given city. Call this when the user asks about current weather, not forecasts."` is.
- **Required arrays are never omitted.** An omitted `required` array means all fields are optional — the model will skip fields the function actually needs and the call will fail at runtime.
- **Enum values always have descriptions.** `"enum": ["asc", "desc"]` without a description leaves the model guessing which to use.

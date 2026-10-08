# AI Harness

Install with `pip install -e .`, configure `.env`, and run `python -m harness.app.cli.main`.

To use Groq:

```env
MODEL_PROVIDER=groq
GROQ_API_KEY=<your-key>
GROQ_MODEL=qwen/qwen3.8-27b
```

Both Groq variables are required. Select a model available to your account that
supports function calling and JSON replies. Restart the CLI after changing `.env`.
Groq uses the existing OpenAI SDK with `https://api.groq.com/openai/v1`; no new
dependency is needed. See [Groq compatibility](https://console.groq.com/docs/openai)
and [tool use](https://console.groq.com/docs/tool-use/overview).

The existing `MODEL_PROVIDER=gemini` (or `google`) and `MODEL_PROVIDER=openai`
routes retain their existing settings and behavior.

Groq-specific tool conversion lives in `harness.mappers.groq_mapper`. The current
provider interface carries the tool catalog as system text from
`build_tools_schema`; the adapter converts that catalog into native function
definitions. Current tool arguments are required strings. If the shared catalog
format or argument types change, this conversion needs updating.

Native calls are converted to the existing `ToolCall` objects. The adapter does
not execute tools. Tool history/results keep the harness's existing text format
and original result IDs; native provider call IDs are not persisted. Replies and
summaries use the existing strict response parser. When native tools are supplied,
the response envelope is prompted and validated locally rather than using strict
JSON-schema output, which Groq does not combine with tool use.

The current orchestrator executes one batch of tools per user turn and returns
the initial response text. Automatic follow-up generation is not added by this
provider replacement.

Run tests with `python -m unittest discover -s tests/unit`.

MODEL_RESPONSE_INSTRUCTION = """
Always respond with a valid JSON object containing
exactly these three fields:

{
  "text": "",
  "tool_calls": [],
  "tool_result_summaries": []
}

Rules:
1. Put your user-facing answer in "text".

2. Put requested tool calls in "tool_calls".
   Each call must contain exactly a nonempty string "tool" and an object "arguments".

3. Summarize previously executed tool results in
   "tool_result_summaries".
   Each summary must contain exactly the original tool
   result "id" (a nonempty string) and a string "summary".

4. Never invent tool result IDs or claim that
   an unexecuted tool has completed.

5. Use empty arrays when there are no tool calls
   or summaries.

6. Return JSON only, without Markdown code fences
   or explanatory text outside the JSON.
""".strip()


# Compatibility name for callers using the previous instruction constant.
TOOL_CALL_INSTRUCTION = MODEL_RESPONSE_INSTRUCTION

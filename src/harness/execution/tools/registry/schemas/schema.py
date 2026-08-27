from harness.execution.tools.contracts.tool import Tool


def build_tools_schema(
    tools: list[Tool],
) -> str:
    if not tools:
        return "No tools are currently available."

    parts = [
        "Available tools:",
        "",
    ]

    for tool in tools:
        parts.append(
            f"Tool: {tool.name}"
        )

        parts.append(
            f"Description: {tool.description}"
        )

        if tool.arguments_schema:
            parts.append("Arguments:")

            for (
                argument_name,
                argument_description,
            ) in tool.arguments_schema.items():
                parts.append(
                    f"- {argument_name}: "
                    f"{argument_description}"
                )
        else:
            parts.append(
                "Arguments: none"
            )

        parts.append("")

    parts.extend(
        [
            "Tool call format:",
            "",
            "When you need to use a tool, "
            "respond only with valid JSON.",
            "",
            "{",
            '  "tool": "<tool_name>",',
            '  "arguments": {',
            '    "<argument_name>": "<argument_value>"',
            "  }",
            "}",
            "",
            "Do not wrap the JSON in Markdown.",
            "Do not include explanatory text "
            "before or after the JSON.",
            "Do not claim that a tool succeeded "
            "unless it was actually executed.",
        ]
    )

    return "\n".join(parts).strip()
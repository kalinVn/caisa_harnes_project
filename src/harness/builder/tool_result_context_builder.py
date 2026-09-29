from harness.domain.tool_result import ToolResult


def build_tool_results_context(
    tool_results: list[ToolResult],
) -> str:
    parts = [
        "The requested tools have finished.",
    ]

    for tool_result in tool_results:
        parts.append(
            "\n".join(
                [
                    f"Tool: {tool_result.name}",
                    f"Success: {tool_result.success}",
                    "Output:",
                    tool_result.output,
                ]
            )
        )

    parts.append(
        "Use these results to continue the task. "
        "If no more tools are needed, respond normally."
    )

    return "\n\n".join(parts)

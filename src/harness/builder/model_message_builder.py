from harness.domain.message import Message


class ModelMessageBuilder:

    def compose_model_messages(self, messages: list[Message]) -> list[Message]:

        model_messages: list[Message] = []

        tool_result_ids_to_summarize = self._add_tool_results_to_model_messages(messages,model_messages)
        

        self._add_tool_result_summary_instructions_to_model_messages(
            model_messages,
            tool_result_ids_to_summarize,
        )

        return model_messages

    def _add_tool_results_to_model_messages(
        self,
        messages: list[Message],
        model_messages: list[Message],
    ) -> list[str]:
        tool_result_ids_to_summarize: list[str] = []

        for message in messages:
            if message.tool_results:
                parts = ["The requested tools have finished."]
                for result in message.tool_results:
                    if result.summary and result.summary.strip():
                        parts.append(result.summary)
                    else:
                        tool_result_ids_to_summarize.append(result.id)
                        parts.append(
                            f"Tool result ID: {result.id}\n"
                            f"Tool: {result.name}\n"
                            f"Success: {result.success}\n"
                            f"Output:\n{result.output}"
                        )
                parts.append(
                    "Use these results to continue the task. "
                    "If no more tools are needed, respond normally."
                )
                model_messages.append(Message(role=message.role, content="\n\n".join(parts)))
            else:
                model_messages.append(message)

        return tool_result_ids_to_summarize

    def _add_tool_result_summary_instructions_to_model_messages (
        self,
        model_messages: list[Message],
        tool_result_ids_to_summarize: list[str],
    ) -> None:
        if not tool_result_ids_to_summarize:
            return

        instruction = (
            "While continuing the main task, return a concise semantic summary "
            "for each of these tool result IDs, identifying each summary by its ID: "
            + ", ".join(tool_result_ids_to_summarize)
            + ". Aim for 100 to 200 tokens per summary, at most about 250 tokens; "
            "use fewer tokens for simple results."
        )

        model_messages.append(Message(role="system", content=instruction))

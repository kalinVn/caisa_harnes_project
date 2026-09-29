from harness.app.domain.message import Message


class ModelMessageBuilder:
    def build(self, messages: list[Message]) -> list[Message]:
        model_messages = []
        unsummarized_ids = []

        for message in messages:
            if message.tool_results:
                parts = ["The requested tools have finished."]
                for result in message.tool_results:
                    if result.summary:
                        parts.append(result.summary)
                    else:
                        unsummarized_ids.append(result.id)
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

        if unsummarized_ids:
            instruction = (
                "While continuing the main task, return a concise semantic summary "
                "for each of these tool result IDs, identifying each summary by its ID: "
                + ", ".join(unsummarized_ids)
                + ". Aim for 100 to 200 tokens per summary, at most about 250 tokens; "
                "use fewer tokens for simple results."
            )
            model_messages.append(Message(role="system", content=instruction))

        return model_messages

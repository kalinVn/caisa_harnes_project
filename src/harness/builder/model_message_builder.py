from dataclasses import replace

from harness.builder.tool_result_context_builder import (
    build_tool_results_context,
    has_tool_result_summary,
)
from harness.domain.message import Message


class ModelMessageBuilder:

    def compose_model_messages(self, messages: list[Message]) -> list[Message]:
        """Prepare model context from all session messages.

        For messages with tool_results, use a summary when available or the
        full output otherwise. Collect IDs for results without summaries and
        instruct the model to summarize them. Do not modify the original
        session messages.
        """
        model_messages: list[Message] = []

        tool_result_ids_to_summarize = self._add_tool_results_to_model_messages(
            messages,
            model_messages,
        )

        self._add_tool_result_summary_instructions_to_model_messages(
            model_messages,
            tool_result_ids_to_summarize,
        )

        return model_messages

    def update_model_messages_by_tool_result_output_requests_ids(
        self,
        model_messages: list[Message],
        tool_result_output_requests: list[str],
    ) -> list[Message]:
        """Update only contexts with explicitly requested full tool outputs.

        The original session messages remain unchanged.
        """
        if not tool_result_output_requests:
            return model_messages

        updated_model_messages: list[Message] = []
        model_messages_updated = False

        for message in model_messages:

            if  not message.has_tool_results() or not message.has_requested_tool_results(tool_result_output_requests):
               
                updated_model_messages.append(message)
                continue

            updated_content = build_tool_results_context(list(message.tool_results), tool_result_output_requests)

            if updated_content == message.content:
                updated_model_messages.append(message)
                continue

            updated_model_messages.append(replace(message, content=updated_content))
            
            model_messages_updated = True

        if not model_messages_updated:
            return model_messages

        return updated_model_messages

    def _add_tool_results_to_model_messages(
        self,
        messages: list[Message],
        model_messages: list[Message],
    ) -> list[str]:
        """Add messages with processed tool results to model_messages.

        Use each ToolResult summary when available. Otherwise, use its full
        output and collect its ID for later summarization. Add messages without
        tool results unchanged and do not modify the original session messages.
        """
        tool_result_ids_to_summarize: list[str] = []

        for message in messages:
            if message.has_tool_results():
                for tool_result in message.tool_results:
                    if not has_tool_result_summary(tool_result):
                        tool_result_ids_to_summarize.append(tool_result.id)

                model_messages.append(
                    Message(
                        role=message.role,
                        content=build_tool_results_context(
                            list(message.tool_results),
                        ),
                        tool_results=message.tool_results,
                    )
                )
            else:
                model_messages.append(message)

        return tool_result_ids_to_summarize

    def _add_tool_result_summary_instructions_to_model_messages(
        self,
        model_messages: list[Message],
        tool_result_ids_to_summarize: list[str],
    ) -> None:
        """Add instructions for ToolResult IDs that need summaries.

        Use the already collected tool_result_ids_to_summarize. Do not scan the
        messages again, process tool output, or modify the session messages.
        """
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

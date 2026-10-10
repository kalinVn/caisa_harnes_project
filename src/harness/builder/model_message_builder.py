from harness.builder.tool_result_context_builder import (
    build_tool_results_context,
    has_tool_result_summary,
)
from harness.domain.message import Message


class ModelMessageBuilder:

    # Обхожда всички съобщения и подготвя контекста за модела.
    # За съобщенията с tool_results използва summary, ако съществува,
    # или пълния output, ако липсва.
    # Събира ID-тата на tool results без summary и добавя
    # инструкции към модела за тяхното обобщаване.
    # Не променя оригиналните съобщения от сесията.
    def compose_model_messages(self, messages: list[Message]) -> list[Message]:
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


    # Обхожда всички съобщения и проверява дали съдържат tool_results.
    # Ако има tool_results, обхожда всеки ToolResult.
    # Ако ToolResult има валидно summary, използва него вместо пълния output.
    # Ако няма summary, използва пълния output и добавя result.id
    # в tool_result_ids_to_summarize за последващо обобщаване.
    # Добавя обработеното съобщение в model_messages.
    # Ако съобщението няма tool_results, го добавя без промяна.
    # Не променя оригиналните съобщения от сесията.
    def _add_tool_results_to_model_messages(
        self,
        messages: list[Message],
        model_messages: list[Message],
    ) -> list[str]:
        tool_result_ids_to_summarize: list[str] = []

        for message in messages:
            if message.tool_results:
                for tool_result in message.tool_results:
                    if not has_tool_result_summary(tool_result):
                        tool_result_ids_to_summarize.append(tool_result.id)

                model_messages.append(
                    Message(
                        role=message.role,
                        content=build_tool_results_context(
                            list(message.tool_results),
                        ),
                    )
                )
            else:
                model_messages.append(message)

        return tool_result_ids_to_summarize

    # Проверява дали има ToolResult ID-та, които трябва да бъдат обобщени.
    # Използва вече събраните ID-та в tool_result_ids_to_summarize.
    # Ако има такива ID-та, добавя към model_messages инструкция,
    # която указва на модела за кои ToolResult-и трябва да генерира summary.
    # Не обхожда повторно всички съобщения и не обработва tool output.
    # Не променя оригиналните съобщения в сесията.
    def _add_tool_result_summary_instructions_to_model_messages(
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

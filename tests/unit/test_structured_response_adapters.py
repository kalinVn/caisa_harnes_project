import json
import unittest
from unittest.mock import Mock

from google.genai import types

from harness.domain.messages.message.model import Message
from harness.intelligence.models.contracts.response.instruction import MODEL_RESPONSE_INSTRUCTION
from harness.intelligence.models.parsing.response.parser import parse_model_response
from harness.intelligence.models.providers.google.client.client import GeminiClient
from harness.intelligence.models.providers.google.mapping.mapper import map_messages as google_messages
from harness.intelligence.models.providers.openai.client.client import OpenAIClient
from harness.intelligence.models.providers.openai.mapping.mapper import map_messages as openai_messages


class StructuredResponseAdaptersTest(unittest.TestCase):
    def test_gemini_requests_json_and_preserves_system_instruction(self):
        client = GeminiClient.__new__(GeminiClient)
        client._client = Mock()
        client._model = "test-model"
        client._client.models.generate_content.return_value = types.GenerateContentResponse(
            candidates=[types.Candidate(content=types.Content(parts=[types.Part.from_text(
                text='{"text":"Done","tool_calls":[],"tool_result_summaries":[]}'
            )]))]
        )
        self.assertEqual(client.generate([
            Message(role="system", content="Project instructions"),
            Message(role="user", content="Continue"),
        ]).text, "Done")
        config = client._client.models.generate_content.call_args.kwargs["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertIn("Project instructions", config.system_instruction)
        self.assertIn(MODEL_RESPONSE_INSTRUCTION, config.system_instruction)

    def test_gemini_empty_response_reports_provider_reason(self):
        client = GeminiClient.__new__(GeminiClient)
        client._client = Mock()
        client._model = "test-model"
        cases = [
            (types.GenerateContentResponse(), "no response text"),
            (types.GenerateContentResponse(prompt_feedback={"block_reason": "SAFETY"}), "SAFETY"),
            (types.GenerateContentResponse(candidates=[types.Candidate(
                finish_reason="MAX_TOKENS"
            )]), "MAX_TOKENS"),
            (types.GenerateContentResponse(candidates=[types.Candidate(
                content=types.Content(parts=[types.Part.from_text(text="  \n")])
            )]), "no response text"),
        ]
        for response, reason in cases:
            with self.subTest(reason=reason):
                client._client.models.generate_content.return_value = response
                with self.assertRaisesRegex(ValueError, reason):
                    client.generate([Message(role="user", content="Continue")])

    def test_mappers_preserve_history_and_add_one_instruction(self):
        messages = [Message(role="system", content="Project instructions"),
                    Message(role="user", content="Read file"),
                    Message(role="assistant", content='Raw tool calls:\n[{"tool":"read_file"}]'),
                    Message(role="user", content="Tool result ID: original-id\nOutput:\ncontents")]
        contents, instruction = google_messages(messages)
        self.assertEqual(instruction.count(MODEL_RESPONSE_INSTRUCTION), 1)
        self.assertIn("Project instructions", instruction)
        self.assertEqual([c.role for c in contents], ["user", "model", "user"])
        self.assertEqual([c.parts[0].text for c in contents], [m.content for m in messages[1:]])
        mapped = openai_messages(messages)
        self.assertEqual(mapped[:-1], [{"role": m.role, "content": m.content} for m in messages])
        self.assertEqual(mapped[-1], {"role": "system", "content": MODEL_RESPONSE_INSTRUCTION})

    def test_adapters_return_contract_and_propagate_invalid_responses(self):
        raw = json.dumps(dict(text="", tool_calls=[dict(tool="read_file", arguments={"path": "a"}),
                                                   dict(tool="read_file", arguments={"path": "b"})],
                              tool_result_summaries=[dict(id="original-id", summary="Read previous file.")]))
        for cls in (GeminiClient, OpenAIClient):
            with self.subTest(provider=cls.__name__):
                client = cls.__new__(cls)
                client._client = Mock()
                client._model = "test-model"
                endpoint = (client._client.models.generate_content if cls is GeminiClient
                            else client._client.responses.create)
                endpoint.return_value = Mock(text=raw, output_text=raw)
                self.assertEqual(client.generate([Message(role="user", content="Continue")]),
                                 parse_model_response(raw))
                endpoint.return_value = Mock(text="invalid", output_text="invalid")
                with self.assertRaises(ValueError):
                    client.generate([Message(role="user", content="Continue")])
                endpoint.reset_mock()
                with self.assertRaises(ValueError):
                    client.generate([])
                endpoint.assert_not_called()

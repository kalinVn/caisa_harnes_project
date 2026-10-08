import json
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx
from openai import APIConnectionError, APIStatusError, RateLimitError

from harness.builder.model_message_builder import ModelMessageBuilder
from harness.builder.tools_schema_builder import build_tools_schema
from harness.domain.message import Message
from harness.domain.tool_call import ToolCall
from harness.domain.tool_result import ToolResult
from harness.factory.model_client_factory import create_model_client
from harness.mappers.groq_mapper import map_messages
from harness.models.errors import ModelConnectionError, ModelRateLimitError
from harness.models.response import ModelResponse
from harness.models.tool_result_summary import ToolResultSummary
from harness.providers.groq_client import GroqClient
from harness.tools.register_tools import register_tools
from harness.tools.tool_registry import ToolRegistry


def envelope(text='', summaries=None):
    return json.dumps(dict(text=text, tool_calls=[], tool_result_summaries=summaries or []))


def tool_call(name='read_file', arguments='{"path":"README.md"}'):
    return SimpleNamespace(type='function', id='groq-call-id',
                           function=SimpleNamespace(name=name, arguments=arguments))


class GroqProviderTest(unittest.TestCase):
    def setUp(self):
        env = patch.dict('os.environ', {'GROQ_API_KEY': 'test-key', 'GROQ_MODEL': 'test-model'})
        env.start()
        self.addCleanup(env.stop)
        sdk = patch('harness.providers.groq_client.OpenAI')
        self.sdk = sdk.start()
        self.addCleanup(sdk.stop)
        self.client = GroqClient()
        self.create = self.sdk.return_value.chat.completions.create
        registry = ToolRegistry()
        register_tools(registry)
        self.tools = registry.list_tools()
        self.messages = [Message(role='system', content=build_tools_schema(self.tools)),
                         Message(role='user', content='hi')]

    def reply(self, content=None, calls=None, finish=None):
        self.create.return_value = SimpleNamespace(choices=[SimpleNamespace(
            finish_reason=finish or ('tool_calls' if calls else 'stop'),
            message=SimpleNamespace(content=content, tool_calls=calls),
        )])
        return self.client.generate(self.messages)

    def test_configuration_and_greeting(self):
        self.sdk.assert_called_once_with(api_key='test-key', base_url='https://api.groq.com/openai/v1',
                                         timeout=60.0, max_retries=2)
        self.assertEqual(self.reply(envelope('Hello')), ModelResponse(text='Hello'))
        self.assertEqual(self.create.call_args.kwargs['model'], 'test-model')
        self.assertEqual(self.create.call_args.kwargs['tool_choice'], 'auto')
        self.assertNotIn('response_format', self.create.call_args.kwargs)

    def test_required_environment(self):
        for name in ('GROQ_API_KEY', 'GROQ_MODEL'):
            with self.subTest(name=name), patch.dict('os.environ', {name: ' '}):
                with self.assertRaisesRegex(ValueError, name):
                    GroqClient()

    def test_existing_tool_catalog_is_converted_without_mutating_messages(self):
        original = deepcopy(self.messages)
        mapped, definitions = map_messages(self.messages)
        self.assertEqual(self.messages, original)
        self.assertEqual(mapped[1], {'role': 'user', 'content': 'hi'})
        self.assertNotIn('Tool call format:', mapped[0]['content'])
        self.assertEqual(len(definitions), len(self.tools))
        for tool, definition in zip(self.tools, definitions):
            self.assertEqual(definition, {'type': 'function', 'function': {
                'name': tool.name, 'description': tool.description, 'parameters': {
                    'type': 'object', 'properties': {
                        k: {'type': 'string', 'description': v} for k, v in tool.arguments_schema.items()
                    }, 'required': list(tool.arguments_schema), 'additionalProperties': False,
                },
            }})

    def test_no_argument_tool_and_user_text_do_not_create_extra_tools(self):
        no_arguments = Mock(name='tool')
        no_arguments.name = 'status'
        no_arguments.description = 'Shows status.'
        no_arguments.arguments_schema = {}
        catalog = build_tools_schema([no_arguments])
        _, tools = map_messages([Message(role='system', content=catalog),
                                 Message(role='user', content=build_tools_schema(self.tools))])
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]['function']['parameters']['properties'], {})
        self.assertEqual(tools[0]['function']['parameters']['required'], [])

    def test_native_parallel_calls_and_summaries(self):
        response = self.reply(envelope('Reading', [{'id': 'original-id', 'summary': 'Earlier result'}]),
                              [tool_call(), tool_call('bash', '{"command":"pwd"}')])
        self.assertEqual(response, ModelResponse('Reading', [
            ToolCall('read_file', {'path': 'README.md'}), ToolCall('bash', {'command': 'pwd'})
        ], [ToolResultSummary('original-id', 'Earlier result')]))
        self.assertEqual(self.reply(calls=[tool_call()]).tool_calls,
                         [ToolCall('read_file', {'path': 'README.md'})])

    def test_rejects_malformed_and_unavailable_native_calls(self):
        invalid = [tool_call('unknown'), tool_call(arguments='[]'), tool_call(arguments='{'),
                   tool_call(arguments='{"path":"a","path":"b"}'),
                   tool_call(arguments='{"value":NaN}'), tool_call(arguments='{"value":1e999}'),
                   tool_call(arguments='{}},{"tool":"unknown","arguments":{}'),
                   tool_call(arguments=None)]
        for call in invalid:
            with self.subTest(call=call), self.assertRaisesRegex(ValueError, 'invalid model response'):
                self.reply(calls=[call])

    def test_invalid_empty_truncated_and_ambiguous_responses(self):
        for content in (None, '', 'hello', '{}', '{"text":"Hello"}',
                        '{"text":"","tool_calls":[{"tool":"bash","arguments":{}}],"tool_result_summaries":[]}'):
            with self.subTest(content=content), self.assertRaises(ValueError):
                self.reply(content)
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.reply(envelope('Partial'), finish='length')
        self.create.return_value = SimpleNamespace(choices=[])
        with self.assertRaisesRegex(ValueError, 'no response choices'):
            self.client.generate(self.messages)

    def test_result_history_and_original_ids_survive_next_turn(self):
        result = ToolResult(name='read_file', output='Example contents')
        self.messages += [Message(role='assistant', content='Raw tool calls:\n[]'),
                          Message(role='user', content='', tool_results=(result,))]
        self.messages = ModelMessageBuilder().build(self.messages)
        response = self.reply(envelope('Done', [{'id': result.id, 'summary': 'Read contents'}]))
        self.assertEqual(response.tool_result_summaries[0].id, result.id)
        sent = self.create.call_args.kwargs['messages']
        self.assertTrue(any(result.id in m['content'] and 'Example contents' in m['content'] for m in sent))
        self.assertEqual([m['role'] for m in sent[:-1]], [m.role for m in self.messages])

    def test_no_tools_and_empty_conversation(self):
        self.messages = [Message(role='user', content='Hello')]
        self.reply(envelope('Hello'))
        self.assertNotIn('tools', self.create.call_args.kwargs)
        self.assertEqual(self.create.call_args.kwargs['response_format'], {'type': 'json_object'})
        self.create.reset_mock()
        for messages in ([], [Message(role='system', content='Instructions')]):
            with self.assertRaisesRegex(ValueError, 'empty conversation'):
                self.client.generate(messages)
        self.create.assert_not_called()

    def test_provider_errors_use_existing_application_errors(self):
        request = httpx.Request('POST', 'https://api.groq.com/openai/v1/chat/completions')
        cases = [(APIConnectionError(request=request), ModelConnectionError)]
        for code in (400, 401, 404, 429, 500):
            error_type = RateLimitError if code == 429 else APIStatusError
            cases.append((error_type('failure', response=httpx.Response(code, request=request), body=None),
                          ModelRateLimitError if code == 429 else ModelConnectionError))
        for error, expected in cases:
            self.create.side_effect = error
            with self.subTest(error=error), self.assertRaises(expected):
                self.client.generate(self.messages)

    def test_factory_preserves_existing_routes_and_adds_groq(self):
        for name, target in (('groq', 'GroqClient'), ('gemini', 'GeminiClient'),
                             ('google', 'GeminiClient'), ('openai', 'OpenAIClient')):
            with patch.dict('os.environ', {'MODEL_PROVIDER': name}), \
                 patch('harness.factory.model_client_factory.' + target) as provider:
                self.assertIs(create_model_client(), provider.return_value)
                provider.assert_called_once_with()
        for name in ('ollama', 'local_qwen2.5:1.5b'):
            with patch.dict('os.environ', {'MODEL_PROVIDER': name}), \
                 self.assertRaisesRegex(ValueError, 'Unsupported MODEL_PROVIDER'):
                create_model_client()

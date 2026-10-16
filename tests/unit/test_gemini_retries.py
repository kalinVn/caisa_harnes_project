import io
import unittest
from unittest.mock import patch

import httpx
from google.genai.errors import ClientError, ServerError

from harness.app.cli.main import main
from harness.domain.message import Message
from harness.models.errors import (
    ModelConnectionError,
    ModelRateLimitError,
)
from harness.providers.google_client import GeminiClient


class GeminiRetriesTest(unittest.TestCase):
    def setUp(self):
        env = patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"})
        env.start()
        self.addCleanup(env.stop)
        self.client = GeminiClient()
        self.addCleanup(self.client._client.close)
        self.messages = [Message(role="user", content="Hello")]

    def response(self, code):
        if code == 200:
            body = {"candidates": [{"content": {"role": "model", "parts": [{
                "text": '{"text":"Done","tool_calls":[],"tool_result_summaries":[]}'
            }]}}]}
        else:
            body = {"error": {"code": code, "message": "Provider failure"}}
        return httpx.Response(code, json=body, request=httpx.Request("POST", "https://example.test"))

    @patch("tenacity.nap.time.sleep")
    @patch("httpx.Client.send")
    def test_transient_failure_recovers(self, send, sleep):
        send.side_effect = [self.response(503), self.response(503), self.response(200)]
        self.assertEqual(self.client.generate(self.messages).text, "Done")
        self.assertEqual(send.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertGreaterEqual(sleep.call_args_list[0].args[0], 1)
        self.assertGreaterEqual(sleep.call_args_list[1].args[0], 2)

    @patch("tenacity.nap.time.sleep")
    @patch("httpx.Client.send")
    def test_persistent_failure_has_bounded_retries(self, send, sleep):
        send.side_effect = lambda *args, **kwargs: self.response(503)
        with self.assertRaisesRegex(ModelConnectionError, "high demand") as caught:
            self.client.generate(self.messages)
        self.assertIsInstance(caught.exception.__cause__, ServerError)
        self.assertEqual(send.call_count, 4)
        self.assertEqual(sleep.call_count, 3)

    @patch("tenacity.nap.time.sleep")
    @patch("httpx.Client.send")
    def test_client_errors_are_not_retried(self, send, sleep):
        for code, expected in [(400, ClientError), (401, ClientError), (429, ModelRateLimitError)]:
            with self.subTest(code=code):
                send.reset_mock()
                send.return_value = self.response(code)
                with self.assertRaises(expected):
                    self.client.generate(self.messages)
                self.assertEqual(send.call_count, 1)
        sleep.assert_not_called()

    def test_cli_stays_open_after_unavailable_error(self):
        with (
            patch("harness.app.cli.main.create_model_client"),
            patch("harness.app.cli.main.MainOrchestrator") as runner,
            patch("harness.app.cli.main.read_input",
                  side_effect=["Hello", "Try again", "exit"]),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            runner.return_value.handle.side_effect = [
                ModelConnectionError("Gemini is temporarily unavailable."), "Done",
            ]
            main()
        self.assertEqual(runner.return_value.handle.call_count, 2)
        self.assertIn("Gemini is temporarily unavailable.", stdout.getvalue())
        self.assertIn("Harness > Done", stdout.getvalue())
        self.assertIn("AI Harness stopped.", stdout.getvalue())

    @patch("tenacity.nap.time.sleep")
    @patch("httpx.Client.send")
    def test_missing_model_reports_configuration_error_without_retry(self, send, sleep):
        self.client._model = "djemini"
        send.return_value = self.response(404)
        with self.assertRaisesRegex(ModelConnectionError, "djemini.*GEMINI_MODEL") as caught:
            self.client.generate(self.messages)
        self.assertIsInstance(caught.exception.__cause__, ClientError)
        send.assert_called_once()
        sleep.assert_not_called()

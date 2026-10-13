import unittest

from harness.parser.command_response_parser import parse_command_response
from harness.validators.command_response_validator import CommandResponseValidator


class CommandResponseValidatorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = CommandResponseValidator()

    def test_returns_true_for_valid_json(self):
        response = '{"answer": "Done", "command_summary": "Created the file."}'

        self.assertTrue(self.validator.validate(response))

    def test_returns_false_for_invalid_json(self):
        self.assertFalse(self.validator.validate('{"answer": "Done"'))

    def test_returns_false_for_empty_response(self):
        self.assertFalse(self.validator.validate(""))

    def test_returns_false_when_answer_is_missing(self):
        response = '{"command_summary": "Created the file."}'

        self.assertFalse(self.validator.validate(response))

    def test_returns_false_when_command_summary_is_missing(self):
        response = '{"answer": "Done"}'

        self.assertFalse(self.validator.validate(response))

    def test_returns_false_for_incorrect_field_types(self):
        responses = (
            '{"answer": 1, "command_summary": "Created the file."}',
            '{"answer": "Done", "command_summary": 1}',
        )

        for response in responses:
            with self.subTest(response=response):
                self.assertFalse(self.validator.validate(response))

    def test_returns_false_for_empty_or_whitespace_only_summary(self):
        for command_summary in ("", "   "):
            with self.subTest(command_summary=command_summary):
                response = (
                    '{"answer": "Done", '
                    f'"command_summary": "{command_summary}"}}'
                )
                self.assertFalse(self.validator.validate(response))

    def test_returns_false_when_json_is_not_an_object(self):
        self.assertFalse(self.validator.validate("[]"))


class CommandResponseParserTest(unittest.TestCase):
    def test_returns_tuple_for_valid_input_and_strips_summary(self):
        response = '{"answer": "Done", "command_summary": "  Created the file.  "}'

        self.assertEqual(
            parse_command_response(response),
            ("Done", "Created the file."),
        )

    def test_returns_none_for_invalid_input(self):
        for response in ('{"answer": "Done"', '{"answer": "Done"}'):
            with self.subTest(response=response):
                self.assertIsNone(parse_command_response(response))


if __name__ == "__main__":
    unittest.main()

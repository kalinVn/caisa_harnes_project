import io
import unittest
from unittest.mock import patch

from harness.app.cli.main import main


class CliMainTest(unittest.TestCase):
    def test_main_processes_messages_until_exit(self) -> None:
        with (
            patch("harness.app.cli.main.load_dotenv"),
            patch("harness.app.cli.main.create_model_client") as create_model_client,
            patch("harness.app.cli.main.Runner") as runner,
            patch(
                "harness.app.cli.main.read_input",
                side_effect=["hello", "exit"],
            ),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            runner.return_value.handle.return_value = "Received: hello"
            main()

        runner.assert_called_once_with(model_client=create_model_client.return_value)
        runner.return_value.handle.assert_called_once()
        self.assertEqual(runner.return_value.handle.call_args.args[0].message, "hello")
        self.assertEqual(
            stdout.getvalue(),
            "AI Harness started.\n"
            "Type 'exit' to stop.\n\n"
            "\nHarness > Received: hello\n\n"
            "AI Harness stopped.\n",
        )


if __name__ == "__main__":
    unittest.main()

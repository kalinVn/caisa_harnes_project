import io
import unittest
from unittest.mock import patch

from harness.application.entrypoints.cli.main import main


class CliMainTest(unittest.TestCase):
    def test_main_processes_messages_until_exit(self) -> None:
        with (
            patch(
                "harness.application.entrypoints.cli.main.read_input",
                side_effect=["hello", "exit"],
            ),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            main()

        self.assertEqual(
            stdout.getvalue(),
            "AI Harness started.\n"
            "Type 'exit' to stop.\n\n"
            "Received: hello\n"
            "AI Harness stopped.\n",
        )


if __name__ == "__main__":
    unittest.main()

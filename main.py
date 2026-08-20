import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from harness.application.entrypoints.cli.input.reader import read_input


def main() -> None:
    """Start the AI Harness."""
    print("AI Harness started.")
    print("Type 'exit' to stop.\n")

    while True:
        user_message = read_input()

        if user_message.lower() == "exit":
            print("AI Harness stopped.")
            break

        print(f"Received: {user_message}")


if __name__ == "__main__":
    main()

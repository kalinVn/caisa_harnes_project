from dotenv import load_dotenv

from harness.app.cli.reader import read_input
from harness.app.models.request import Request
from harness.app.orchestrator import Runner
from harness.app.models.errors import (
    ModelConnectionError,
    ModelRateLimitError,
)
from harness.intelligence.models.routing.selector.selector import create_model_client


def main() -> None:
    load_dotenv()

    print("AI Harness started.")
    print("Type 'exit' to stop.\n")

    model_client = create_model_client()
    runner = Runner(model_client=model_client)

    while True:
        user_message = read_input()

        if user_message.lower() == "exit":
            print("AI Harness stopped.")
            break

        request = Request.create(user_message)

        try:
            response = runner.handle(request)
        except (
            ModelConnectionError,
            ModelRateLimitError,
        ) as error:
            print(f"\nHarness > {error}\n")
            continue

        print(f"\nHarness > {response}\n")


if __name__ == "__main__":
    main()
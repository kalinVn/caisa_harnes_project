from dotenv import load_dotenv

from harness.application.entrypoints.cli.input.reader import read_input
from harness.application.orchestration.engine.runner.runner import Runner
from harness.application.request.model.request import Request
from harness.intelligence.models.routing.selector.selector import (
    create_model_client,
)


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

        response = runner.handle(request)

        print(f"\nHarness > {response}\n")
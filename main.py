from harness.application.entrypoints.cli.input.reader import read_input
from harness.application.request.model.request import Request


def main() -> None:
    print("AI Harness started.")
    print("Type 'exit' to stop.\n")

    while True:
        user_message = read_input()

        if user_message.lower() == "exit":
            print("AI Harness stopped.")
            break

        request = Request.create(user_message)

        print(f"Message: {request.message}")
        print(f"Session ID: {request.session_id}")
        print(f"Created at: {request.created_at}")


if __name__ == "__main__":
    main()
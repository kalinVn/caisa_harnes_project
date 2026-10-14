from pathlib import Path
import sys


def run() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

    from harness.app.cli.main import main

    main()


if __name__ == "__main__":
    run()

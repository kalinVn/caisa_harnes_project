from pathlib import Path


class ReadFileTool:
    def execute(self, path: Path) -> str:
        if not path.is_file():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        return path.read_text(
            encoding="utf-8"
        )
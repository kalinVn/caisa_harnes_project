from pathlib import Path


class CAISAPromptLoader:
    def __init__(self, project_root: Path | None = None) -> None:
        self._project_root = project_root or Path.cwd()

    def load(self) -> str:
        prompt_path = self._project_root / ".caisa" / "CAISA.md"

        if not prompt_path.exists():
            return ""

        return prompt_path.read_text(
            encoding="utf-8"
        ).strip()
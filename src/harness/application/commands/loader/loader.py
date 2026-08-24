# src/harness/application/commands/loader/loader.py

from harness.domain.commands.model import Command


class CommandLoader:
    def load(self, content: str) -> Command:
        sections = self._parse_sections(content)

        name = sections.get("Name")
        description = sections.get("Description")

        if not name:
            raise ValueError(
                "Command must contain a '# Name' section."
            )

        if not description:
            raise ValueError(
                "Command must contain a '# Description' section."
            )

        extra_sections = {
            key: value
            for key, value in sections.items()
            if key not in {"Name", "Description"}
        }

        return Command(
            name=name,
            description=description,
            sections=extra_sections,
        )

    def _parse_sections(
        self,
        content: str,
    ) -> dict[str, str]:
        sections: dict[str, str] = {}

        current_section: str | None = None
        current_lines: list[str] = []

        def save_current_section() -> None:
            if current_section is None:
                return

            sections[current_section] = (
                "\n".join(current_lines).strip()
            )

        for line in content.splitlines():
            if line.startswith("# "):
                save_current_section()

                current_section = line[2:].strip()
                current_lines = []
                continue

            if current_section is not None:
                current_lines.append(line)

        save_current_section()

        return sections

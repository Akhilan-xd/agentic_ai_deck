import sys
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_links import connect_topics_in_vault, merge_existing_note, safe_title, vault_root

ALLOWED_FOLDERS = {"papers", "methods", "datasets", "metrics", "studies"}


class SaveNoteInput(BaseModel):
    folder: str = Field(..., description="One of: papers, methods, datasets, metrics, studies")
    title: str = Field(
        ...,
        description=(
            "Note title. This becomes the filename and the wikilink target. "
            "Reuse an existing title when this is the same method, dataset item, metric, or topic."
        ),
    )
    body: str = Field(
        ...,
        description=(
            "Full markdown, including YAML frontmatter with type, topics, and "
            'source: "[[Paper Title]]". topics lists shared subject names.'
        ),
    )


class SaveObsidianNoteTool(BaseTool):
    name: str = "Save Obsidian Note"
    description: str = (
        "Write one markdown note into the Obsidian vault. "
        "If a non-paper note with this title already exists, keep it and attach the new paper instead of replacing it. "
        "Notes that list the same topic are then linked in the graph."
    )
    args_schema: Type[BaseModel] = SaveNoteInput

    def _run(self, folder: str, title: str, body: str) -> str:
        if folder not in ALLOWED_FOLDERS:
            return f"Folder must be one of: {', '.join(sorted(ALLOWED_FOLDERS))}"

        cleaned = safe_title(title)
        if not cleaned:
            return "Title is empty."

        vault = vault_root()
        path = (vault / folder / f"{cleaned}.md").resolve()
        if path.parent != (vault / folder).resolve():
            return "Refusing to write outside the vault folder."

        path.parent.mkdir(parents=True, exist_ok=True)
        incoming = body.rstrip() + "\n"
        if path.exists() and folder != "papers":
            path.write_text(
                merge_existing_note(path.read_text(encoding="utf-8"), incoming),
                encoding="utf-8",
            )
            action = "Linked existing"
        else:
            path.write_text(incoming, encoding="utf-8")
            action = "Wrote"

        connect_topics_in_vault(vault)
        return f"{action} {folder}/{cleaned}.md"

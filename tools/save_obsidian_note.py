from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

ALLOWED_FOLDERS = {"papers", "methods", "datasets", "metrics", "studies"}


class SaveNoteInput(BaseModel):
    folder: str = Field(..., description="One of: papers, methods, datasets, metrics, studies")
    title: str = Field(..., description="Note title. This becomes the filename and the wikilink target.")
    body: str = Field(..., description="Full markdown for the note, including YAML frontmatter.")


class SaveObsidianNoteTool(BaseTool):
    name: str = "Save Obsidian Note"
    description: str = "Write one markdown note into the Obsidian vault."
    args_schema: Type[BaseModel] = SaveNoteInput

    def _run(self, folder: str, title: str, body: str) -> str:
        if folder not in ALLOWED_FOLDERS:
            return f"Folder must be one of: {', '.join(sorted(ALLOWED_FOLDERS))}"

        safe_title = "".join(ch for ch in title if ch not in '\\/:*?"<>|').strip()
        if not safe_title:
            return "Title is empty."

        vault = Path("obsidian_vault").resolve()
        path = (vault / folder / f"{safe_title}.md").resolve()
        if path.parent != (vault / folder).resolve():
            return "Refusing to write outside the vault folder."

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body.rstrip() + "\n", encoding="utf-8")
        return f"Wrote {folder}/{safe_title}.md"
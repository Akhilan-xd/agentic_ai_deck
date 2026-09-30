import sys
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vault_links import list_notes


class ListVaultInput(BaseModel):
    query: str = Field(
        default="",
        description="Optional substring. Leave empty to list every note title already in the vault.",
    )


class ListVaultNotesTool(BaseTool):
    name: str = "List Vault Notes"
    description: str = (
        "List note titles already in the Obsidian vault. "
        "Reuse one of these titles when a new paper discusses the same method, dataset, metric, or topic."
    )
    args_schema: Type[BaseModel] = ListVaultInput

    def _run(self, query: str = "") -> str:
        return list_notes(query=query)

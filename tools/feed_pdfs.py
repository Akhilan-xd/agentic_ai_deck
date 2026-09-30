import re
from pathlib import Path
from typing import Type

from crewai.project.json_loader import load_jsonc_file
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
PAPER_CREW = ROOT / "paper_crew.jsonc"
CREW_CONFIG = ROOT / "crew.jsonc"


class FeedPdfsInput(BaseModel):
    pdf_filenames: str = Field(
        ...,
        description="Every PDF file name to process, for example ['2505.00527v2.pdf', '2406.09767v3.pdf']",
    )


def filenames_in(text: str) -> list[str]:
    found = re.findall(r"[A-Za-z0-9._-]+\.pdf", text, flags=re.IGNORECASE)
    names: list[str] = []
    for name in found:
        base = Path(name).name
        if base not in names:
            names.append(base)
    return names


def configured_filenames() -> list[str]:
    data = load_jsonc_file(CREW_CONFIG)
    raw = data.get("inputs", {}).get("pdf_filenames", [])
    if isinstance(raw, str):
        return filenames_in(raw)
    if isinstance(raw, list):
        names: list[str] = []
        for item in raw:
            for name in filenames_in(str(item)):
                if name not in names:
                    names.append(name)
        return names
    return []


def resolve_filenames(passed: str) -> list[str]:
    """Use the crew.jsonc list so a partial tool call cannot drop a PDF."""
    configured = configured_filenames()
    if configured:
        return configured
    return filenames_in(passed)


class FeedPdfsTool(BaseTool):
    name: str = "Feed PDFs"
    description: str = (
        "Run extraction, library notes, and publishing for every PDF in the list. "
        "Pass the full list. Each file is handled on its own."
    )
    args_schema: Type[BaseModel] = FeedPdfsInput

    def _run(self, pdf_filenames: str) -> str:
        names = resolve_filenames(pdf_filenames)
        if not names:
            return "No PDF filenames were given. Set inputs.pdf_filenames in crew.jsonc."

        from crewai.project.crew_loader import load_crew

        knowledge = Path("knowledge").resolve()
        reports: list[str] = []
        for name in names:
            path = (knowledge / name).resolve()
            if path.parent != knowledge or not path.is_file():
                reports.append(f"{name}: missing from knowledge/")
                continue
            try:
                crew, _ = load_crew(PAPER_CREW)
                result = crew.kickoff(inputs={"pdf_filename": name})
                raw = getattr(result, "raw", None) or str(result)
                reports.append(f"{name}: extracted and published\n{raw.strip()}")
            except Exception as exc:
                reports.append(f"{name}: failed ({exc})")

        return "\n\n".join(reports)

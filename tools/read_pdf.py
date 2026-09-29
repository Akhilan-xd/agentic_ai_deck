from pathlib import Path
from typing import Type

import fitz
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ReadPdfInput(BaseModel):
    pdf_filename: str = Field(
        ...,
        description="PDF file name inside the knowledge folder, for example 2505.00527v2.pdf",
    )


class ReadPdfTool(BaseTool):
    name: str = "Read PDF"
    description: str = "Read a PDF from the knowledge folder and return its text."
    args_schema: Type[BaseModel] = ReadPdfInput

    def _run(self, pdf_filename: str) -> str:
        knowledge = Path("knowledge").resolve()
        path = (knowledge / Path(pdf_filename).name).resolve()
        if path.parent != knowledge or not path.is_file():
            return f"PDF not found in knowledge/: {pdf_filename}"

        doc = fitz.open(path)
        pages = [page.get_text() for page in doc]
        return "\n\n".join(pages)
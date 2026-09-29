"""Example tool. Copy this file when you add your own."""

from crewai.tools import BaseTool


class WhitespaceTool(BaseTool):
    name: str = "whitespace_tool"
    description: str = "Count the whitespace in a piece of text. Input is the text to count."

    def _run(self, text: str) -> str:
        return str(len(text.strip()))

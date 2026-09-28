"""Example tool. Copy this file when you add your own."""

from crewai.tools import BaseTool


class WordCountTool(BaseTool):
    name: str = "word_count"
    description: str = "Count the words in a piece of text. Input is the text to count."

    def _run(self, text: str) -> str:
        return str(len(text.split()))

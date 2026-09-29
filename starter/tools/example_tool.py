# counts the words in some text

from crewai.tools import BaseTool


class WordCountTool(BaseTool):
    name: str = "word_count"
    description: str = "Count the words in a piece of text. Input is the text to count."

    def _run(self, text: str) -> str:
        words = text.split()
        return str(len(words))

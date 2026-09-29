# counts spaces, tabs, and newlines

from crewai.tools import BaseTool


class WhitespaceTool(BaseTool):
    name: str = "whitespace_tool"
    description: str = "Count the whitespace in a piece of text. Input is the text to count."

    def _run(self, text: str) -> str:
        count = 0
        for letter in text:
            if letter == " " or letter == "\n" or letter == "\t":
                count = count + 1
        return str(count)

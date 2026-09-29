# chat that answers in a few sentences, then reads the answer out loud
#
#   python -m starter.qa
#   python -m starter.qa "what should I read to learn stoicism?"

import os
import sys

from crewai import Agent
from dotenv import load_dotenv

from starter.llm import local_llm
from starter.main import check_ollama
from starter.tools.reading import ReadingLookupTool, lookup_reading
from starter.tools.speech import SpeakTool, arm_script, last_spoken, speak_aloud

source_words = [
    "book",
    "read",
    "buy",
    "purchase",
    "website",
    "site",
    "link",
    "citation",
    "cite",
    "source",
    "where can i",
    "recommend",
    "isbn",
    "article",
    "learn more",
]

partner_story = """
You talk like a friend. Keep it short and plain.
Do not use outlines or headers. Do not start with "Certainly" or "Great question".
If the question is vague, answer the likely meaning. If you are unsure, say so.

Only use titles and URLs from reading_lookup or from a "Live lookup" note.
Share at most two websites and two books.
For a book, name the author and give the read link and the buy link.
Never write a URL that was not in those results.
If there are no results, say you could not check a live link.
""".strip()

narrator_story = """
You read the answer aloud.
Do not rewrite it or add a greeting.
Call the speak tool once. Then reply with exactly: Spoken.
""".strip()


def verbose():
    value = os.getenv("QA_VERBOSE", "false").strip().lower()
    return value in ["1", "true", "yes"]


def build_agent():
    return Agent(
        role="Conversation partner",
        goal="Answer in a few sentences, and point to a real site or book when that helps",
        backstory=partner_story,
        llm=local_llm(),
        tools=[ReadingLookupTool()],
        verbose=verbose(),
        max_iter=5,
    )


def build_narrator():
    return Agent(
        role="Narrator",
        goal="Read the answer aloud by calling the speak tool once",
        backstory=narrator_story,
        llm=local_llm(),
        tools=[SpeakTool()],
        verbose=verbose(),
        max_iter=3,
    )


def wants_sources(question):
    text = question.lower()
    for word in source_words:
        if word in text:
            return True
    return False


def message_for_agent(question):
    if not wants_sources(question):
        return question
    notes = lookup_reading(question)
    return (
        question
        + "\n\nLive lookup results. Use these titles and links only. "
        + "Do not call reading_lookup again for this turn.\n"
        + notes
    )


def narrate(narrator, reply):
    arm_script(reply)
    result = narrator.kickoff(
        messages=[
            {
                "role": "user",
                "content": "Call the speak tool once so this answer is read aloud:\n\n" + reply,
            }
        ]
    )
    if last_spoken() == "":
        speak_aloud(reply)
    text = result.raw or ""
    return text.strip()


def answer(agent, question, history):
    messages = history + [{"role": "user", "content": message_for_agent(question)}]
    result = agent.kickoff(messages=messages)
    text = result.raw or ""
    return text.strip()


def remember(history, question, reply):
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": reply})
    while len(history) > 12:
        history.pop(0)


def main():
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if provider == "ollama":
        check_ollama()
    else:
        print("Using OpenAI-compatible model: " + os.getenv("OPENAI_MODEL_NAME", "local-model"))

    partner = build_agent()
    narrator = build_narrator()

    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:]).strip()
        reply = answer(partner, question, [])
        print(reply)
        print(narrate(narrator, reply))
        return

    history = []
    print("Ask anything. I will keep it short, and I can point you to something to read or buy.")
    print("The narrator reads each answer aloud. Type exit to stop.")
    print()
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in ["exit", "quit"]:
            break
        if question == "":
            continue
        reply = answer(partner, question, history)
        print()
        print(reply)
        print()
        print(narrate(narrator, reply))
        print()
        remember(history, question, reply)


if __name__ == "__main__":
    main()

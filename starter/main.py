# run the starter crew

import os
import sys

from dotenv import load_dotenv

from starter.crew import StarterCrew
from starter.ollama_server import find_server, has_model, installed_models, remember_base_url


def check_ollama():
    found = find_server()
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip()
    if found is None:
        print("Ollama is not running.")
        print("From the project folder run: python -m starter.setup")
        raise SystemExit(1)

    remember_base_url(found)
    names = installed_models(found) or []
    if len(names) > 0 and not has_model(names, model):
        print("Ollama is running at " + found + ", but " + model + " is not installed.")
        print("Installed models: " + ", ".join(names))
        print("Run: python -m starter.setup")
        raise SystemExit(1)

    print("Using Ollama at " + found + "  model: " + model)


def main():
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if len(sys.argv) > 1:
        topic = sys.argv[1]
    else:
        topic = os.getenv("TOPIC", "local LLM agents with CrewAI")

    if provider == "ollama":
        check_ollama()
    else:
        print("Using OpenAI-compatible model: " + os.getenv("OPENAI_MODEL_NAME", "local-model"))

    print("Topic: " + topic)
    print()
    result = StarterCrew().crew().kickoff(inputs={"topic": topic})
    print()
    print("----- Brief -----")
    print()
    print(result)


if __name__ == "__main__":
    main()

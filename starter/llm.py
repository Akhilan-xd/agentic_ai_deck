# builds the model from the .env file

import os

from crewai import LLM


def local_llm():
    provider = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    if provider == "openai_compatible":
        model = os.getenv("OPENAI_MODEL_NAME", "local-model").strip()
        if not model.startswith("openai/"):
            model = "openai/" + model
        return LLM(
            model=model,
            base_url=os.getenv("OPENAI_API_BASE", "http://localhost:1234/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "local"),
            temperature=temperature,
        )

    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip()
    if not model.startswith("ollama/"):
        model = "ollama/" + model
    return LLM(
        model=model,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
    )

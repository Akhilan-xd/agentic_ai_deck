"""Start Ollama and download the model named in .env.

Run this once before the crew:

    python -m starter.setup
"""

import os

from dotenv import load_dotenv

from starter.ollama_server import (
    ROOT,
    ensure_server,
    has_model,
    installed_models,
    pull_model,
)


def main() -> None:
    load_dotenv(ROOT / ".env")
    base_url = ensure_server()
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b").strip()
    names = installed_models(base_url) or []
    if has_model(names, model):
        print(f"{model} is already installed at {base_url}")
    else:
        pull_model(base_url, model)
    print(f"Ready. Server: {base_url}  Model: {model}")
    print("Next: python -m starter.main")


if __name__ == "__main__":
    main()

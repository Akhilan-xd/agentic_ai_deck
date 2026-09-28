"""Find, start, and pull from the local Ollama server.

The `ollama` command uses OLLAMA_HOST. A shell, bashrc, or old project
often leaves that on a port where nothing is listening, while the real
server is on 127.0.0.1:11434. These helpers talk to the server that
actually answers, then force the CLI onto that same host.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:11434"
SERVE_LOG = ROOT / ".ollama" / "serve.log"


def _base_url(value: str) -> str:
    value = value.strip().rstrip("/")
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return "http://" + value


def _endpoint(base_url: str) -> tuple[str, int]:
    parsed = urlparse(_base_url(base_url))
    host = parsed.hostname or "127.0.0.1"
    if host == "localhost":
        host = "127.0.0.1"
    port = parsed.port or 11434
    return host, port


def _same_server(left: str, right: str) -> bool:
    return _endpoint(left) == _endpoint(right)


def _host_port(base_url: str) -> str:
    host, port = _endpoint(base_url)
    return f"{host}:{port}"


def installed_models(base_url: str) -> list[str] | None:
    """Return model names, or None when that address is not answering."""
    url = _base_url(base_url) + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            payload = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    return [item.get("name", "") for item in payload.get("models", [])]


def has_model(names: list[str], wanted: str) -> bool:
    return wanted in names or f"{wanted}:latest" in names


def _candidate_urls() -> list[str]:
    raw = [
        os.getenv("OLLAMA_BASE_URL", DEFAULT_BASE_URL),
        DEFAULT_BASE_URL,
        os.getenv("OLLAMA_HOST", ""),
    ]
    urls: list[str] = []
    for item in raw:
        if not item:
            continue
        url = _base_url(item)
        if not any(_same_server(url, existing) for existing in urls):
            urls.append(url)
    return urls


def find_server() -> str | None:
    """Return the first Ollama address that answers."""
    for url in _candidate_urls():
        if installed_models(url) is not None:
            return url
    return None


def _ensure_env_file() -> Path:
    env_path = ROOT / ".env"
    example = ROOT / ".env.example"
    if not env_path.exists() and example.exists():
        env_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        print("Created .env from .env.example")
    return env_path


def remember_base_url(base_url: str) -> None:
    """Point .env and this process at the server we actually reached."""
    os.environ["OLLAMA_BASE_URL"] = _base_url(base_url)
    env_path = _ensure_env_file()
    if not env_path.exists():
        return
    text = env_path.read_text(encoding="utf-8")
    current = ""
    for line in text.splitlines():
        if line.startswith("OLLAMA_BASE_URL="):
            current = line.split("=", 1)[1].strip()
            break
    if current and _same_server(current, base_url):
        return
    line = f"OLLAMA_BASE_URL={_base_url(base_url)}"
    if current:
        text = text.replace(f"OLLAMA_BASE_URL={current}", line, 1)
    else:
        if text and not text.endswith("\n"):
            text += "\n"
        text += line + "\n"
    env_path.write_text(text, encoding="utf-8")


def ensure_server() -> str:
    """Use a running Ollama server, or start one on 127.0.0.1:11434."""
    found = find_server()
    configured = os.getenv("OLLAMA_HOST", "")
    if found:
        if configured and not _same_server(configured, found):
            print(
                f"Ignoring OLLAMA_HOST={configured}. "
                f"Ollama is answering at {found}."
            )
        remember_base_url(found)
        return found

    if shutil.which("ollama") is None:
        raise SystemExit(
            "Ollama is not installed. Install it from https://ollama.com "
            "and run python -m starter.setup again."
        )

    print(f"Starting Ollama at {DEFAULT_BASE_URL}")
    SERVE_LOG.parent.mkdir(parents=True, exist_ok=True)
    log_file = SERVE_LOG.open("ab")
    env = os.environ.copy()
    # Bind the new server explicitly. A stale OLLAMA_HOST would otherwise
    # make `ollama serve` listen on a different port than this project.
    env["OLLAMA_HOST"] = _host_port(DEFAULT_BASE_URL)
    subprocess.Popen(
        ["ollama", "serve"],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    for _ in range(30):
        if installed_models(DEFAULT_BASE_URL) is not None:
            print("Ollama is up.")
            remember_base_url(DEFAULT_BASE_URL)
            return DEFAULT_BASE_URL
        time.sleep(0.5)
    raise SystemExit(f"Ollama did not start. Details are in {SERVE_LOG}")


def pull_model(base_url: str, model: str) -> None:
    """Download a model from the server this project is using."""
    if shutil.which("ollama") is None:
        raise SystemExit(
            "Ollama is not installed. Install it from https://ollama.com "
            "and run python -m starter.setup again."
        )
    env = os.environ.copy()
    env["OLLAMA_HOST"] = _host_port(base_url)
    print(f"Downloading {model} from {env['OLLAMA_HOST']}")
    subprocess.check_call(["ollama", "pull", model], env=env)

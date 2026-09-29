# find a running ollama server, or start one, then download a model

import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://127.0.0.1:11434"
LOG_FILE = ROOT / ".ollama" / "serve.log"


def clean_url(value):
    value = value.strip().rstrip("/")
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return "http://" + value


def host_and_port(base_url):
    url = clean_url(base_url)
    url = url.replace("https://", "").replace("http://", "")
    if "/" in url:
        url = url.split("/")[0]
    if ":" in url:
        host, port_text = url.rsplit(":", 1)
        port = int(port_text)
    else:
        host = url
        port = 11434
    if host == "localhost":
        host = "127.0.0.1"
    return host, port


def installed_models(base_url):
    url = clean_url(base_url) + "/api/tags"
    try:
        response = urllib.request.urlopen(url, timeout=3)
        data = json.loads(response.read().decode())
    except Exception:
        return None
    names = []
    for item in data.get("models", []):
        names.append(item.get("name", ""))
    return names


def has_model(names, wanted):
    if wanted in names:
        return True
    if wanted + ":latest" in names:
        return True
    return False


def find_server():
    raw = [
        os.getenv("OLLAMA_BASE_URL", DEFAULT_URL),
        DEFAULT_URL,
        os.getenv("OLLAMA_HOST", ""),
    ]
    urls = []
    for item in raw:
        if item is None or item.strip() == "":
            continue
        url = clean_url(item)
        host, port = host_and_port(url)
        key = host + ":" + str(port)
        seen = False
        for old in urls:
            old_host, old_port = host_and_port(old)
            if old_host + ":" + str(old_port) == key:
                seen = True
        if not seen:
            urls.append(url)

    for url in urls:
        if installed_models(url) is not None:
            return url
    return None


def make_env_file():
    env_path = ROOT / ".env"
    example = ROOT / ".env.example"
    if not env_path.exists() and example.exists():
        env_path.write_text(example.read_text())
        print("Created .env from .env.example")
    return env_path


def remember_base_url(base_url):
    base_url = clean_url(base_url)
    os.environ["OLLAMA_BASE_URL"] = base_url
    env_path = make_env_file()
    if not env_path.exists():
        return

    lines = env_path.read_text().splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.startswith("OLLAMA_BASE_URL="):
            found = True
            new_lines.append("OLLAMA_BASE_URL=" + base_url)
        else:
            new_lines.append(line)
    if not found:
        new_lines.append("OLLAMA_BASE_URL=" + base_url)
    env_path.write_text("\n".join(new_lines) + "\n")


def ensure_server():
    found = find_server()
    configured = os.getenv("OLLAMA_HOST", "")
    if found:
        if configured.strip() != "":
            same = host_and_port(configured) == host_and_port(found)
            if not same:
                print("Ignoring OLLAMA_HOST=" + configured + ". Ollama is answering at " + found + ".")
        remember_base_url(found)
        return found

    if shutil.which("ollama") is None:
        raise SystemExit("Ollama is not installed. Get it from https://ollama.com and run setup again.")

    print("Starting Ollama at " + DEFAULT_URL)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(LOG_FILE, "ab")
    env = os.environ.copy()
    host, port = host_and_port(DEFAULT_URL)
    env["OLLAMA_HOST"] = host + ":" + str(port)
    subprocess.Popen(
        ["ollama", "serve"],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

    for _ in range(30):
        if installed_models(DEFAULT_URL) is not None:
            print("Ollama is up.")
            remember_base_url(DEFAULT_URL)
            return DEFAULT_URL
        time.sleep(0.5)

    raise SystemExit("Ollama did not start. See " + str(LOG_FILE))


def pull_model(base_url, model):
    if shutil.which("ollama") is None:
        raise SystemExit("Ollama is not installed. Get it from https://ollama.com and run setup again.")
    env = os.environ.copy()
    host, port = host_and_port(base_url)
    env["OLLAMA_HOST"] = host + ":" + str(port)
    print("Downloading " + model + " from " + env["OLLAMA_HOST"])
    subprocess.check_call(["ollama", "pull", model], env=env)

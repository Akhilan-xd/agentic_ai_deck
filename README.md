# CrewAI local starter

A small CrewAI project you can copy and build on. Two agents run in order: one researches a topic, the next writes a short brief. Both call a model on your own machine through [Ollama](https://ollama.com). No cloud API key is required.

```text
starter/
  setup.py                # starts Ollama and downloads the model
  main.py                 # what you run
  llm.py                  # the only place the model is chosen
  crew.py                 # wires agents, tasks, and tools
  config/agents.yaml      # add a role here
  config/tasks.yaml       # add a step here
  qa.py                   # spoken Q&A chat; see starter/README.md
  tools/example_tool.py   # copy this when you add a tool
  tools/reading.py        # book and site lookup for qa.py
  tools/speech.py         # voice for qa.py
```

`{topic}` in the YAML files is filled in when you run the crew.

## What you need

- Python 3.10, 3.11, 3.12, or 3.13
- About 8 GB of free disk for a small model, more for larger ones
- [Ollama](https://ollama.com) installed and able to reach `http://localhost:11434`

`llama3.1:8b` is the default. It is large enough to follow the two-step brief. Smaller models often ignore the task format.

## 1. Install Ollama

**macOS:** download the app from [ollama.com](https://ollama.com), or:

```bash
brew install ollama
```

**Linux:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:** download the installer from [ollama.com](https://ollama.com).

You only need the Ollama program installed in this step. The next step starts it and downloads the model. Do not run `ollama pull` yourself: if your shell has `OLLAMA_HOST` pointed at a port where nothing is listening, that command fails even when Ollama is already running.

## 2. Set up this project

From the project folder, check the Python version first. It must be 3.10 or newer. Python 3.8 and 3.9 cannot install current CrewAI.

```bash
python3 --version
python3 -m venv .venv
```

If that `python3` is too old, install Python 3.12 and create the environment with it, for example `python3.12 -m venv .venv`.

Activate the virtual environment:

```bash
# macOS and Linux
source .venv/bin/activate

# Windows Command Prompt
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install dependencies. This pulls CrewAI and LiteLLM, which routes `ollama/...` model names to your local server:

```bash
pip install -r requirements.txt
```

Copy the environment file and leave the defaults if you pulled `llama3.1:8b`:

```bash
cp .env.example .env
```

On Windows Command Prompt use `copy .env.example .env`.

Start Ollama if it is stopped, and download the model named in `.env`:

```bash
python -m starter.setup
```

This looks for a server on `http://127.0.0.1:11434` and on `OLLAMA_HOST`. If one is already running, the download uses that server. If none is running, it starts Ollama on port `11434` and downloads there. A stale `OLLAMA_HOST` in `~/.bashrc` cannot send the download to the wrong port.

The first download of `llama3.1:8b` is several gigabytes. When the command prints `Ready`, continue to the next step.

## 3. Run it

```bash
python -m starter.main
```

Pass your own topic as an argument. It replaces `{topic}` in the agent and task files:

```bash
python -m starter.main "how a city should roll out internal coding agents"
```

The researcher runs first. The writer then receives those notes and prints a brief. The first run is slow because the model loads into memory.

To change the default topic without passing an argument, edit `TOPIC` in `.env`.

For a short chat that answers and then reads the reply aloud, run `python -m starter.qa`. Agents, tools, and the voice setting are in [starter/README.md](starter/README.md).

## 4. Point it at a different model

Edit `.env`:

```bash
OLLAMA_MODEL=qwen2.5:7b
```

Download that model with the same setup command. It reads `OLLAMA_MODEL` from `.env`:

```bash
python -m starter.setup
```

`qwen2.5:7b` is a good next step when you turn on tools. Keep `LLM_TEMPERATURE` around `0.2` so the agents stay on the brief.

If Ollama runs on another computer, set the host and start Ollama so it listens on the network:

```bash
OLLAMA_BASE_URL=http://192.168.1.20:11434
```

On the Ollama machine:

```bash
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

## 5. Use LM Studio or another local server

Any server that speaks the OpenAI chat API works. In LM Studio, start the local server (default `http://localhost:1234`). Then set `.env` like this:

```bash
LLM_PROVIDER=openai_compatible
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_MODEL_NAME=your-model-name-as-shown-in-lm-studio
OPENAI_API_KEY=lm-studio
```

`starter/llm.py` reads those values. You do not need to change the agents.

## 6. Add an agent

1. Add a block to `starter/config/agents.yaml`. The top-level name is the method name you will add in Python. Set `llm: local` so it uses the same model.

```yaml
editor:
  role: Editor
  goal: Tighten the brief on {topic} without adding new claims
  backstory: You cut repetition and flag anything the research notes do not support.
  llm: local
  verbose: true
  max_iter: 5
```

2. Add a method in `starter/crew.py` with the same name:

```python
@agent
def editor(self) -> Agent:
    return Agent(config=self.agents_config["editor"])
```

3. Give that agent a task (next section). An agent with no task does not run.

## 7. Add a task

1. Add a block to `starter/config/tasks.yaml`. `agent` must match an `@agent` method. `context` lists earlier tasks whose output this step should see.

```yaml
edit_task:
  description: Edit the brief on {topic}. Keep every claim tied to the research notes.
  expected_output: The revised brief, plus a short list of cuts you made.
  agent: editor
  context:
    - write_task
```

2. Add the matching method in `starter/crew.py`:

```python
@task
def edit_task(self) -> Task:
    return Task(config=self.tasks_config["edit_task"])
```

Tasks run in the order they are declared in `tasks.yaml`.

## 8. Add a tool

The example tool counts words. It stays off until you opt in, because small local models often mishandle tool calls.

1. In `starter/config/agents.yaml`, uncomment the tool on the agent that should use it:

```yaml
tools:
  - word_count
```

2. Run the crew again. `word_count` is already defined in `starter/crew.py` and implemented in `starter/tools/example_tool.py`.

To add your own tool, copy `starter/tools/example_tool.py`, change the class, then expose it from the crew:

```python
@tool
def my_tool(self):
    return MyTool()
```

Reference `my_tool` under `tools:` in the agent YAML. The YAML name and the method name must match.

## If it fails

| What you see | What to do |
| --- | --- |
| `could not connect to ollama server` after `ollama pull` | Run `python -m starter.setup` instead. Your shell's `OLLAMA_HOST` is pointed at a different port than the running server. |
| `Ollama is not running` | Run `python -m starter.setup`. It starts the server on port 11434. |
| Model is not installed | Run `python -m starter.setup`, or set `OLLAMA_MODEL` in `.env` to a model you already have and run setup again. |
| `OPENAI_API_KEY` error | Copy `.env.example` to `.env`. The Ollama path does not call OpenAI; CrewAI still wants a placeholder key when you switch providers. |
| Agent loops or ignores the format | Stay on `llama3.1:8b` or larger, keep temperature at `0.2`, and leave tools commented out until the brief looks right. |
| Connection error to another machine | Use that machine's real IP in `OLLAMA_BASE_URL`, and start Ollama with `OLLAMA_HOST=0.0.0.0:11434`. |

## Project layout

| File | Role |
| --- | --- |
| `starter/setup.py` | Starts Ollama and downloads the model in `.env` |
| `starter/ollama_server.py` | Finds the running server and ignores a stale `OLLAMA_HOST` |
| `starter/main.py` | Loads `.env`, checks Ollama, runs the crew |
| `starter/llm.py` | Builds the local LLM from `.env` |
| `starter/crew.py` | Connects YAML names to Python methods |
| `starter/config/agents.yaml` | Roles, goals, model, optional tools |
| `starter/config/tasks.yaml` | Steps, expected output, and which agent does each step |
| `starter/qa.py` | Spoken Q&A chat. Details in `starter/README.md` |
| `starter/tools/example_tool.py` | Pattern for a custom tool |
| `starter/tools/reading.py` | Wikipedia and Open Library lookup used by `qa.py` |
| `starter/tools/speech.py` | Reads the answer aloud and writes `spoken/latest.mp3` |

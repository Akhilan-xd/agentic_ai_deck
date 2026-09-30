# Spoken Q&A (`qa.py`)

A short chat. One agent answers, the next reads that answer aloud. Setup and the research crew are in the [project README](../README.md).

```bash
python -m starter.qa
python -m starter.qa "what should I read to learn stoicism?"
```

Type `exit` or `quit` to stop the chat. Each reply is saved as `spoken/latest.mp3`.

## Agents

Two agents, one after the other. Both use the model from `.env` (see the project README).

| Agent | What it does | Tool |
| --- | --- | --- |
| Conversation partner | Answers in a few sentences | `reading_lookup` |
| Narrator | Reads that answer aloud, once | `speak` |

The chat remembers the last 12 messages (about six turns). Set `QA_VERBOSE=true` in `.env` to print the agent steps.

## Tools

**`reading_lookup`** (`starter/tools/reading.py`) searches Wikipedia and Open Library. It returns at most two sites and two books, each with a real link. The partner is told to use only those links.

The lookup runs by itself when the question mentions a book, site, source, or something to buy (words such as `book`, `read`, `website`, `recommend`). Otherwise the partner can still call the tool.

**`speak`** (`starter/tools/speech.py`) turns the answer into speech with [edge-tts](https://github.com/rany2/edge-tts), writes `spoken/latest.mp3`, and plays it if `mpg123`, `ffplay`, or `mpv` is installed. Web addresses are spoken as the word "link".

## Voice

Change the voice in `.env`:

```bash
SPEAK_VOICE=en-US-AriaNeural
```

If `SPEAK_VOICE` is missing, the fallback in `starter/tools/speech.py` is `en-US-AndrewNeural` (`default_voice`).

A few other voices: `en-US-AndrewNeural`, `en-GB-SoniaNeural`, `en-IE-EmilyNeural`. List every voice with:

```bash
edge-tts --list-voices
```

To save the mp3 and skip playback, set `SPEAK_PLAY=off` in `.env`.

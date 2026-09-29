# reads an answer out loud and saves spoken/latest.mp3

import asyncio
import os
import shutil
import subprocess

import edge_tts
from crewai.tools import BaseTool

here = os.path.dirname(__file__)
root = os.path.abspath(os.path.join(here, "..", ".."))
out_dir = os.path.join(root, "spoken")
default_voice = "en-US-AndrewNeural"

# the chat sets this to the answer for this turn
script = ""
spoken_path = ""


def arm_script(text):
    global script, spoken_path
    script = text.strip()
    spoken_path = ""


def last_spoken():
    return spoken_path


def clean_text(text):
    text = text.replace("**", "").replace("`", "")
    words = []
    for word in text.split():
        if word.startswith("http://") or word.startswith("https://"):
            words.append("link")
        else:
            words.append(word)
    text = " ".join(words)
    if len(text) > 2000:
        text = text[:2000]
    if text == "":
        text = "There is nothing to read."
    return text


def save_mp3(text, path, voice):
    async def run():
        await edge_tts.Communicate(text, voice).save(path)

    # asyncio.run fails if a loop is already going, so use a thread then
    try:
        asyncio.get_running_loop()
        in_loop = True
    except RuntimeError:
        in_loop = False

    if not in_loop:
        asyncio.run(run())
        return

    import concurrent.futures

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    pool.submit(lambda: asyncio.run(run())).result()
    pool.shutdown()


def try_play(path):
    choice = os.getenv("SPEAK_PLAY", "auto").strip().lower()
    if choice in ["0", "false", "no", "off"]:
        return "playback turned off"

    players = [
        ["mpg123", "-q", path],
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        ["mpv", "--really-quiet", path],
    ]
    for command in players:
        if shutil.which(command[0]) is None:
            continue
        try:
            subprocess.run(command, check=True, timeout=180)
            return "played with " + command[0]
        except Exception:
            continue
    return "no speaker available on this machine"


def speak_aloud(text):
    global spoken_path
    spoken = clean_text(script or text)
    voice = os.getenv("SPEAK_VOICE", default_voice).strip()
    if voice == "":
        voice = default_voice
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "latest.mp3")
    save_mp3(spoken, path, voice)
    spoken_path = path
    playback = try_play(path)
    return "Spoken with " + voice + ". File: " + path + ". " + playback + "."


class SpeakTool(BaseTool):
    name: str = "speak"
    description: str = "Read text aloud. Call this once with the answer."

    def _run(self, text: str) -> str:
        return speak_aloud(text)

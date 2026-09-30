"""Connect notes that share a topic so the Obsidian graph links them."""

from __future__ import annotations

import re
from pathlib import Path

TOPIC_FOLDER = "topics"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
TOPICS_RE = re.compile(r"^topics:\s*\[(.*)\]\s*$", re.M)
SOURCE_RE = re.compile(r'^source:\s*"?\[\[(.+?)\]\]"?\s*$', re.M)
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
CONNECTED_RE = re.compile(
    r"\n?<!-- connected:start -->.*?<!-- connected:end -->\n?",
    re.S,
)


def vault_root() -> Path:
    return Path("obsidian_vault").resolve()


def safe_title(title: str) -> str:
    return "".join(ch for ch in title if ch not in '\\/:*?"<>|').strip()


def parse_frontmatter(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def parse_topics(text: str) -> list[str]:
    frontmatter = parse_frontmatter(text)
    match = TOPICS_RE.search(frontmatter)
    if not match:
        return []
    topics = []
    for part in match.group(1).split(","):
        topic = part.strip().strip("'\"")
        if topic:
            topics.append(topic)
    return topics


def parse_sources(text: str) -> list[str]:
    return SOURCE_RE.findall(parse_frontmatter(text))


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1).strip()


def set_topics(text: str, topics: list[str]) -> str:
    unique = []
    for topic in topics:
        if topic and topic not in unique:
            unique.append(topic)
    line = "topics: [" + ", ".join(unique) + "]"
    match = FRONTMATTER_RE.match(text)
    if not match:
        return f"---\n{line}\n---\n\n{text.rstrip()}\n"
    frontmatter = match.group(1)
    if TOPICS_RE.search(frontmatter):
        frontmatter = TOPICS_RE.sub(line, frontmatter, count=1)
    else:
        frontmatter = frontmatter.rstrip() + "\n" + line
    rest = text[match.end() :]
    return f"---\n{frontmatter}\n---{rest if rest.startswith(chr(10)) else chr(10) + rest}"


def merge_existing_note(existing: str, new: str) -> str:
    """Keep a shared note when a later paper uses it, and record the new paper."""
    new_sources = parse_sources(new)
    if not new_sources or all(source in existing for source in new_sources):
        topics = parse_topics(existing) + parse_topics(new)
        return set_topics(new if new_sources else existing, topics)

    topics = parse_topics(existing) + parse_topics(new)
    merged = set_topics(existing, topics)
    source = new_sources[0]
    marker = f"[[{source}]]"
    if marker not in merged:
        extra = strip_frontmatter(new)
        merged = (
            merged.rstrip()
            + f"\n\n### Also discussed in {marker}\n\n{extra}\n"
        )
    return merged


def _note_paths(vault: Path) -> list[Path]:
    return sorted(p for p in vault.rglob("*.md") if p.is_file())


def _upsert_connected(text: str, titles: list[str]) -> str:
    block = ["<!-- connected:start -->", "## Connected notes"]
    for title in titles:
        block.append(f"- [[{title}]]")
    block.append("<!-- connected:end -->")
    replacement = "\n" + "\n".join(block) + "\n"
    if CONNECTED_RE.search(text):
        return CONNECTED_RE.sub(replacement, text, count=1).rstrip() + "\n"
    return text.rstrip() + "\n" + replacement


def connect_topics_in_vault(vault: Path | None = None) -> str:
    vault = Path(vault or vault_root()).resolve()
    if not vault.is_dir():
        return "Vault not found."

    notes: list[tuple[Path, str, list[str]]] = []
    for path in _note_paths(vault):
        if path.parent.name == TOPIC_FOLDER:
            continue
        text = path.read_text(encoding="utf-8")
        notes.append((path, text, parse_topics(text)))

    by_topic: dict[str, list[str]] = {}
    stems = {path.stem: path for path, _, _ in notes}
    for path, _, topics in notes:
        for topic in topics:
            titles = by_topic.setdefault(topic, [])
            if path.stem not in titles and path.stem != topic:
                titles.append(path.stem)

    topic_dir = vault / TOPIC_FOLDER
    topic_dir.mkdir(parents=True, exist_ok=True)
    live_topics = set(by_topic)

    for stale in topic_dir.glob("*.md"):
        if stale.stem not in live_topics:
            stale.unlink()

    for topic, titles in sorted(by_topic.items()):
        if topic in stems:
            hub = stems[topic]
            current = hub.read_text(encoding="utf-8")
            hub.write_text(_upsert_connected(current, titles), encoding="utf-8")
        else:
            lines = [
                "---",
                "type: topic",
                "---",
                "",
                f"{topic} is a shared topic. A new paper that discusses the same subject links here, which connects it to the other notes in the graph.",
                "",
                "<!-- connected:start -->",
                "## Connected notes",
            ]
            for title in titles:
                lines.append(f"- [[{title}]]")
            lines.extend(["<!-- connected:end -->", ""])
            (topic_dir / f"{safe_title(topic)}.md").write_text(
                "\n".join(lines), encoding="utf-8"
            )

    return f"Linked {len(by_topic)} shared topics."


def list_notes(vault: Path | None = None, query: str = "") -> str:
    vault = Path(vault or vault_root()).resolve()
    if not vault.is_dir():
        return "Vault is empty."
    query_text = query.strip().lower()
    rows = []
    for path in _note_paths(vault):
        title = path.stem
        if query_text and query_text not in title.lower():
            continue
        topics = parse_topics(path.read_text(encoding="utf-8"))
        topic_text = f" [{', '.join(topics)}]" if topics else ""
        rows.append(f"{path.parent.name}/{title}{topic_text}")
    if not rows:
        return "No notes yet."
    return "\n".join(rows)

# looks up a wikipedia page and a couple of books

import html
import json
import urllib.parse
import urllib.request

from crewai.tools import BaseTool

USER_AGENT = "CometQA/1.0 (local study project)"


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    response = urllib.request.urlopen(request, timeout=12)
    data = response.read().decode()
    return json.loads(data)


def strip_html(value):
    text = ""
    inside = False
    for ch in value:
        if ch == "<":
            inside = True
        elif ch == ">":
            inside = False
        elif not inside:
            text = text + ch
    return " ".join(html.unescape(text).split())


def pick_isbn(isbn_list):
    backup = ""
    for isbn in isbn_list:
        clean = ""
        for ch in str(isbn):
            if ch.isdigit() or ch in "Xx":
                clean = clean + ch
        if len(clean) == 13 and clean.startswith("978"):
            return clean
        if backup == "" and len(clean) in [10, 13]:
            backup = clean
    return backup


def websites(query):
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": 2,
        "format": "json",
    })
    data = get_json("https://en.wikipedia.org/w/api.php?" + params)
    lines = []
    for hit in data.get("query", {}).get("search", []):
        title = hit.get("title", "").strip()
        if title == "":
            continue
        page = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
        line = "- " + title + " — " + page
        snippet = strip_html(hit.get("snippet", ""))
        if snippet != "":
            line = line + "\n  " + snippet
        lines.append(line)
    return lines


def books(query):
    params = urllib.parse.urlencode({
        "q": query,
        "limit": 2,
        "fields": "title,author_name,key,isbn,first_publish_year",
    })
    data = get_json("https://openlibrary.org/search.json?" + params)
    lines = []
    for doc in data.get("docs", []):
        title = (doc.get("title") or "").strip()
        if title == "":
            continue
        authors = doc.get("author_name") or []
        if len(authors) > 0:
            author = authors[0]
        else:
            author = "unknown author"
        year = doc.get("first_publish_year")
        if year:
            title_bit = title + " (" + str(year) + ")"
        else:
            title_bit = title
        line = "- " + title_bit + " by " + author
        work = doc.get("key") or ""
        if work != "":
            line = line + "\n  Read: https://openlibrary.org" + work
        isbn = pick_isbn(doc.get("isbn") or [])
        if isbn != "":
            line = line + "\n  Buy: https://www.amazon.com/s?k=" + urllib.parse.quote(isbn)
        lines.append(line)
    return lines


def lookup_reading(query):
    query = " ".join(query.split())
    if query == "":
        return "No lookup results. Ask for a topic first. Do not invent links."

    parts = []
    errors = []

    try:
        sites = websites(query)
        if len(sites) > 0:
            parts.append("Websites:\n" + "\n".join(sites))
    except Exception as exc:
        errors.append("website search failed (" + str(exc) + ")")

    try:
        found = books(query)
        if len(found) > 0:
            parts.append("Books:\n" + "\n".join(found))
    except Exception as exc:
        errors.append("book search failed (" + str(exc) + ")")

    if len(parts) == 0:
        if len(errors) > 0:
            detail = "; ".join(errors)
        else:
            detail = "nothing matched"
        return "No live results (" + detail + "). Do not invent links."

    if len(errors) > 0:
        parts.append("Note: " + "; ".join(errors))
    return "\n\n".join(parts)


class ReadingLookupTool(BaseTool):
    name: str = "reading_lookup"
    description: str = (
        "Find real websites and books to read or buy. "
        "Input is a short search, like 'stoicism beginner books'."
    )

    def _run(self, query: str) -> str:
        return lookup_reading(query)

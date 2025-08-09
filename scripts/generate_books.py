import json
import os
import re
import sys
from pathlib import Path

import urllib.parse
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[1]
LIST_PATH = REPO_ROOT / "list"
BOOKS_DIR = REPO_ROOT / "_books"
COVER_DIR = REPO_ROOT / "assets" / "cover"

OVERRIDES = {
    # list title -> override metadata
    "Culture": {
        "canonical_title": "The Culture Series",
        "author": "Iain M. Banks",
        "year": 1987,
    },
    "Meaning": {
        "canonical_title": "Man's Search for Meaning",
        "author": "Viktor E. Frankl",
        "year": 1946,
    },
    "The Capitalist Manifesto": {
        "canonical_title": "The Capitalist Manifesto",
        "author": "Andrew Bernstein",
        "year": 2005,
    },
    "The Road to Sefdom": {
        "canonical_title": "The Road to Serfdom",
        "author": "Friedrich A. Hayek",
        "year": 1944,
    },
    "the decline & fall of the Roman Empire": {
        "canonical_title": "The History of the Decline and Fall of the Roman Empire",
        "author": "Edward Gibbon",
        "year": 1776,
    },
    "Lying": {
        "canonical_title": "Lying",
        "author": "Sam Harris",
        "year": 2011,
    },
    "The Player of Games": {
        "canonical_title": "The Player of Games",
    },
    "The Skeptics' Guide To The Universe": {
        "canonical_title": "The Skeptics' Guide to the Universe",
        "author": "Steven Novella et al.",
        "year": 2018,
    },
    "The Age of Napoleon": {
        "canonical_title": "The Age of Napoleon",
        "author": "Will Durant; Ariel Durant",
        "year": 1975,
    },
    "Liftoff": {
        "canonical_title": "Liftoff: Elon Musk and the Desperate Early Days That Launched SpaceX",
        "author": "Eric Berger",
        "year": 2021,
    },
    "Masters of Doom": {
        "canonical_title": "Masters of Doom",
        "author": "David Kushner",
        "year": 2003,
    },
    "Storm of Steel": {
        "canonical_title": "Storm of Steel",
        "author": "Ernst Jünger",
    },
    "On Writing": {
        "canonical_title": "On Writing: A Memoir of the Craft",
        "author": "Stephen King",
        "year": 2000,
    },
    "Dune": {
        "canonical_title": "Dune",
        "author": "Frank Herbert",
        "year": 1965,
    },
    "Stranger in a Strange Land": {
        "canonical_title": "Stranger in a Strange Land",
        "author": "Robert A. Heinlein",
        "year": 1961,
    },
    "The Lord of the Ring": {
        "canonical_title": "The Lord of the Rings",
        "author": "J. R. R. Tolkien",
        "year": 1954,
    },
    "Destined for War": {
        "canonical_title": "Destined for War",
        "author": "Graham Allison",
        "year": 2017,
    },
    "Bad Therapy": {
        "canonical_title": "Bad Therapy",
        "author": "Abigail Shrier",
        "year": 2023,
    },
    "The Story of Civilization": {
        "canonical_title": "The Story of Civilization",
        "author": "Will Durant; Ariel Durant",
        "year": 1935,
    },
}

# Wikipedia title overrides for better summary hits
WIKI_OVERRIDES = {
    "The Culture Series": "Culture (series)",
    "The Skeptics' Guide to the Universe": "The Skeptics' Guide to the Universe (book)",
    "Lying": "Lying (book)",
    "Daemon": "Daemon (novel)",
}


def read_list_blocks(list_path: Path):
    raw = list_path.read_text(encoding="utf-8")
    print(f"list length: {len(raw)}")
    # Normalize newlines
    text = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    preview = "\\n".join(text.splitlines()[:3])
    print(f"list preview:\n{preview}")
    blocks = []
    current = []
    for line in text.splitlines():
        if line.strip() == "":
            if current:
                blocks.append(current)
                current = []
            continue
        current.append(line.rstrip())
    if current:
        blocks.append(current)
    return blocks


def parse_block(lines):
    title = lines[0].strip()
    quote_lines = []
    source = None
    for line in lines[1:]:
        if line.strip().startswith("http://") or line.strip().startswith("https://"):
            source = line.strip()
            break
        if line.strip():
            quote_lines.append(line.strip())
    quote = " ".join(quote_lines).strip() if quote_lines else ""
    return {
        "title": title,
        "quote": quote,
        "source": source,
    }


def safe_filename(name: str) -> str:
    # Keep letters, numbers, spaces, hyphens, underscores; collapse spaces
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"[^\w\-\s]", "", name, flags=re.UNICODE)
    name = name.replace("/", "-")
    return name


def openlibrary_search(title: str):
    query = urllib.parse.urlencode({"title": title})
    url = f"https://openlibrary.org/search.json?{query}&limit=1"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            docs = data.get("docs", [])
            return docs[0] if docs else None
    except Exception:
        return None


def openlibrary_fetch_description_by_key(work_or_book_key: str) -> str | None:
    # work_or_book_key like "/works/OL123W" or "/books/OL123M"
    url = f"https://openlibrary.org{work_or_book_key}.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            desc = data.get("description")
            if isinstance(desc, dict):
                desc = desc.get("value")
            if isinstance(desc, str):
                # Normalize whitespace and trim
                desc = re.sub(r"\s+", " ", desc).strip()
                return desc
    except Exception:
        return None
    return None


def openlibrary_fetch_summary(doc: dict) -> str | None:
    # Prefer work description, fallback to edition description
    work_key = doc.get("key")  # typically a work key like /works/OLxxxW
    if isinstance(work_key, str):
        desc = openlibrary_fetch_description_by_key(work_key)
        if desc:
            return desc
    edition_keys = doc.get("edition_key") or []
    for ek in edition_keys[:2]:  # try first two editions
        if isinstance(ek, str):
            desc = openlibrary_fetch_description_by_key(f"/books/{ek}")
            if desc:
                return desc
    return None


def wikipedia_fetch_summary(title: str) -> str | None:
    # REST API summary endpoint
    api_title = title
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(api_title)}"
    req = urllib.request.Request(url, headers={"User-Agent": "books-recommended-bot/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            extract = data.get("extract")
            if isinstance(extract, str) and extract.strip():
                # Use first 800 chars to keep it concise
                text = extract.strip()
                if len(text) > 800:
                    text = text[:797].rstrip() + "..."
                return text
    except Exception:
        return None
    return None


def download_cover(cover_id: int, dest_path: Path) -> bool:
    # Use large size; jpg
    url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            content = resp.read()
            dest_path.write_bytes(content)
            return True
    except Exception:
        return False


def ensure_cover_filename(cover_path: Path) -> bool:
    """Ensure the cover file exists with the expected case-sensitive filename.
    If a case-insensitive match exists, rename it.
    Returns True if file exists (possibly after rename), False otherwise.
    """
    if cover_path.exists():
        return True
    expected_lower = cover_path.name.lower()
    for p in cover_path.parent.glob("*.jpg"):
        if p.name.lower() == expected_lower:
            try:
                p.rename(cover_path)
                return True
            except Exception:
                return False
    return False


def write_book_file(dest_path: Path, frontmatter: dict):
    # Ensure directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---"]
    for key in ["title", "author", "year", "quote", "source", "summary", "cover"]:
        if key in frontmatter and frontmatter[key] not in (None, ""):
            value = frontmatter[key]
            # Quote strings safely
            if isinstance(value, str):
                # Escape existing quotes in YAML double-quoted style
                value = value.replace("\\", "\\\\").replace("\"", "\\\"")
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    dest_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    if not LIST_PATH.exists():
        print(f"list file not found: {LIST_PATH}", file=sys.stderr)
        sys.exit(1)

    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    COVER_DIR.mkdir(parents=True, exist_ok=True)

    blocks = read_list_blocks(LIST_PATH)
    print(f"Found {len(blocks)} entries in list")
    for lines in blocks:
        info = parse_block(lines)
        title_from_list = info["title"]
        print(f"Processing: {title_from_list}")

        override = OVERRIDES.get(title_from_list)

        # Look up metadata via Open Library (prefer override canonical title for search)
        search_title = (override.get("canonical_title") if override else None) or title_from_list
        doc = openlibrary_search(search_title)
        if doc:
            author = (override.get("author") if override and override.get("author") else (doc.get("author_name", [None])[0]))
            year = (override.get("year") if override and override.get("year") else doc.get("first_publish_year"))
            canonical_title = (override.get("canonical_title") if override and override.get("canonical_title") else (doc.get("title") or title_from_list))
            cover_id = doc.get("cover_i")
            summary_text = openlibrary_fetch_summary(doc)
            # Prefer Wikipedia summary when available to avoid mismatches (e.g., "One of Us Is Lying")
            wiki_title = WIKI_OVERRIDES.get(canonical_title, canonical_title)
            wiki_summary = wikipedia_fetch_summary(wiki_title)
            if wiki_summary:
                summary_text = wiki_summary
        else:
            author = override.get("author") if override else None
            year = override.get("year") if override else None
            canonical_title = (override.get("canonical_title") if override and override.get("canonical_title") else title_from_list)
            cover_id = None
            summary_text = None

        # Choose filename based on canonical title
        filename_base = safe_filename(canonical_title)
        md_path = BOOKS_DIR / f"{filename_base}.md"
        cover_rel = f"/assets/cover/{filename_base}.jpg"
        cover_path = COVER_DIR / f"{filename_base}.jpg"

        # Download cover if available and not already present
        if cover_id and not cover_path.exists():
            downloaded = download_cover(cover_id, cover_path)
            if not downloaded:
                # If failed, clear cover path to avoid referencing missing file
                cover_rel = None
        elif not cover_id:
            cover_rel = None

        # If no cover yet, try to adopt an existing cover by original title or case-insensitive match
        if cover_rel is None:
            original_cover_candidate = COVER_DIR / f"{safe_filename(title_from_list)}.jpg"
            # Prefer renaming case-insensitive match for expected canonical filename
            if ensure_cover_filename(cover_path):
                cover_rel = f"/assets/cover/{cover_path.name}"
            elif original_cover_candidate.exists():
                try:
                    original_cover_candidate.rename(cover_path)
                    cover_rel = f"/assets/cover/{cover_path.name}"
                except Exception:
                    pass

        # Always (re)write the file to apply overrides

        frontmatter = {
            "title": canonical_title,
            "author": author,
            "year": year,
            "quote": info.get("quote"),
            "source": info.get("source"),
            "summary": summary_text or "",
            "cover": cover_rel,
        }
        write_book_file(md_path, frontmatter)
        print(f"Created: {md_path.name}")

    # Cleanup clearly wrong earlier generated files
    wrong_files = [
        "Culture and anarchy an essay in political and social criticism.md",
        "On the origin of species by means of natural selection.md",
        "One Of Us Is Lying.md",
        "the decline  fall of the Roman Empire.md",
        "History of the Decline and Fall of the Roman Empire Complete and Unabridged.md",
        "Liftoff.md",
        "On Writing.md",
        "The Road to Sefdom.md",
        "The Story of Civilization I.md",
    ]
    for fname in wrong_files:
        path = BOOKS_DIR / fname
        if path.exists():
            try:
                path.unlink()
                print(f"Removed wrong file: {fname}")
            except Exception as e:
                print(f"Failed removing {fname}: {e}")

    # Cleanup wrong cover files matching the removed md names
    wrong_covers = [
        "Culture and anarchy an essay in political and social criticism.jpg",
        "On the origin of species by means of natural selection.jpg",
        "One Of Us Is Lying.jpg",
        "History of the Decline and Fall of the Roman Empire Complete and Unabridged.jpg",
    ]
    for cname in wrong_covers:
        cpath = COVER_DIR / cname
        if cpath.exists():
            try:
                cpath.unlink()
                print(f"Removed wrong cover: {cname}")
            except Exception as e:
                print(f"Failed removing cover {cname}: {e}")


if __name__ == "__main__":
    main()



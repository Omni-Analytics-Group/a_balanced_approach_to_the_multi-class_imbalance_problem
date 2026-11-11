# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""List citing works that the open citation indexes know about and data/citations.csv does not.

Run from the repository root:

    uv run scripts/find_new_citations.py

It queries OpenAlex and Semantic Scholar for works that cite the dissertation,
matches them against the CSV by DOI and by title, and prints the ones that are
missing so they can be read and added by hand. Nothing is written to disk.

Google Scholar has no API and blocks automated access, so its list has to be
checked in a browser.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITATIONS = ROOT / "data" / "citations.csv"

DISSERTATION_DOI = "10.31274/etd-180810-3375"
OPENALEX_WORK = "W103892688"
OPENALEX_URL = "https://api.openalex.org/works?filter=cites:{work}&per-page=200&cursor={cursor}"
SEMANTIC_SCHOLAR_URL = (
    "https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}/citations"
    "?fields=title,year,venue,externalIds&limit=100&offset={offset}"
)
TITLE_MATCH_THRESHOLD = 0.92
MAX_RETRIES = 6


class IndexUnavailable(RuntimeError):
    """A citation index could not be read in full, so its list would be incomplete."""


def fetch_json(url: str) -> dict:
    """GET a JSON document, backing off when the service rate-limits."""
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                time.sleep(4 * (attempt + 1))
                continue
            raise IndexUnavailable(f"HTTP {error.code} from {url}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"request failed ({error}): {url}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise IndexUnavailable(f"gave up after {MAX_RETRIES} attempts: {url}")


def normalize_title(title: str | None) -> str:
    plain = unicodedata.normalize("NFKD", title or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", plain).strip()


def printable(text: str) -> str:
    """Drop control characters so third-party titles cannot alter terminal output."""
    return "".join(char for char in " ".join(text.split()) if unicodedata.category(char)[0] != "C")


def normalize_doi(doi: str | None) -> str:
    return (doi or "").lower().replace("https://doi.org/", "").strip()


def openalex_citing() -> list[dict[str, str]]:
    found, cursor = [], "*"
    while cursor:
        page = fetch_json(OPENALEX_URL.format(work=OPENALEX_WORK, cursor=urllib.parse.quote(cursor, safe="*")))
        if not page.get("results"):
            break
        for work in page["results"]:
            found.append(
                {
                    "source": "OpenAlex",
                    "title": work.get("title") or "",
                    "year": str(work.get("publication_year") or ""),
                    "doi": normalize_doi(work.get("doi")),
                }
            )
        cursor = page.get("meta", {}).get("next_cursor")
    return found


def semantic_scholar_citing() -> list[dict[str, str]]:
    found, offset = [], 0
    while True:
        page = fetch_json(SEMANTIC_SCHOLAR_URL.format(doi=DISSERTATION_DOI, offset=offset))
        if not page.get("data"):
            break
        for entry in page["data"]:
            paper = entry.get("citingPaper") or {}
            ids = paper.get("externalIds") or {}
            doi = ids.get("DOI") or (f"10.48550/arxiv.{ids['ArXiv']}" if ids.get("ArXiv") else "")
            found.append(
                {
                    "source": "Semantic Scholar",
                    "title": paper.get("title") or "",
                    "year": str(paper.get("year") or ""),
                    "doi": normalize_doi(doi),
                }
            )
        if "next" not in page:
            break
        offset += 100
    return found


def known_works() -> tuple[set[str], list[str]]:
    """DOIs and normalized titles (including merged versions) already in the CSV."""
    dois: set[str] = set()
    titles: list[str] = []
    with CITATIONS.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            dois.update(normalize_doi(doi) for doi in [row["doi"], *row["other_dois"].split()] if doi)
            for title in [row["title"], row["english_title"], *row["alt_titles"].split(" || ")]:
                if title:
                    titles.append(normalize_title(title))
    return dois, titles


def is_known(candidate: dict[str, str], dois: set[str], titles: list[str]) -> bool:
    if candidate["doi"] and candidate["doi"] in dois:
        return True
    title = normalize_title(candidate["title"])
    if not title:
        return False
    return any(SequenceMatcher(None, title, known).ratio() >= TITLE_MATCH_THRESHOLD for known in titles)


def main() -> None:
    if not CITATIONS.exists():
        sys.exit(f"missing {CITATIONS}")
    dois, titles = known_works()
    try:
        candidates = openalex_citing() + semantic_scholar_citing()
    except IndexUnavailable as error:
        sys.exit(f"could not read a citation index, so no result is reported: {error}")
    missing: dict[str, dict[str, str]] = {}
    for candidate in candidates:
        if is_known(candidate, dois, titles):
            continue
        key = candidate["doi"] or normalize_title(candidate["title"])
        missing.setdefault(key, candidate)
    print(f"checked {len(candidates)} index records against {len(titles)} known titles")
    if not missing:
        print("no new citing works found")
        return
    print(f"{len(missing)} citing works are not in data/citations.csv:")
    for candidate in sorted(missing.values(), key=lambda item: item["year"], reverse=True):
        doi = f"https://doi.org/{candidate['doi']}" if candidate["doi"] else "no DOI"
        print(f"- {candidate['year'] or 'n.d.'} | {printable(candidate['title'])} | {printable(doi)} | via {candidate['source']}")


if __name__ == "__main__":
    main()

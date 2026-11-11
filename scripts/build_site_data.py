# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Write docs/data.js for the GitHub Pages site and the citing-works tables for the README.

Run from the repository root after editing data/citations.csv or data/resources.json:

    uv run scripts/build_site_data.py

Outputs:
    docs/data.js            data for the interactive site (docs/index.html)
    data/CITING_WORKS.md    every citing work grouped by discipline, linked from the README
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CITATIONS = ROOT / "data" / "citations.csv"
RESOURCES = ROOT / "data" / "resources.json"
SITE_DATA = ROOT / "docs" / "data.js"
CITING_WORKS = ROOT / "data" / "CITING_WORKS.md"

GOOGLE_SCHOLAR_COUNT = 167
GOOGLE_SCHOLAR_DATE = "2026-11-10"

SITE_FIELDS = (
    "id",
    "title",
    "english_title",
    "authors",
    "short_ref",
    "year",
    "venue",
    "doc_type",
    "language",
    "url",
    "discipline",
    "domain",
    "usage",
    "reports_cba_values",
    "deep_learning",
    "how_used",
    "quote",
    "evidence",
    "cited_by",
    "countries",
)

USAGE_ORDER = (
    "Builds on CBA",
    "Uses CBA as a metric",
    "Discusses CBA",
    "Software",
    "Cites it for balanced accuracy",
    "Cites it for the imbalance problem",
    "Cites it for a method",
    "Other",
    "Not determined",
)


def read_citations() -> list[dict[str, str]]:
    with CITATIONS.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def safe_url(url: str) -> str:
    return url if url.startswith(("https://", "http://")) else ""


def site_row(row: dict[str, str]) -> dict[str, object]:
    slim: dict[str, object] = {field: row.get(field, "") for field in SITE_FIELDS}
    slim["url"] = safe_url(row.get("url", ""))
    slim["year"] = int(row["year"]) if row.get("year") else None
    slim["cited_by"] = int(row["cited_by"]) if row.get("cited_by") else 0
    return slim


def write_site_data(rows: list[dict[str, str]], resources: dict) -> None:
    payload = {
        "generated": date.today().isoformat(),
        "googleScholarCount": GOOGLE_SCHOLAR_COUNT,
        "googleScholarDate": GOOGLE_SCHOLAR_DATE,
        "usageOrder": list(USAGE_ORDER),
        "citations": [site_row(row) for row in rows],
        "software": resources.get("software", []),
        "reading": resources.get("reading", []),
        "implementations": resources.get("cba_implementations", []),
    }
    SITE_DATA.parent.mkdir(exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    SITE_DATA.write_text(f"window.SITE_DATA = {text};\n", encoding="utf-8")
    print(f"wrote {SITE_DATA.relative_to(ROOT)} ({len(rows)} citing works)")


MARKDOWN_PUNCTUATION = re.compile(r"([\\`*_{}\[\]()#+!|~])")


def single_line(text: str) -> str:
    """Collapse every run of whitespace, including Unicode line separators, to one space."""
    return " ".join(text.split())


def markdown_escape(text: str) -> str:
    """Escape text from third parties so it cannot open Markdown or HTML constructs."""
    escaped = MARKDOWN_PUNCTUATION.sub(r"\\\1", single_line(text))
    return escaped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def markdown_url(url: str) -> str:
    """Return a URL that is safe inside a Markdown link target, or an empty string."""
    checked = safe_url(single_line(url))
    return checked.replace(" ", "%20").replace("(", "%28").replace(")", "%29").replace("<", "%3C").replace(">", "%3E")


def citing_work_line(row: dict[str, str]) -> str:
    title = markdown_escape(row["title"])
    url = markdown_url(row["url"])
    linked = f"[{title}]({url})" if url else title
    byline = ", ".join(markdown_escape(part) for part in (row["short_ref"], row["venue"]) if part)
    detail = f" {markdown_escape(row['how_used'])}" if row["how_used"] and row["usage"] != "Not determined" else ""
    return f"- **{markdown_escape(row['usage'])}.** {linked}. {byline}.{detail}"


def write_citing_works(rows: list[dict[str, str]]) -> None:
    by_discipline: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_discipline[row["discipline"]].append(row)
    ordered = sorted(by_discipline, key=lambda name: (name == "Not determined", -len(by_discipline[name]), name))
    usage_rank = {name: position for position, name in enumerate(USAGE_ORDER)}
    lines = [
        "# Works citing the dissertation",
        "",
        (
            f"{len(rows)} distinct works, grouped by the discipline of the citing work. "
            "Within each group, works that use Class Balance Accuracy come first. "
            "This file is generated from [citations.csv](citations.csv) by `scripts/build_site_data.py`. "
            "Edit the CSV, not this file."
        ),
        "",
    ]
    for discipline in ordered:
        group = sorted(
            by_discipline[discipline],
            key=lambda row: (usage_rank.get(row["usage"], 99), -(int(row["year"]) if row["year"] else 0), row["title"].lower()),
        )
        lines += [f"## {markdown_escape(discipline)} ({len(group)})", ""]
        lines += [citing_work_line(row) for row in group]
        lines.append("")
    CITING_WORKS.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {CITING_WORKS.relative_to(ROOT)}")


def print_summary(rows: list[dict[str, str]]) -> None:
    print("usage:", Counter(row["usage"] for row in rows).most_common())
    countries = {code for row in rows for code in row["countries"].split()}
    languages = {row["language"] for row in rows}
    print(f"countries: {len(countries)}, languages: {len(languages)}")


def main() -> None:
    rows = read_citations()
    resources = json.loads(RESOURCES.read_text(encoding="utf-8")) if RESOURCES.exists() else {}
    write_site_data(rows, resources)
    write_citing_works(rows)
    print_summary(rows)


if __name__ == "__main__":
    main()

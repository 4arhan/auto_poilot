"""Scrape the main-nav pages of https://4arhan.github.io/Autopiolot/ to Markdown."""

from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify

BASE = "https://4arhan.github.io/Autopiolot"
SLUGS = [
    "index",
    "solutions",
    "cases",
    "demo",
    "pricing",
    "process",
    "about",
    "contact",
]

OUT_DIR = Path(__file__).parent / "content"
USER_AGENT = "autopilot-scraper/0.1 (+https://github.com/4arhan/auto_poilot)"
TIMEOUT = 20
MAX_RETRIES = 3
STRIP_TAGS = ("script", "style", "nav", "header", "footer", "form", "noscript", "svg")


def fetch(url: str) -> str:
    last_err: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            last_err = e
            time.sleep(2**attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def extract(html: str) -> tuple[str, str, str]:
    """Return (title, description, cleaned_main_html)."""
    soup = BeautifulSoup(html, "html.parser")

    title = (soup.title.string or "").strip() if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = (desc_tag.get("content") or "").strip() if desc_tag else ""

    main: Tag | None = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id="content")
        or soup.find(class_="content")
        or soup.body
    )
    if main is None:
        main = soup

    for tag in main.find_all(STRIP_TAGS):
        tag.decompose()
    for tag in main.find_all(attrs={"role": "navigation"}):
        tag.decompose()

    return title, description, str(main)


def to_markdown(html: str) -> str:
    md = markdownify(html, heading_style="ATX", strip=["img"])
    lines = [ln.rstrip() for ln in md.splitlines()]
    out: list[str] = []
    blank = 0
    for ln in lines:
        if ln == "":
            blank += 1
            if blank <= 1:
                out.append(ln)
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip() + "\n"


def frontmatter(title: str, url: str, slug: str, description: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    safe_title = title.replace('"', '\\"')
    safe_desc = description.replace('"', '\\"')
    return (
        "---\n"
        f'title: "{safe_title}"\n'
        f"url: {url}\n"
        f"slug: {slug}\n"
        f"scraped_at: {ts}\n"
        f'description: "{safe_desc}"\n'
        "---\n\n"
    )


def scrape_one(slug: str) -> tuple[Path, int]:
    url = f"{BASE}/{slug}.html"
    html = fetch(url)
    title, description, main_html = extract(html)
    body_md = to_markdown(main_html)
    heading = f"# {title}\n\n" if title and not body_md.lstrip().startswith("#") else ""
    doc = frontmatter(title, url, slug, description) + heading + body_md
    path = OUT_DIR / f"{slug}.md"
    path.write_text(doc, encoding="utf-8")
    words = len(body_md.split())
    return path, words


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    for i, slug in enumerate(SLUGS):
        try:
            path, words = scrape_one(slug)
            print(f"✓ {slug}.html → {path.relative_to(Path.cwd())} ({words} words)")
        except Exception as e:
            print(f"✗ {slug}.html — {e}", file=sys.stderr)
            failures.append(slug)
        if i < len(SLUGS) - 1:
            time.sleep(1)
    if failures:
        print(f"\n{len(failures)} page(s) failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"\nDone. {len(SLUGS)} pages written to {OUT_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())

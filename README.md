# auto_poilot — site scraper

Scrapes the 8 main-nav pages of <https://4arhan.github.io/Autopiolot/> and writes each as a Markdown file under `content/`. Output is content-only (nav/header/footer stripped) and includes YAML front-matter with title, URL, slug, timestamp, and description — suitable for downstream embedding / vectorization.

## Usage

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scrape.py
```

Output: `content/{index,solutions,cases,demo,pricing,process,about,contact}.md`.

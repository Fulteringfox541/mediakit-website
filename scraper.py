import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ============================================================
# SETUP: replace the placeholder URLs below with the real ones.
#   "content"  = their blog / insights / news / resources page
#   "product"  = their main product or solutions page
#   "linkedin" = their LinkedIn company page (NOT scraped, just linked)
# ============================================================
COMPETITORS = {
    "SPi (Structured Products Intelligence)": {
        "content":  "https://sp-intelligence.com/webflow-page/research",
        "product":  "https://sp-intelligence.com/",
        "linkedin": "https://www.linkedin.com/company/spintelligence/posts/?feedView=all",
    },
    "LPA (Lucht Probst Associates)": {
        "content":  "https://www.l-p-a.com/about-lpa/news-archive/",
        "product":  "https://www.l-p-a.com/capmatix/",
        "linkedin": "https://www.linkedin.com/company/lpa-lucht-probst-associates-gmbh/posts/?feedView=all",
    },
    "WSD (Wall Street Docs)": {
        "content":  "https://www.wsd.com/company/about-wsd#history",
        "product":  "https://www.wsd.com/products/structured-products-intelligence",
        "linkedin": "https://www.linkedin.com/company/wsdgroup/posts/?feedView=all",
    },
    "Leonteq": {
        "content":  "https://www.leonteq.com/news-and-media/news/investment-themes",
        "product":  "https://www.leonteq.com/our-solutions/products/for-end-investors",
        "linkedin": "https://www.linkedin.com/company/leonteq/posts/?feedView=all",
    },
    "Cegaware": {
        "content":  "https://www.cegaware.com/blog",
        "product":  "https://www.cegaware.com",
        "linkedin": "https://www.linkedin.com/company/cegaware/posts/?feedView=all",
    },
}

TRACKED_PAGES = ["content", "product"]
STATE_FILE = "state.json"

# How many new sentences to show per changed page, so the report stays readable.
MAX_NEW_SENTENCES = 8


def fetch_page_text(url):
    """Return cleaned visible text from a page, or None if unreachable."""
    if not url:
        return None
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        text = ' '.join(soup.get_text(separator=' ').split())
        return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def fingerprint(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def split_sentences(text):
    """Rough sentence split. Good enough to spot what is new without
    needing any extra libraries."""
    chunks = []
    current = ""
    for char in text:
        current += char
        if char in ".!?" and len(current.strip()) > 0:
            chunks.append(current.strip())
            current = ""
    if current.strip():
        chunks.append(current.strip())
    return chunks


def find_new_content(old_text, new_text):
    """Return the sentences present in the new text that were not in the old
    text. This is what actually changed, rather than the whole page."""
    old_sentences = set(split_sentences(old_text))
    new_sentences = split_sentences(new_text)

    added = [s for s in new_sentences if s not in old_sentences and len(s) > 20]

    if not added:
        # Text changed but no clearly new sentences (for example wording
        # tweaks or reordering). Say so honestly rather than show nothing.
        return None

    return added[:MAX_NEW_SENTENCES]


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def build_report():
    state = load_state()
    new_state = {}
    date_str = datetime.now().strftime("%Y-%m-%d")

    changed_blocks = []
    quiet = []
    unreachable = []

    for name, pages in COMPETITORS.items():
        company_changes = []

        for page_type in TRACKED_PAGES:
            url = pages.get(page_type)
            key = f"{name} :: {page_type}"
            text = fetch_page_text(url)

            if text is None:
                if url:
                    unreachable.append(f"{name} ({page_type})")
                continue

            new_fp = fingerprint(text)
            # Store fingerprint and text so we can compare next week.
            new_state[key] = {"fp": new_fp, "text": text}

            old_entry = state.get(key)
            old_fp = old_entry.get("fp") if isinstance(old_entry, dict) else None
            old_text = old_entry.get("text", "") if isinstance(old_entry, dict) else ""

            if old_fp is None:
                # First time seeing this page. Record baseline, do not report.
                continue

            if new_fp != old_fp:
                added = find_new_content(old_text, text)
                if added:
                    bullet_lines = "\n".join(f"    - {s}" for s in added)
                    company_changes.append(
                        f"  {page_type.upper()} page changed: {url}\n"
                        f"  New content:\n{bullet_lines}\n"
                    )
                else:
                    company_changes.append(
                        f"  {page_type.upper()} page changed: {url}\n"
                        f"  (Minor change only: wording or layout tweaks, "
                        f"no clearly new content.)\n"
                    )

        if company_changes:
            block = f"{name}\n" + "\n".join(company_changes)
            linkedin = pages.get("linkedin")
            if linkedin:
                block += f"  Check LinkedIn: {linkedin}\n"
            changed_blocks.append(block)
        else:
            quiet.append(name)

    lines = [f"WEEKLY COMPETITOR SNAPSHOT  ({date_str})", ""]

    if changed_blocks:
        lines.append("CHANGES DETECTED THIS WEEK")
        lines.append("")
        lines.extend(changed_blocks)
        lines.append("")
    else:
        lines.append("No website changes detected across tracked pages this week.")
        lines.append("")

    if quiet:
        lines.append("No website change: " + ", ".join(quiet))
        lines.append("")

    if unreachable:
        lines.append("Could not reach: " + ", ".join(unreachable))
        lines.append("")

    lines.append("LinkedIn pages to glance at (not auto-checked):")
    for name, pages in COMPETITORS.items():
        linkedin = pages.get("linkedin")
        if linkedin:
            lines.append(f"  {name}: {linkedin}")
    lines.append("")

    lines.append(
        "Note: this shows text that is newly present on a page since last week. "
        "It flags what changed, not why it matters. For a plain-English read, "
        "paste anything interesting into Claude. LinkedIn is not auto-checked."
    )

    save_state(new_state)
    return "\n".join(lines)


def post_to_teams(report_content):
    teams_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if not teams_url:
        print("No TEAMS_WEBHOOK_URL set, skipping post.")
        return
    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.2",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": report_content,
                            "wrap": True,
                            "fontType": "Monospace"
                        }
                    ]
                }
            }
        ]
    }
    response = requests.post(teams_url, json=payload)
    print(f"Teams response: {response.status_code} - {response.text}")


def main():
    report = build_report()
    print(report)
    post_to_teams(report)


if __name__ == "__main__":
    main()

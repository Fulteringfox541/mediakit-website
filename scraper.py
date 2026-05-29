import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ============================================================
# SETUP: replace the placeholder URLs below with the real ones.
# For each competitor:
#   "content"  = their blog / insights / news / resources page
#   "product"  = their main product or solutions page
#   "linkedin" = their LinkedIn company page (NOT scraped, just linked
#                in the report so you can check it manually)
# Leave any value as None to skip it for that company.
# ============================================================
COMPETITORS = {
    "SPi (Structured Products Intelligence)": {
        "content":  "https://sp-intelligence.com/webflow-page/research",   # CHECK THIS URL
        "product":  "https://sp-intelligence.com/",   # CHECK THIS URL
        "linkedin": "https://www.linkedin.com/company/spintelligence/posts/?feedView=all",   # CHECK THIS URL
    },
    "LPA (Lucht Probst Associates)": {
        "content":  "https://www.l-p-a.com/about-lpa/news-archive/",             # CHECK THIS URL
        "product":  "https://www.l-p-a.com/capmatix/",            # CHECK THIS URL
        "linkedin": "https://www.linkedin.com/company/lpa-lucht-probst-associates-gmbh/posts/?feedView=all",   # CHECK THIS URL
    },
    "WSD (Wall Street Docs)": {
        "content":  "https://www.wsd.com/company/about-wsd#history",               # CHECK THIS URL
        "product":  "https://www.wsd.com/products/structured-products-intelligence",               # CHECK THIS URL
        "linkedin": "https://www.linkedin.com/company/wsdgroup/posts/?feedView=all",   # CHECK THIS URL
    },
    "Leonteq": {
        "content":  "https://www.leonteq.com/news-and-media/news/investment-themes",               # CHECK THIS URL
        "product":  "https://www.leonteq.com/our-solutions/products/for-end-investors",           # CHECK THIS URL
        "linkedin": "https://www.linkedin.com/company/leonteq/posts/?feedView=all",  # CHECK THIS URL
    },
    "Cegaware": {
        "content":  "https://www.cegaware.com/blog",          # CHECK THIS URL
        "product":  "https://www.cegaware.com",          # CHECK THIS URL
        "linkedin": "https://www.linkedin.com/company/cegaware/posts/?feedView=all", # CHECK THIS URL
    },
}

# Page types that get scraped and compared. LinkedIn is deliberately excluded.
TRACKED_PAGES = ["content", "product"]

STATE_FILE = "state.json"


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
        # Drop nav, scripts, styles, and footers so we compare real content.
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        text = ' '.join(soup.get_text(separator=' ').split())
        return text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def fingerprint(text):
    """A short signature of the page content, used to detect change."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


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

    changed_blocks = []   # competitors with something new
    quiet = []            # competitors with no change
    unreachable = []      # pages that could not be checked

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
            new_state[key] = new_fp
            old_fp = state.get(key)

            if old_fp is None:
                # First time seeing this page. Record it, do not report it as
                # a change (there is nothing to compare to yet).
                continue

            if new_fp != old_fp:
                snippet = text[:300].strip()
                company_changes.append(
                    f"  {page_type.upper()} page changed.\n"
                    f"  Now showing: {snippet}...\n"
                )

        if company_changes:
            block = f"{name}\n" + "\n".join(company_changes)
            linkedin = pages.get("linkedin")
            if linkedin:
                block += f"  Check LinkedIn: {linkedin}\n"
            changed_blocks.append(block)
        else:
            quiet.append(name)

    # Assemble the report
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

    # Always list LinkedIn pages as a manual prompt, since these are not scraped.
    lines.append("LinkedIn pages to glance at (not auto-checked):")
    for name, pages in COMPETITORS.items():
        linkedin = pages.get("linkedin")
        if linkedin:
            lines.append(f"  {name}: {linkedin}")
    lines.append("")

    lines.append(
        "Note: this flags that website pages changed and roughly what appeared. "
        "It does not judge commercial relevance, and it does not read LinkedIn. "
        "Review anything flagged before acting."
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

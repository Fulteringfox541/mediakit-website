import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

COMPETITORS = {
    "SPi (Structured Products Intelligence)": "https://sp-intelligence.com",
    "LPA (Lucht Probst Associates)": "http://l-p-a.com",
    "WSD (Wall Street Docs)": "https://wsd.com",
    "Leonteq": "https://leonteq.com",
    "Cegaware": "https://cegaware.com"
}

def safe_scrape(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error: {e}")
    return None

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_content = f"WEEKLY COMPETITOR INTELLIGENCE SUMMARY ({date_str})\n\n"
    
    for name, url in COMPETITORS.items():
        report_content += f"COMPANY: {name}\n"
        soup = safe_scrape(url)
        if soup:
            text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'span'])[:20]])
            report_content += f"• Homepage Snapshot: {text[:250]}...\n"
        report_content += "\n-------------\n\n"
        
    teams_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if teams_url:
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

if __name__ == "__main__":
    main()

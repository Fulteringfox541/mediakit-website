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
        print(f"Error scraping {url}: {e}")
    return None

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # We build the report using clean, basic HTML line breaks (<br>) that Teams loves
    report_content = f"<h2>Weekly competitor insights summary ({date_str})</h2><br><br>"
    
    for name, url in COMPETITORS.items():
        report_content += f"<h3>🏢 {name}</h3>"
        soup = safe_scrape(url)
        
        if soup:
            text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'span'])[:20]])
            # Clean text of any rogue quotes that break webhooks
            clean_text = text[:300].replace('"', "'").replace('\n', ' ')
            report_content += f"<b>Homepage Snapshot:</b> {clean_text}...<br><br>"
            
            links = [a.text.strip() for a in soup.find_all('a') if len(a.text.strip()) > 15][:5]
            report_content += "<b>Latest Content Links:</b><br>"
            for link in links:
                clean_link = link.replace('"', "'").replace('\n', ' ')
                report_content += f"• {clean_link}<br>"
            report_content += "<br>"
        else:
            report_content += "<i>Failed to scrape site this week.</i><br><br>"
        report_content += "<hr><br>"
        
    # Send directly to Microsoft Teams right here inside Python (much more stable)
    teams_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if teams_url:
        payload = {"text": report_content}
        response = requests.post(teams_url, json=payload)
        print(f"Teams delivery status: {response.status_code}")
    else:
        print("Missing TEAMS_WEBHOOK_URL secret!")

if __name__ == "__main__":
    main()

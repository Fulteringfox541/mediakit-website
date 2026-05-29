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
    
    # Formatted strictly to Microsoft's standard text requirements
    report_content = f"WEEKLY COMPETITOR INTELLIGENCE SUMMARY ({date_str})\n\n"
    
    for name, url in COMPETITORS.items():
        report_content += f"COMPANY: {name}\n"
        soup = safe_scrape(url)
        
        if soup:
            text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'span'])[:20]])
            clean_text = text[:250].replace('"', "'").replace('\n', ' ').strip()
            report_content += f"• Homepage Snapshot: {clean_text}...\n"
            
            links = [a.text.strip() for a in soup.find_all('a') if len(a.text.strip()) > 15][:3]
            if links:
                report_content += "• Links Found:\n"
                for link in links:
                    clean_link = link.replace('"', "'").replace('\n', ' ').strip()
                    report_content += f"  - {clean_link}\n"
        else:
            report_content += "• Status: Webpage scan failed this week.\n"
        report_content += "\n-------------------------------------\n\n"
        
    teams_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if teams_url:
        # Verified official Microsoft Workflow webhook payload schema
        payload = {"text": report_content}
        
        response = requests.post(teams_url, json=payload)
        print(f"Teams Server Response Code: {response.status_code}")
        print(f"Teams Server Server Message: {response.text}")
    else:
        print("Error: Missing TEAMS_WEBHOOK_URL secret!")

if __name__ == "__main__":
    main()

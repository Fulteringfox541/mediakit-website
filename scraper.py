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
    report_content = f"Weekly Competitor Intelligence Summary ({date_str})\n\n"
    
    for name, url in COMPETITORS.items():
        report_content += f"### 🏢 {name}\n"
        soup = safe_scrape(url)
        
        if soup:
            text = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'span'])[:20]])
            report_content += f"**Homepage Snapshot:** {text[:300]}...\n\n"
            
            links = [a.text.strip() for a in soup.find_all('a') if len(a.text.strip()) > 15][:5]
            report_content += "**Latest Content Links:**\n"
            for link in links:
                report_content += f"- {link}\n"
            report_content += "\n"
        else:
            report_content += "*Failed to scrape site this week.*\n\n"
        report_content += "---\n"
        
    # Save the text directly to a file that GitHub can read
    with open("weekly_report.txt", "w", encoding="utf-8") as f:
        f.write(report_content)
    print("Report compiled successfully!")

if __name__ == "__main__":
    main()

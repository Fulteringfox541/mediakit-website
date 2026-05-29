import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 1. Configuration - Your 5 Competitors
COMPETITORS = {
    "SPi (Structured Products Intelligence)": {
        "homepage": "https://sp-intelligence.com/",
        "pricing": "https://sp-intelligence.com/",
        "blog": "https://sp-intelligence.com/"
    },
    "LPA (Lucht Probst Associates)": {
        "homepage": "http://www.l-p-a.com/",
        "pricing": "http://www.l-p-a.com/",
        "blog": "http://www.l-p-a.com/"
    },
    "WSD (Wall Street Docs)": {
        "homepage": "https://www.wsd.com/",
        "pricing": "https://www.wsd.com/",
        "blog": "https://www.wsd.com/"
    },
    "Leonteq": {
        "homepage": "https://www.leonteq.com/",
        "pricing": "https://www.leonteq.com/",
        "blog": "https://www.leonteq.com/"
    },
    "Cegaware": {
        "homepage": "https://www.cegaware.com/",
        "pricing": "https://www.cegaware.com/",
        "blog": "https://www.cegaware.com/"
    }
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

def extract_intel():
    email_body = "<h2>Weekly Competitor Intelligence Summary</h2><br>"
    
    for name, urls in COMPETITORS.items():
        email_body += f"<h3>🏢 {name}</h3>"
        
        # Scrape Pricing Text
        soup_price = safe_scrape(urls["pricing"])
        if soup_price:
            text = ' '.join([p.text for p in soup_price.find_all(['p', 'h1', 'h2', 'span'])[:20]])
            email_body += f"<p><b>Pricing Snippet / Page Text:</b> {text[:300]}...</p>"
        
        # Scrape Blog / Content Links
        soup_blog = safe_scrape(urls["blog"])
        if soup_blog:
            links = [a.text.strip() for a in soup_blog.find_all('a') if len(a.text.strip()) > 15][:5]
            email_body += "<p><b>Latest Content Links found:</b></p><ul>"
            for link in links:
                email_body += f"<li>{link}</li>"
            email_body += "</ul>"
            
        email_body += "<hr>"
    return email_body

def send_email(content):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    receiver_email = os.environ.get("RECEIVER_EMAIL")
    
    if not sender_email or not sender_password:
        print("Email credentials missing. Skipping email send.")
        print(content)
        return

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Weekly Competitor Intelligence Digest"
    
    msg.attach(MIMEText(content, 'html'))
    
    try:
        server = smtplib.SMTP('://gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    report = extract_intel()
    send_email(report)

#!/usr/bin/env python3
"""
SoCal CRE Daily Brief - Scrapes market data and sends synthesized email
"""

import os
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import anthropic

# Configuration
GMAIL_ADDRESS = "andrewkreid63@gmail.com"
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")

# Data collection functions
def fetch_biznow_articles():
    """Scrape latest CRE articles from BizNow"""
    try:
        response = requests.get("https://www.biznow.com", timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Look for recent articles (adjust selectors based on actual BizNow structure)
        for item in soup.find_all('article', limit=10):
            title = item.find('h2') or item.find('h3')
            link = item.find('a')
            if title and link:
                articles.append({
                    'source': 'BizNow',
                    'title': title.get_text(strip=True),
                    'url': link.get('href', ''),
                    'date': datetime.now().isoformat()
                })
        return articles
    except Exception as e:
        print(f"Error fetching BizNow: {e}")
        return []

def fetch_la_biz_journal():
    """Fetch LA Business Journal CRE news"""
    try:
        # LA Biz Journal commercial real estate section
        url = "https://www.bizjournals.com/losangeles/real_estate"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        for item in soup.find_all('div', class_='story-item', limit=10):
            title = item.find('h3')
            link = item.find('a')
            if title and link:
                articles.append({
                    'source': 'LA Business Journal',
                    'title': title.get_text(strip=True),
                    'url': link.get('href', ''),
                    'date': datetime.now().isoformat()
                })
        return articles
    except Exception as e:
        print(f"Error fetching LA Biz Journal: {e}")
        return []

def fetch_sd_union_tribune():
    """Fetch San Diego Union-Tribune real estate section"""
    try:
        url = "https://www.sandiegouniontribune.com/business/real-estate"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        for item in soup.find_all('a', limit=10):
            if item.find('h2') or item.find('h3'):
                title = item.find('h2') or item.find('h3')
                if title:
                    articles.append({
                        'source': 'San Diego Union-Tribune',
                        'title': title.get_text(strip=True),
                        'url': item.get('href', ''),
                        'date': datetime.now().isoformat()
                    })
        return articles
    except Exception as e:
        print(f"Error fetching SD Union-Tribune: {e}")
        return []

def fetch_broker_reports():
    """Fetch latest broker market reports (CBRE, Cushman, JLL, Newmark, Colliers)"""
    brokers = {
        'CBRE': 'https://www.cbre.com/research',
        'Cushman & Wakefield': 'https://www.cushmanwakefield.com/en/research',
        'JLL': 'https://www.jll.com/en/research',
        'Newmark': 'https://www.nmrk.com/en/research',
        'Colliers': 'https://www.colliers.com/en/research'
    }
    
    reports = []
    for broker, url in brokers.items():
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for recent reports (selectors may vary)
            for item in soup.find_all('a', limit=3):
                if 'southern' in item.get_text().lower() or 'california' in item.get_text().lower() or 'socal' in item.get_text().lower():
                    reports.append({
                        'broker': broker,
                        'title': item.get_text(strip=True),
                        'url': item.get('href', ''),
                        'date': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"Error fetching {broker} reports: {e}")
    
    return reports

def fetch_fred_data():
    """Fetch economic data from Federal Reserve (Treasury, SOFR)"""
    try:
        data = {}
        
        # 10-Year Treasury Yield
        if FRED_API_KEY:
            response = requests.get(
                f"https://api.stlouisfed.org/fred/series/data",
                params={
                    'series_id': 'DGS10',
                    'api_key': FRED_API_KEY,
                    'file_type': 'json',
                    'limit': 1
                },
                timeout=10
            )
            if response.status_code == 200:
                fred_data = response.json()
                if fred_data.get('observations'):
                    data['treasury_10y'] = {
                        'value': fred_data['observations'][-1].get('value'),
                        'date': fred_data['observations'][-1].get('date')
                    }
            
            # SOFR Rate
            response = requests.get(
                f"https://api.stlouisfed.org/fred/series/data",
                params={
                    'series_id': 'SOFR',
                    'api_key': FRED_API_KEY,
                    'file_type': 'json',
                    'limit': 1
                },
                timeout=10
            )
            if response.status_code == 200:
                fred_data = response.json()
                if fred_data.get('observations'):
                    data['sofr'] = {
                        'value': fred_data['observations'][-1].get('value'),
                        'date': fred_data['observations'][-1].get('date')
                    }
        
        return data
    except Exception as e:
        print(f"Error fetching FRED data: {e}")
        return {}

def fetch_market_data():
    """Fetch S&P 500 and REIT data"""
    try:
        data = {}
        
        # S&P 500 (using Alpha Vantage or similar - you may need an API key)
        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    'function': 'GLOBAL_QUOTE',
                    'symbol': '^GSPC',
                    'apikey': os.getenv('ALPHAVANTAGE_API_KEY', 'demo')
                },
                timeout=10
            )
            if response.status_code == 200:
                quote = response.json().get('Global Quote', {})
                data['sp500'] = {
                    'price': quote.get('05. price'),
                    'change': quote.get('09. change'),
                    'change_percent': quote.get('10. change percent')
                }
        except:
            pass
        
        # Major REITs (office, industrial, multifamily, retail)
        reit_symbols = {
            'Multifamily': ['AVB', 'EQR', 'MAA'],  # AvalonBay, Equity Residential, Mid-America
            'Industrial': ['DLR', 'PLD', 'WELL'],  # Digital Realty, Prologis, Welltower
            'Office': ['VNO', 'SL', 'JBGS'],  # Vornado, Salesforce (subsidiary), JBG SMITH
            'Retail': ['SPG', 'WRI', 'KIM']  # Simon Property, Whitestone REIT, Kimco
        }
        
        data['reits'] = {}
        for asset_class, symbols in reit_symbols.items():
            data['reits'][asset_class] = []
            for symbol in symbols:
                try:
                    response = requests.get(
                        "https://www.alphavantage.co/query",
                        params={
                            'function': 'GLOBAL_QUOTE',
                            'symbol': symbol,
                            'apikey': os.getenv('ALPHAVANTAGE_API_KEY', 'demo')
                        },
                        timeout=10
                    )
                    if response.status_code == 200:
                        quote = response.json().get('Global Quote', {})
                        data['reits'][asset_class].append({
                            'symbol': symbol,
                            'price': quote.get('05. price'),
                            'change_percent': quote.get('10. change percent')
                        })
                except:
                    pass
        
        return data
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return {}

def synthesize_with_claude(articles, reports, economic_data, market_data):
    """Use Claude API to synthesize data into a daily brief"""
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        prompt = f"""
You are a commercial real estate analyst specializing in Southern California markets. 
Based on the following data, write a 10-15 minute daily CRE brief for an investor.

The brief should:
1. Start with a national/macro snapshot (Treasury, SOFR, S&P 500, major REIT performance)
2. Highlight key SoCal market trends (by asset class: office, industrial, multifamily, retail)
3. Flag significant price/cap rate movements
4. Summarize the most important news and broker reports
5. Identify any new developments, approvals, or major deals

Format it as a readable email newsletter. Be concise but insightful. Focus on actionable insights.

NEWS ARTICLES:
{json.dumps(articles, indent=2)}

BROKER REPORTS:
{json.dumps(reports, indent=2)}

ECONOMIC DATA:
{json.dumps(economic_data, indent=2)}

MARKET DATA:
{json.dumps(market_data, indent=2)}
"""
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text
    except Exception as e:
        print(f"Error synthesizing with Claude: {e}")
        return f"Error generating brief: {e}"

def send_email(subject, body):
    """Send email via Gmail"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = GMAIL_ADDRESS
        
        # Create HTML version
        html = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto;">
      <h2 style="color: #0066cc;">SoCal CRE Daily Brief</h2>
      <p style="color: #666; font-size: 12px;">{datetime.now().strftime('%B %d, %Y')}</p>
      <hr style="border: none; border-top: 1px solid #ddd;">
      {body.replace(chr(10), '<br>')}
      <hr style="border: none; border-top: 1px solid #ddd;">
      <p style="font-size: 11px; color: #999;">This is an automated daily brief. Market data sources: BizNow, LA Business Journal, SD Union-Tribune, CBRE, Cushman & Wakefield, JLL, Newmark, Colliers, Federal Reserve.</p>
    </div>
  </body>
</html>
"""
        
        msg.attach(MIMEText(html, 'html'))
        
        # Connect and send via Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email sent successfully to {GMAIL_ADDRESS}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    """Main function - orchestrate the entire brief generation"""
    print(f"Starting SoCal CRE Brief generation at {datetime.now()}")
    
    # Collect data
    print("Fetching articles...")
    articles = []
    articles.extend(fetch_biznow_articles())
    articles.extend(fetch_la_biz_journal())
    articles.extend(fetch_sd_union_tribune())
    
    print("Fetching broker reports...")
    reports = fetch_broker_reports()
    
    print("Fetching economic data...")
    economic_data = fetch_fred_data()
    
    print("Fetching market data...")
    market_data = fetch_market_data()
    
    # Synthesize with Claude
    print("Synthesizing brief with Claude...")
    brief_content = synthesize_with_claude(articles, reports, economic_data, market_data)
    
    # Send email
    print("Sending email...")
    subject = f"SoCal CRE Daily Brief - {datetime.now().strftime('%A, %B %d, %Y')}"
    send_email(subject, brief_content)
    
    print("Done!")

if __name__ == "__main__":
    main()

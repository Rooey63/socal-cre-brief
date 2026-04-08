#!/usr/bin/env python3
"""
Update dashboard data with latest market information
"""

import json
import os
from datetime import datetime
import requests

def fetch_dashboard_data():
    """Fetch all data needed for the dashboard"""
    data = {
        'timestamp': datetime.now().isoformat(),
        'metrics': {}
    }
    
    # 10-Year Treasury Yield
    try:
        fred_api_key = os.getenv('FRED_API_KEY')
        if fred_api_key:
            response = requests.get(
                "https://api.stlouisfed.org/fred/series/data",
                params={
                    'series_id': 'DGS10',
                    'api_key': fred_api_key,
                    'file_type': 'json',
                    'limit': 1
                },
                timeout=10
            )
            if response.status_code == 200:
                fred_data = response.json()
                if fred_data.get('observations'):
                    latest = fred_data['observations'][-1]
                    data['metrics']['treasury_10y'] = {
                        'value': float(latest.get('value', 0)),
                        'date': latest.get('date'),
                        'label': '10-Year Treasury Yield'
                    }
    except Exception as e:
        print(f"Error fetching Treasury data: {e}")
    
    # SOFR Rate
    try:
        fred_api_key = os.getenv('FRED_API_KEY')
        if fred_api_key:
            response = requests.get(
                "https://api.stlouisfed.org/fred/series/data",
                params={
                    'series_id': 'SOFR',
                    'api_key': fred_api_key,
                    'file_type': 'json',
                    'limit': 1
                },
                timeout=10
            )
            if response.status_code == 200:
                fred_data = response.json()
                if fred_data.get('observations'):
                    latest = fred_data['observations'][-1]
                    data['metrics']['sofr'] = {
                        'value': float(latest.get('value', 0)),
                        'date': latest.get('date'),
                        'label': 'SOFR Rate'
                    }
    except Exception as e:
        print(f"Error fetching SOFR data: {e}")
    
    # S&P 500
    try:
        api_key = os.getenv('ALPHAVANTAGE_API_KEY', 'demo')
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={
                'function': 'GLOBAL_QUOTE',
                'symbol': '^GSPC',
                'apikey': api_key
            },
            timeout=10
        )
        if response.status_code == 200:
            quote = response.json().get('Global Quote', {})
            data['metrics']['sp500'] = {
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%'),
                'label': 'S&P 500',
                'timestamp': quote.get('07. latest trading day')
            }
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
    
    # Major REITs
    reit_symbols = {
        'Multifamily': [
            {'symbol': 'AVB', 'name': 'AvalonBay Communities'},
            {'symbol': 'EQR', 'name': 'Equity Residential'},
            {'symbol': 'MAA', 'name': 'Mid-America Apartment'}
        ],
        'Industrial': [
            {'symbol': 'DLR', 'name': 'Digital Realty'},
            {'symbol': 'PLD', 'name': 'Prologis'},
            {'symbol': 'WELL', 'name': 'Welltower'}
        ],
        'Office': [
            {'symbol': 'VNO', 'name': 'Vornado Realty'},
            {'symbol': 'SL', 'name': 'Salesforce Real Estate'},
            {'symbol': 'JBGS', 'name': 'JBG SMITH'}
        ],
        'Retail': [
            {'symbol': 'SPG', 'name': 'Simon Property Group'},
            {'symbol': 'WRI', 'name': 'Whitestone REIT'},
            {'symbol': 'KIM', 'name': 'Kimco Realty'}
        ]
    }
    
    data['reits'] = {}
    api_key = os.getenv('ALPHAVANTAGE_API_KEY', 'demo')
    
    for asset_class, reits in reit_symbols.items():
        data['reits'][asset_class] = []
        for reit in reits:
            try:
                response = requests.get(
                    "https://www.alphavantage.co/query",
                    params={
                        'function': 'GLOBAL_QUOTE',
                        'symbol': reit['symbol'],
                        'apikey': api_key
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    quote = response.json().get('Global Quote', {})
                    data['reits'][asset_class].append({
                        'symbol': reit['symbol'],
                        'name': reit['name'],
                        'price': float(quote.get('05. price', 0)),
                        'change_percent': quote.get('10. change percent', '0%'),
                        'timestamp': quote.get('07. latest trading day')
                    })
            except Exception as e:
                print(f"Error fetching {reit['symbol']}: {e}")
    
    return data

def main():
    """Fetch and save dashboard data"""
    print("Updating dashboard data...")
    
    data = fetch_dashboard_data()
    
    # Ensure dashboard directory exists
    os.makedirs('dashboard', exist_ok=True)
    
    # Save to JSON
    with open('dashboard/data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Dashboard data saved: {data['timestamp']}")

if __name__ == "__main__":
    main()

import pandas as pd
import requests
import time

def get_ticker(company_name):
    yfinance = "https://query2.finance.yahoo.com/v1/finance/search"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
    params = {"q": company_name, "quotes_count": 10, "country": "United States"}

    res = requests.get(url=yfinance, params=params, headers={'User-Agent': user_agent})
    data = res.json()

    # Lists of U.S. exchange codes, with major exchanges prioritized
    major_us_exchanges = ['NYQ', 'NMS', 'NGM', 'ASE', 'NYE', 'AMX', 'BATS', 'CBOE', 'IEXG']
    otc_exchanges = ['OTC', 'OTCQB', 'OTCQX', 'PINK']

    # First, search in major exchanges
    for quote in data.get('quotes', []):
        if quote.get('exchange') in major_us_exchanges:
            return quote.get('symbol', 'N/A')

    # If not found, search in OTC exchanges
    for quote in data.get('quotes', []):
        if quote.get('exchange') in otc_exchanges:
            return quote.get('symbol', 'N/A')
    
    return 'N/A'

def find_stock_tickers(file_path):
    # Load the Excel file
    df = pd.read_csv(file_path)

    # Iterate over the company names and search for their stock tickers
    for index, row in df.iterrows():
        print(f'Searching for ticker of {row["Brand"]}..., {index}')
        ticker = get_ticker(row['Brand'])
        df.at[index, 'Ticker'] = ticker
        # Sleep for 0.5 seconds to avoid getting blocked by Yahoo Finance
        time.sleep(0.5)
        print(f'Ticker for {row["Brand"]}: {ticker}')

    # Save the updated dataframe back to Excel
    updated_file_path = file_path.replace('.csv', '_with_tickers.csv')
    df.to_excel(updated_file_path, index=False)
    return updated_file_path

# Call the function with the path to your Excel file
file_path = "C:/Users/batuh/OneDrive/Documents/Workstation/BrandStockReturns/BrandData/unique_companies.csv"

updated_file_path = find_stock_tickers(file_path)
print(f'Updated file saved to: {updated_file_path}')
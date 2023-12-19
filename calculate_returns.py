import pandas as pd
import yfinance as yf
from datetime import datetime
import math

def get_annual_return(ticker, year):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    # print(f'Getting data for {ticker} from {start_date} to {end_date}')
    data = yf.download(ticker, start=start_date, end=end_date)
    # print(f'Data: {data}')
    # Ensure there is data for both the start and end of the year
    if not data.empty:
        start_price = data.iloc[0]['Open']
        end_price = data.iloc[-1]['Close']
        return (end_price - start_price) / start_price
    else:
        return None

def load_ticker_mapping(mapping_file_path):
    return pd.read_excel(mapping_file_path).set_index('Brand')['Ticker'].to_dict()

def load_brand_rankings(year, rankings_directory, most_improved=False, weighted=False):
    rankings_file_path = f"{rankings_directory}/brandirectory-ranking-data-global-{year}.csv"
    rankings = pd.read_csv(rankings_file_path)

    # Convert 'Previous Position' to numeric, coercing non-numeric values to NaN
    rankings['Previous Position'] = pd.to_numeric(rankings['Previous Position'], errors='coerce')
    # Fill NaN values with a large number to minimize their effect
    rankings['Previous Position'] = rankings['Previous Position'].fillna(1000)
    # Calculate the position change
    rankings['Position Change'] = rankings['Previous Position'] - rankings['Position']

    if most_improved:
        if weighted:
            # Apply weighting: the smaller the previous position, the larger the weight for the same position change
            rankings['Weighted Change'] = rankings['Position Change'] / rankings['Previous Position']
            # Sort by weighted change, higher is better
            top_movers = rankings.sort_values(by='Weighted Change', ascending=False).head(10)['Brand']
        else:
            # Sort by exact position change, higher is better
            top_movers = rankings.sort_values(by='Position Change', ascending=False).head(10)['Brand']
        return top_movers
    else:
        top_brands = rankings.head(10)['Brand']
        return top_brands


def calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory, most_improved=False, weighted=False):
    annual_returns = {}
    for year in range(start_year, end_year + 1):
        brands = load_brand_rankings(year, rankings_directory, most_improved, weighted)
        tickers = [ticker_mapping.get(brand) for brand in brands if (ticker_mapping.get(brand, 'N/A') != 'N/A' and not (type(ticker_mapping.get(brand))==float and math.isnan(ticker_mapping.get(brand))))]
        print(f"Tickers for {year}: {tickers}")
        if not tickers:
            continue
        individual_returns = [get_annual_return(ticker, year) for ticker in tickers if ticker is not None]
        annual_returns[year] = sum(individual_returns) / len(individual_returns) if individual_returns else None
    return annual_returns

def get_market_return(index_ticker, start_year, end_year):
    market_returns = {}
    for year in range(start_year, end_year + 1):
        market_returns[year] = get_annual_return(index_ticker, year)
    return market_returns

def main(rankings_directory):
    ticker_mapping = load_ticker_mapping('BrandData/CompanyToTicker_with_tickers.xlsx')
    
    # Calculate returns for top 10 brands
    top_brand_returns = calculate_returns_for_brands(ticker_mapping, 2022, 2023, rankings_directory)
    # Calculate returns for 10 most improved brands based on exact position change
    most_improved_brand_returns_exact = calculate_returns_for_brands(ticker_mapping, 2022, 2023, rankings_directory, most_improved=True, weighted=False)
    # Calculate returns for 10 most improved brands based on weighted position change
    most_improved_brand_returns_weighted = calculate_returns_for_brands(ticker_mapping, 2022, 2023, rankings_directory, most_improved=True, weighted=True)
    
    market_returns = get_market_return('^GSPC', 2022, 2023)

    for year in range(2022, 2024):
        print(f"Year: {year}")
        print(f"Top 10 Brands Average Return: {top_brand_returns.get(year, 'N/A')}")
        print(f"Top 10 Most Improved Brands Average Return (Exact): {most_improved_brand_returns_exact.get(year, 'N/A')}")
        print(f"Top 10 Most Improved Brands Average Return (Weighted): {most_improved_brand_returns_weighted.get(year, 'N/A')}")
        print(f"S&P 500 Market Return: {market_returns.get(year, 'N/A')}")

if __name__ == "__main__":
    rankings_directory = 'BrandData' # Set this to the directory containing the ranking CSV files
    main(rankings_directory)
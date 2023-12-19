import pandas as pd
import yfinance as yf
from datetime import datetime
import math
from scipy.stats import mstats

def get_returns(ticker, year):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    data = yf.download(ticker, start=start_date, end=end_date, interval='1mo')

    # Calculate the monthly returns by comparing the open price of the month to the close price of the same month
    monthly_returns = []
    for i in range(len(data)):
        open_price = data['Open'].iloc[i]
        close_price = data['Adj Close'].iloc[i]
        monthly_return = (close_price / open_price) - 1
        monthly_returns.append(monthly_return)

    yearly_return = data['Adj Close'].iloc[-1] / data['Adj Close'].iloc[0] - 1
    return monthly_returns, yearly_return

def calculate_cagr_yearly(start_value, end_value, number_of_years):
    """
    Calculate the Compound Annual Growth Rate (CAGR).
    """
    if number_of_years <= 0:
        raise ValueError("Number of years must be positive")

    return (end_value / start_value) ** (1 / number_of_years) - 1

def calculate_performance_metrics(monthly_returns):
    # Assuming monthly_returns is a list of monthly returns
    monthly_returns_series = pd.Series(monthly_returns)
    # Calculate Sharpe Ratio using a risk-free rate, assuming it to be 0 for simplicity
    excess_returns = monthly_returns_series  # Assuming no risk-free rate
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * (12 ** 0.5)  # Annualize Sharpe Ratio
    # Add more metrics like Sortino, Treynor, Max Drawdown, VaR, etc.
    # ...
    return {
        'sharpe_ratio': sharpe_ratio,
        # ... other metrics
    }

def calculate_cagr(returns):
    """
    Calculate the Compound Annual Growth Rate (CAGR).
    Assumes the returns are monthly and compounds them over the total period.
    """
    # Convert returns to multipliers and calculate the product
    multipliers = [1 + r for r in returns]
    total_return = pd.Series(multipliers).prod()

    # Number of years is the total months divided by 12
    periods = len(returns) / 12
    cagr = (total_return ** (1 / periods)) - 1
    return cagr

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
    monthly_returns = {}
    yearly_returns = {}
    for year in range(start_year, end_year + 1):
        brands = load_brand_rankings(year, rankings_directory, most_improved, weighted)
        tickers = [ticker_mapping.get(brand) for brand in brands if (ticker_mapping.get(brand, 'N/A') != 'N/A' and not (type(ticker_mapping.get(brand))==float and math.isnan(ticker_mapping.get(brand))))]
        print(f"Tickers for {year}: {tickers}")
        if not tickers:
            continue
        all_returns, yearly_returns_list= zip(*[get_returns(ticker, year) for ticker in tickers if ticker is not None])
        avg_yearly_return = sum(yearly_returns_list) / len(yearly_returns_list)
        average_monthly_returns = [sum(month) / len(month) for month in zip(*all_returns)]
        print("Number of months: ", len(average_monthly_returns))
        monthly_returns[year] = average_monthly_returns
        yearly_returns[year] = avg_yearly_return
    return monthly_returns, yearly_returns

def get_market_monthly_returns(index_ticker, start_year, end_year):
    market_returns = {}
    market_yearly_returns = {}
    for year in range(start_year, end_year + 1):
        market_returns[year], market_yearly_returns[year] = get_returns(index_ticker, year)
    return market_returns, market_yearly_returns

def main(rankings_directory, start_year=2022, end_year=2022):
    ticker_mapping = load_ticker_mapping('BrandData/CompanyToTicker_with_tickers.xlsx')
    
    # Calculate monthly returns for top 10 brands
    top_brand_monthly_returns, top_brand_yearly_returns = calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory)
    # Calculate monthly returns for 10 most improved brands based on exact position change
    most_improved_monthly_returns_exact, most_improved_yearly_returns_exact = calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory, most_improved=True, weighted=False)
    # Calculate monthly returns for 10 most improved brands based on weighted position change
    most_improved_monthly_returns_weighted, most_improved_yearly_returns_weighted = calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory, most_improved=True, weighted=True)
    
    market_monthly_returns, market_yearly_returns = get_market_monthly_returns('^GSPC', start_year, end_year)

    total_monthly_returns_top_brands = []
    total_monthly_returns_most_improved_exact = []
    total_monthly_returns_most_improved_weighted = []
    total_monthly_returns_market = []

    total_yearly_returns_top_brands = []
    total_yearly_returns_most_improved_exact = []
    total_yearly_returns_most_improved_weighted = []
    total_yearly_returns_market = []

    for year in range(start_year, end_year+1):
        print(f"Year: {year}")
        
        # Calculate performance metrics for top 10 brands
        top_brand_metrics = calculate_performance_metrics(top_brand_monthly_returns.get(year, []))
        print(f"Top 10 Brands Sharpe Ratio: {top_brand_metrics.get('sharpe_ratio', 'N/A')}, Yearly returns: {top_brand_yearly_returns.get(year, [])}")
        
        # Calculate performance metrics for most improved brands (exact)
        most_improved_metrics_exact = calculate_performance_metrics(most_improved_monthly_returns_exact.get(year, []))
        print(f"Top 10 Most Improved Brands Sharpe Ratio (Exact): {most_improved_metrics_exact.get('sharpe_ratio', 'N/A')} Yearly returns: {most_improved_yearly_returns_exact.get(year, [])}")
        
        # Calculate performance metrics for most improved brands (weighted)
        most_improved_metrics_weighted = calculate_performance_metrics(most_improved_monthly_returns_weighted.get(year, []))
        print(f"Top 10 Most Improved Brands Sharpe Ratio (Weighted): {most_improved_metrics_weighted.get('sharpe_ratio', 'N/A')}, Yearly returns: {most_improved_yearly_returns_weighted.get(year, [])}")
        
        # Calculate performance metrics for the market
        market_metrics = calculate_performance_metrics(market_monthly_returns.get(year, []))
        print(f"S&P 500 Market Sharpe Ratio: {market_metrics.get('sharpe_ratio', 'N/A')}, Yearly returns: {market_yearly_returns.get(year, [])}")

        total_monthly_returns_top_brands.extend(top_brand_monthly_returns.get(year, []))
        total_monthly_returns_most_improved_exact.extend(most_improved_monthly_returns_exact.get(year, []))
        total_monthly_returns_most_improved_weighted.extend(most_improved_monthly_returns_weighted.get(year, []))
        total_monthly_returns_market.extend(market_monthly_returns.get(year, []))

        total_yearly_returns_top_brands.append(top_brand_yearly_returns.get(year, []))
        total_yearly_returns_most_improved_exact.append(most_improved_yearly_returns_exact.get(year, []))
        total_yearly_returns_most_improved_weighted.append(most_improved_yearly_returns_weighted.get(year, []))
        total_yearly_returns_market.append(market_yearly_returns.get(year, []))


    # Calculate Sharpe Ratios at the end
    net_sharpe_ratio_top_brands = calculate_performance_metrics(total_monthly_returns_top_brands)['sharpe_ratio']
    net_sharpe_ratio_most_improved_exact = calculate_performance_metrics(total_monthly_returns_most_improved_exact)['sharpe_ratio']
    net_sharpe_ratio_most_improved_weighted = calculate_performance_metrics(total_monthly_returns_most_improved_weighted)['sharpe_ratio']
    net_sharpe_ratio_market = calculate_performance_metrics(total_monthly_returns_market)['sharpe_ratio']

    # Calculate CAGRs at the end
    avg_yearly_returns_top_brands = sum(total_yearly_returns_top_brands) / len(total_yearly_returns_top_brands)
    avg_yearly_returns_most_improved_exact = sum(total_yearly_returns_most_improved_exact) / len(total_yearly_returns_most_improved_exact)
    avg_yearly_returns_most_improved_weighted = sum(total_yearly_returns_most_improved_weighted) / len(total_yearly_returns_most_improved_weighted)
    avg_yearly_returns_market = sum(total_yearly_returns_market) / len(total_yearly_returns_market)

    # Print Net Sharpe Ratios
    print(f"Net Sharpe Ratio for Top 10 Brands: {net_sharpe_ratio_top_brands}, Yearly returns: {avg_yearly_returns_top_brands}")
    print(f"Net Sharpe Ratio for Most Improved Brands (Exact): {net_sharpe_ratio_most_improved_exact}, Yearly returns: {avg_yearly_returns_most_improved_exact}")
    print(f"Net Sharpe Ratio for Most Improved Brands (Weighted): {net_sharpe_ratio_most_improved_weighted}, Yearly returns: {avg_yearly_returns_most_improved_weighted}")
    print(f"Net Sharpe Ratio for S&P 500 Market: {net_sharpe_ratio_market}, Yearly returns: {avg_yearly_returns_market}")

if __name__ == "__main__":
    rankings_directory = 'BrandData' # Set this to the directory containing the ranking CSV files
    main(rankings_directory, start_year=2021, end_year=2023)
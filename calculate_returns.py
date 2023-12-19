import pandas as pd
import yfinance as yf
from datetime import datetime
import math
from scipy.stats import mstats
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import numpy as np

def get_returns(ticker, year):
    start_date = f"{year-1}-12-01"
    end_date = f"{year}-12-31"
    data = yf.download(ticker, start=start_date, end=end_date, interval='1mo')
    
    if len(data) < 12:
        return [], 0
    
    # Calculate the monthly returns by comparing the open price of the month to the close price of the same month
    monthly_returns = []
    for i in range(1, len(data)):
        prev_close_price = data['Adj Close'].iloc[i-1]
        current_close_price = data['Adj Close'].iloc[i]
        monthly_return = (current_close_price / prev_close_price) - 1
        monthly_returns.append(monthly_return)

    yearly_return = data['Adj Close'].iloc[-1] / data['Adj Close'].iloc[0] - 1
    return monthly_returns, yearly_return

def create_pdf(pdf_path, table_data):
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter  # Get the dimensions of the page
    
    # Cumulative Returns
    image = ImageReader("data/cumulative_returns.png")
    c.drawImage(image, 50, height - 350, width=500, height=300)  # Adjust the position and size as needed

    # Yearly Returns
    image = ImageReader("data/yearly_returns.png")
    c.drawImage(image, 50, height - 700, width=500, height=300)  # Adjust the position and size as needed

    # Net Returns and Sharpe Ratios
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ])
    table = Table(table_data, colWidths=[width/len(table_data[0])] * len(table_data[0]), hAlign='LEFT')
    table.setStyle(table_style)
    
    table.wrapOn(c, width, height)
    table.drawOn(c, 30, height - 800)  # Adjust as needed

    c.save()

def calculate_performance_metrics(monthly_returns):
    # Assuming monthly_returns is a list of monthly returns
    monthly_returns_series = pd.Series(monthly_returns)
    # Calculate Sharpe Ratio using a risk-free rate, assuming it to be 0 for simplicity
    excess_returns = monthly_returns_series  # Assuming no risk-free rate
    print(f'Excess returns: {excess_returns}, mean: {excess_returns.mean()}, std: {excess_returns.std()}')
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * (12 ** 0.5)  # Annualize Sharpe Ratio
    # Add more metrics like Sortino, Treynor, Max Drawdown, VaR, etc.
    # ...
    return {
        'sharpe_ratio': sharpe_ratio,
        # ... other metrics
    }

def calculate_net_returns(yearly_returns):
    """
    Calculate the net cumulative return over multiple years.
    """
    if not yearly_returns:
        return 0

    cumulative_return = 1
    for yr_return in yearly_returns:
        cumulative_return *= (1 + yr_return)

    # Subtract 1 to get the net return
    net_return = cumulative_return - 1
    return net_return

def load_ticker_mapping(mapping_file_path):
    return pd.read_excel(mapping_file_path).set_index('Brand')['Ticker'].to_dict()

def load_brand_rankings(year, rankings_directory, most_improved=False, weighted=False, number_of_brands=10):
    rankings_file_path = f"{rankings_directory}/brandirectory-ranking-data-global-{year}.csv"
    rankings = pd.read_csv(rankings_file_path)

    # Convert 'Previous Position' to numeric, coercing non-numeric values to NaN
    rankings['Previous Position'] = pd.to_numeric(rankings['Previous Position'], errors='coerce')
    # Fill NaN values with a large number to minimize their effect
    rankings['Previous Position'] = rankings['Previous Position'].fillna(501)
    # Calculate the position change
    rankings['Position Change'] = rankings['Previous Position'] - rankings['Position']

    if most_improved:
        if weighted:
            # Apply weighting: the smaller the previous position, the larger the weight for the same position change
            rankings['Weighted Change'] = rankings['Position Change'] / rankings['Previous Position']
            # Sort by weighted change, higher is better
            top_movers = rankings.sort_values(by='Weighted Change', ascending=False).head(number_of_brands)['Brand']
        else:
            # Sort by exact position change, higher is better
            top_movers = rankings.sort_values(by='Position Change', ascending=False).head(number_of_brands)['Brand']
        return top_movers
    else:
        top_brands = rankings.head(number_of_brands)['Brand']
        return top_brands

def calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory, number_of_brands, most_improved=False, weighted=False):
    monthly_returns = {}
    yearly_returns = {}
    for year in range(start_year, end_year + 1):
        brands = load_brand_rankings(year, rankings_directory, most_improved, weighted, number_of_brands)
        tickers = [ticker_mapping.get(brand) for brand in brands if (ticker_mapping.get(brand, 'N/A') != 'N/A' and not (type(ticker_mapping.get(brand))==float and math.isnan(ticker_mapping.get(brand))))]
        print(f"Tickers for {year}: {tickers}")
        if not tickers:
            continue
        all_returns, yearly_returns_list= zip(*[get_returns(ticker, year) for ticker in tickers if ticker is not None])
        avg_yearly_return = sum(yearly_returns_list) / len(yearly_returns_list)
        average_monthly_returns = [sum(month) / len(month) for month in zip(*all_returns)]
        monthly_returns[year] = average_monthly_returns
        yearly_returns[year] = avg_yearly_return
    return monthly_returns, yearly_returns

def get_market_monthly_returns(index_ticker, start_year, end_year):
    market_returns = {}
    market_yearly_returns = {}
    for year in range(start_year, end_year + 1):
        market_returns[year], market_yearly_returns[year] = get_returns(index_ticker, year)
    return market_returns, market_yearly_returns

def plot_cumulative_returns(total_yearly_returns_top_brands, total_yearly_returns_most_improved_exact, total_yearly_returns_most_improved_weighted, total_yearly_returns_market, start_year, end_year):
    plt.clf()
    # Plot the cumulative returns over time from yearly returns.
    cumulative_returns_top_brands, cumulative_returns_most_improved_exact, cumulative_returns_most_improved_weighted, cumulative_returns_market = [1], [1], [1], [1]
    for i in range(len(total_yearly_returns_market)):
        cumulative_returns_top_brands.append(cumulative_returns_top_brands[-1] * (1 + total_yearly_returns_top_brands[i]))
        cumulative_returns_most_improved_exact.append(cumulative_returns_most_improved_exact[-1] * (1 + total_yearly_returns_most_improved_exact[i]))
        cumulative_returns_most_improved_weighted.append(cumulative_returns_most_improved_weighted[-1] * (1 + total_yearly_returns_most_improved_weighted[i]))
        cumulative_returns_market.append(cumulative_returns_market[-1] * (1 + total_yearly_returns_market[i]))

    # Plot the cumulative returns
    print(f'Cumulative Returns: {cumulative_returns_top_brands}')
    plt.plot(cumulative_returns_top_brands, label='Top Brands')
    plt.plot(cumulative_returns_most_improved_exact, label='Most Improved Brands (Exact)')
    plt.plot(cumulative_returns_most_improved_weighted, label='Most Improved Brands (Weighted)')
    plt.plot(cumulative_returns_market, label='S&P 500 Market')

    # Add labels and legend
    plt.xlabel('Year')
    plt.ylabel('Cumulative Returns')

    # Add xticks starting from start_year-1(2020) to end_year+1(2022)
    plt.xticks(range(len(total_yearly_returns_market)+1), range(start_year-1, end_year+1))
    
    plt.legend()
    plt.savefig('data/cumulative_returns.png', format='png')

def plot_yearly_returns(total_yearly_returns_top_brands, total_yearly_returns_most_improved_exact, total_yearly_returns_most_improved_weighted, total_yearly_returns_market, start_year, end_year):
    # Reset the plot
    plt.clf()

    # Number of groups (years)
    num_groups = len(total_yearly_returns_market)

    # Positions for the bars on the x-axis
    bar_width = 0.2
    index = np.arange(num_groups)

    # Plot each strategy
    plt.bar(index, total_yearly_returns_top_brands, bar_width, label='Top Brands')
    plt.bar(index + bar_width, total_yearly_returns_most_improved_exact, bar_width, label='Most Improved Brands (Exact)')
    plt.bar(index + 2 * bar_width, total_yearly_returns_most_improved_weighted, bar_width, label='Most Improved Brands (Weighted)')
    plt.bar(index + 3 * bar_width, total_yearly_returns_market, bar_width, label='S&P 500 Market')

    # Add labels and legend
    plt.xlabel('Year')
    plt.ylabel('Yearly Returns')
    plt.title('Yearly Returns by Strategy')
    plt.xticks(index + bar_width, range(start_year, end_year + 1))
    plt.legend()

    # Save the figure
    plt.savefig('data/yearly_returns.png', format='png')

def table_net_returns_and_sharpe_ratios(annualized_return_top_brands, annualized_return_most_improved_exact, annualized_return_most_improved_weighted, annualized_return_market, net_sharpe_ratio_top_brands, net_sharpe_ratio_most_improved_exact, net_sharpe_ratio_most_improved_weighted, net_sharpe_ratio_market):
    # Create a table with the net returns and Sharpe Ratios
    table_data = [
        ['Top Brands', annualized_return_top_brands, net_sharpe_ratio_top_brands],
        ['Most Improved Brands (Exact)', annualized_return_most_improved_exact, net_sharpe_ratio_most_improved_exact],
        ['Most Improved Brands (Weighted)', annualized_return_most_improved_weighted, net_sharpe_ratio_most_improved_weighted],
        ['S&P 500 Market', annualized_return_market, net_sharpe_ratio_market]
    ]
    table = pd.DataFrame(table_data, columns=['', 'Annualized Return', 'Net Sharpe Ratio'])
    table_data = table.values.tolist()
    # Add header row
    header = table.columns.to_list()
    table_data.insert(0, header)
    return table_data

def main(rankings_directory, start_year=2022, end_year=2022, calculate_top_brands=True, calculate_most_improved_exact=True, calculate_most_improved_weighted=True, calculate_market=True, number_of_brands=10):
    ticker_mapping = load_ticker_mapping('BrandData/CompanyToTicker_with_tickers.xlsx')
    
    if calculate_top_brands:
        top_brand_monthly_returns, top_brand_yearly_returns = calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory, number_of_brands)
    if calculate_most_improved_exact:
        most_improved_monthly_returns_exact, most_improved_yearly_returns_exact = calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory, number_of_brands, most_improved=True, weighted=False)
    if calculate_most_improved_weighted:
        most_improved_monthly_returns_weighted, most_improved_yearly_returns_weighted = calculate_returns_for_brands(ticker_mapping, start_year, end_year, rankings_directory, number_of_brands, most_improved=True, weighted=True)
    if calculate_market:
        market_monthly_returns, market_yearly_returns = get_market_monthly_returns('^GSPC', start_year, end_year)

    total_monthly_returns_top_brands, total_monthly_returns_most_improved_exact, total_monthly_returns_most_improved_weighted, total_monthly_returns_market = [], [], [], []
    total_yearly_returns_top_brands, total_yearly_returns_most_improved_exact, total_yearly_returns_most_improved_weighted, total_yearly_returns_market = [], [], [], []

    for year in range(start_year, end_year+1):
        print(f"Year: {year}")

        if calculate_top_brands:
            top_brand_metrics = calculate_performance_metrics(top_brand_monthly_returns.get(year, []))
            total_monthly_returns_top_brands.extend(top_brand_monthly_returns.get(year, []))
            total_yearly_returns_top_brands.append(top_brand_yearly_returns.get(year, []))
            print(f"Top 10 Brands Sharpe Ratio: {top_brand_metrics.get('sharpe_ratio', 'N/A')}, Yearly returns: {top_brand_yearly_returns.get(year, [])}")

        if calculate_most_improved_exact:
            most_improved_metrics_exact = calculate_performance_metrics(most_improved_monthly_returns_exact.get(year, []))
            total_monthly_returns_most_improved_exact.extend(most_improved_monthly_returns_exact.get(year, []))
            total_yearly_returns_most_improved_exact.append(most_improved_yearly_returns_exact.get(year, []))
            print(f"Top 10 Most Improved Brands Sharpe Ratio (Exact): {most_improved_metrics_exact.get('sharpe_ratio', 'N/A')} Yearly returns: {most_improved_yearly_returns_exact.get(year, [])}")        

        if calculate_most_improved_weighted:
            most_improved_metrics_weighted = calculate_performance_metrics(most_improved_monthly_returns_weighted.get(year, []))
            total_monthly_returns_most_improved_weighted.extend(most_improved_monthly_returns_weighted.get(year, []))
            total_yearly_returns_most_improved_weighted.append(most_improved_yearly_returns_weighted.get(year, []))
            print(f"Top 10 Most Improved Brands Sharpe Ratio (Weighted): {most_improved_metrics_weighted.get('sharpe_ratio', 'N/A')}, Yearly returns: {most_improved_yearly_returns_weighted.get(year, [])}")

        if calculate_market:        
            market_metrics = calculate_performance_metrics(market_monthly_returns.get(year, []))
            total_monthly_returns_market.extend(market_monthly_returns.get(year, []))
            total_yearly_returns_market.append(market_yearly_returns.get(year, []))
            print(f"S&P 500 Market Sharpe Ratio: {market_metrics.get('sharpe_ratio', 'N/A')}, Yearly returns: {market_yearly_returns.get(year, [])}")


    print("-"*50)

    if calculate_top_brands:
        net_return_top_brands = calculate_net_returns(total_yearly_returns_top_brands)
        annualized_return_top_brands = (1 + net_return_top_brands) ** (1/len(total_yearly_returns_top_brands)) - 1
        net_sharpe_ratio_top_brands = calculate_performance_metrics(total_monthly_returns_top_brands)['sharpe_ratio']
        print(f"Net Sharpe Ratio for Top 10 Brands: {net_sharpe_ratio_top_brands}, Annualized returns: {annualized_return_top_brands}")
    
    if calculate_most_improved_exact:
        net_return_most_improved_exact = calculate_net_returns(total_yearly_returns_most_improved_exact)
        annualized_return_most_improved_exact = (1 + net_return_most_improved_exact) ** (1/len(total_yearly_returns_most_improved_exact)) - 1
        net_sharpe_ratio_most_improved_exact = calculate_performance_metrics(total_monthly_returns_most_improved_exact)['sharpe_ratio']
        print(f"Net Sharpe Ratio for Most Improved Brands (Exact): {net_sharpe_ratio_most_improved_exact}, Annualized returns: {annualized_return_most_improved_exact}")

    if calculate_most_improved_weighted:
        net_return_most_improved_weighted = calculate_net_returns(total_yearly_returns_most_improved_weighted)
        annualized_return_most_improved_weighted = (1 + net_return_most_improved_weighted) ** (1/len(total_yearly_returns_most_improved_weighted)) - 1
        net_sharpe_ratio_most_improved_weighted = calculate_performance_metrics(total_monthly_returns_most_improved_weighted)['sharpe_ratio']
        print(f"Net Sharpe Ratio for Most Improved Brands (Weighted): {net_sharpe_ratio_most_improved_weighted}, Annualized returns: {annualized_return_most_improved_weighted}")
    
    if calculate_market:
        net_return_market = calculate_net_returns(total_yearly_returns_market)
        annualized_return_market = (1 + net_return_market) ** (1/len(total_yearly_returns_market)) - 1
        net_sharpe_ratio_market = calculate_performance_metrics(total_monthly_returns_market)['sharpe_ratio']
        print(f"Net Sharpe Ratio for S&P 500 Market: {net_sharpe_ratio_market}, Annualized returns: {annualized_return_market}")

    plot_yearly_returns(total_yearly_returns_top_brands, total_yearly_returns_most_improved_exact, total_yearly_returns_most_improved_weighted, total_yearly_returns_market, start_year, end_year)

    plot_cumulative_returns(total_yearly_returns_top_brands, total_yearly_returns_most_improved_exact, total_yearly_returns_most_improved_weighted, total_yearly_returns_market, start_year, end_year)
    table_data = table_net_returns_and_sharpe_ratios(annualized_return_top_brands, annualized_return_most_improved_exact, annualized_return_most_improved_weighted, annualized_return_market, net_sharpe_ratio_top_brands, net_sharpe_ratio_most_improved_exact, net_sharpe_ratio_most_improved_weighted, net_sharpe_ratio_market)
    pdf_path = 'data/analysis_report.pdf'
    create_pdf(pdf_path, table_data)

if __name__ == "__main__":
    rankings_directory = 'BrandData'
    main(rankings_directory, start_year=2017, end_year=2022, calculate_top_brands=True, calculate_most_improved_exact=True, calculate_most_improved_weighted=True, calculate_market=True, number_of_brands=10)
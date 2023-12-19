# Brand Performance Analysis in Stock Market
## Project Overview
This project investigates the performance of top global brands in the stock market compared to standard market indices. Utilizing data from various sources, the script calculates and analyzes the financial performance of stocks associated with leading and rapidly improving brands. The core hypothesis is that top and improving brands may outperform the market.

## Research Background
The project is inspired by multiple research studies indicating a correlation between brand value and stock performance.
### Relavent Links
https://www.sciencedirect.com/science/article/pii/S2405844018321789 \
https://alphaarchitect.com/2022/09/brand-values-and-long-term-stock-returns/ \
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4146667 \
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6446061/ \
https://www.reddit.com/r/investing/comments/pxsq91/should_you_invest_in_the_most_reputable_brands_in/


## Repository Structure
analysis_script.py: Main Python script for data analysis and PDF report generation. \
BrandData/: Directory containing brand-to-ticker mappings and historical brand rankings. \
data/: Folder for storing intermediate data files and generated plots.

## Key Features
Data Extraction: Utilizes yfinance for historical stock data. \
Performance Metrics: Calculates Sharpe Ratio, annualized returns. \
PDF Reporting: Generates a comprehensive report of the analysis in PDF format. \
Visualization: Includes functions for plotting cumulative and yearly returns.

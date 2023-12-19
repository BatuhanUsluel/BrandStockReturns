import os
import glob
import pandas as pd

# Assuming the files are CSV and are stored in a specific directory
file_directory = 'BrandData/'  # Adjust this to the directory where the files are stored
file_pattern = 'brandirectory-ranking-data-global-*.csv'  # Pattern to match the files

# Collect all file paths
file_paths = glob.glob(os.path.join(file_directory, file_pattern))

# Function to extract unique company names from a file
def extract_unique_companies(file_path):
    print(f'Processing file: {file_path}')
    try:
        df = pd.read_csv(file_path)
        # Assuming the column with company names is named 'Brand'
        # Adjust this if the column name is different
        company_names = df['Brand'].unique()
        return set(company_names)
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return set()

# Set to store all unique company names
all_unique_companies = set()

# Iterate over each file and update the set of unique company names
for file_path in file_paths:
    unique_companies = extract_unique_companies(file_path)
    all_unique_companies.update(unique_companies)

# Display the number of unique companies found
len(all_unique_companies)

# Save the unique company names to a CSV file
unique_companies_file = 'unique_companies.csv'
pd.Series(list(all_unique_companies)).to_csv(unique_companies_file, index=False)
print(f'Unique companies saved to: {unique_companies_file}')
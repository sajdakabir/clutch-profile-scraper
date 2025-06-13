#!/usr/bin/env python3
"""
update_missing_urls.py
────────────────────────────────────────────────────────────────────
A script to find and update only the missing website URLs in the output file.
"""

import os
import sys
import time
import random
import pandas as pd
from datetime import datetime

# Configuration
INPUT_CSV = "processed_first_1k - processed_first_1k.csv.csv"
OUTPUT_CSV = "clutch_with_sites.csv"
SLEEP_BETWEEN = (3, 6)  # Random delay between requests

def print_status(message: str, status_type: str = "info") -> None:
    """Print status message with timestamp and color coding"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status_type == "success":
        prefix = "✅"
    elif status_type == "warning":
        prefix = "⚠️"
    elif status_type == "error":
        prefix = "❌"
    else:
        prefix = "ℹ️"
    print(f"[{timestamp}] {prefix} {message}")

def main():
    # Load the input data
    try:
        input_df = pd.read_csv(INPUT_CSV)
        print_status(f"Loaded {len(input_df)} companies from {INPUT_CSV}", "success")
    except Exception as e:
        print_status(f"Failed to load {INPUT_CSV}: {str(e)}", "error")
        sys.exit(1)
    
    # Load existing output data or create new
    if os.path.exists(OUTPUT_CSV):
        try:
            output_df = pd.read_csv(OUTPUT_CSV)
            print_status(f"Loaded existing output with {len(output_df)} rows", "info")
            
            # Ensure all input rows are in the output
            merged_df = pd.merge(
                input_df, 
                output_df[['clutch_profile_url', 'company_website_url']], 
                on='clutch_profile_url', 
                how='left'
            )
            
            # Find rows with missing website URLs
            missing_mask = (merged_df['company_website_url'].isna()) | \
                         (merged_df['company_website_url'] == '') | \
                         (merged_df['company_website_url'].str.contains('NOT_FOUND|ERROR|INVALID|TIMEOUT', case=False, na=True))
            
            missing_df = merged_df[missing_mask].copy()
            
            if len(missing_df) == 0:
                print_status("No missing website URLs found. All rows are complete!", "success")
                return
                
            print_status(f"Found {len(missing_df)} rows with missing or invalid website URLs", "info")
            
            # Update the output file with the merged data
            # This ensures we have all input rows, even if some were missing from the output
            merged_df.to_csv(OUTPUT_CSV, index=False)
            print_status(f"Updated {OUTPUT_CSV} with all input rows", "success")
            
            # Now run the scraper on just the missing rows
            print_status("Run the continue_scraping.py script to process the missing URLs", "info")
            print_status("Command: source venv/bin/activate && python continue_scraping.py", "info")
            
        except Exception as e:
            print_status(f"Error processing files: {str(e)}", "error")
            sys.exit(1)
    else:
        print_status("No existing output file found. Creating a new one...", "warning")
        # Create a new output file with all input rows
        input_df.to_csv(OUTPUT_CSV, index=False)
        print_status(f"Created new {OUTPUT_CSV} with {len(input_df)} rows", "success")
        print_status("Run the continue_scraping.py script to process the URLs", "info")
        print_status("Command: source venv/bin/activate && python continue_scraping.py", "info")

if __name__ == "__main__":
    main()

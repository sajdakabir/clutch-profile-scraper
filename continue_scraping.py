#!/usr/bin/env python3
"""
continue_scraping.py
────────────────────────────────────────────────────────────────────
A modified version of the Clutch scraper that continues from where it left off.
Starts from row 415 and appends to the existing output file.
"""

import os
import random
import sys
import time
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse, urlunparse
from typing import Tuple

# Third-party imports
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)

# Configuration
INPUT_CSV = "processed_first_1k - processed_first_1k.csv.csv"
OUTPUT_CSV = "clutch_with_sites.csv"
TEMP_CSV = "clutch_temp.csv"
HEADLESS = True
WAIT_SHORT = 20
MAX_RETRIES = 2
SLEEP_BETWEEN = (3, 6)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
START_ROW = 414  # 0-based index, so 414 means row 415

class ScraperError(Exception):
    """Custom exception for scraping errors"""
    pass

def print_status(message: str, status_type: str = "info") -> None:
    """Print status message with timestamp and color coding"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status_type == "success":
        prefix = "✅"
    elif status_type == "warning":
        prefix = "⚠️"
    elif status_type == "error":
        prefix = "❌"
    elif status_type == "info":
        prefix = "ℹ️"
    else:
        prefix = "➡️"
    
    print(f"[{timestamp}] {prefix} {message}")

def save_progress(df: pd.DataFrame, output_file: str) -> None:
    """Save progress to the output file"""
    try:
        # Save to a temporary file first
        temp_file = output_file + ".tmp"
        df.to_csv(temp_file, index=False)
        
        # If successful, rename the temp file to the output file
        if os.path.exists(temp_file):
            if os.path.exists(output_file):
                os.remove(output_file)
            os.rename(temp_file, output_file)
        
        print_status(f"Progress saved to {output_file}", "success")
    except Exception as e:
        print_status(f"Failed to save progress: {str(e)}", "error")

def setup_driver() -> uc.Chrome:
    """Set up and return a configured Chrome WebDriver"""
    try:
        options = uc.ChromeOptions()
        
        if HEADLESS:
            options.add_argument('--headless=new')
        
        options.add_argument('--disable-blink-features=AutomationScript')
        options.add_argument('--disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={USER_AGENT}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--profile-directory=Default')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--disable-default-apps')
        options.add_argument('--window-size=1920,1080')
        
        print_status("Launching Chrome with undetected-chromedriver...")
        
        driver = uc.Chrome(
            options=options,
            use_subprocess=True
        )
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print_status(f"Failed to initialize WebDriver: {str(e)}", "error")
        raise ScraperError("WebDriver initialization failed") from e

def clean_url(url: str) -> str:
    """Extract just the base domain from a URL."""
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return url
        
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception as e:
        print_status(f"Error cleaning URL {url}: {str(e)}", "error")
        return url

def get_company_website(clutch_url: str, driver: uc.Chrome, attempt: int = 1) -> Tuple[str, str]:
    """Returns a tuple of (company_website_url, status)"""
    try:
        print_status(f"Attempt {attempt}: Scraping {clutch_url}")
        
        try:
            driver.get(clutch_url)
            time.sleep(2)
            
            if "challenge" in driver.current_url.lower() or "cloudflare" in driver.page_source.lower():
                print_status("Detected Cloudflare challenge, waiting...", "warning")
                time.sleep(10)
            
            selectors = [
                "a.sg-button-v2--primary[href*='r.clutch.co/redirect']",
                "a[href*='r.clutch.co/redirect'][href*='u=']",
                "a[href*='website'][class*='button']",
                "a:contains('Visit Website')"
            ]
            
            redirect_href = None
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    redirect_href = element.get_attribute("href")
                    if redirect_href and "redirect" in redirect_href:
                        break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not redirect_href:
                print_status("No redirect button found, parsing page source...", "warning")
                soup = BeautifulSoup(driver.page_source, "html.parser")
                for a in soup.find_all("a", href=True):
                    if "r.clutch.co/redirect" in a["href"] and "u=" in a["href"]:
                        redirect_href = a["href"]
                        break
            
            if not redirect_href:
                print_status(f"⚠️  Couldn't find redirect link on {clutch_url}", "warning")
                return "WEBSITE_NOT_FOUND", "not_found"
                
            parsed = urlparse(redirect_href)
            query_params = parse_qs(parsed.query)
            actual_url = query_params.get("u", [""])[0]
            
            if not actual_url:
                print_status(f"No URL found in redirect: {redirect_href}", "warning")
                return "INVALID_REDIRECT", "invalid_redirect"
                
            decoded_url = unquote(actual_url)
            cleaned_url = clean_url(decoded_url)
            print_status(f"Successfully extracted URL: {cleaned_url}", "success")
            return cleaned_url, "success"
            
        except TimeoutException as te:
            print_status(f"Timeout while loading {clutch_url}: {str(te)}", "warning")
            return "TIMEOUT", "timeout"
            
    except WebDriverException as we:
        print_status(f"WebDriver error on {clutch_url}: {str(we)}", "error")
        return "WEBDRIVER_ERROR", "webdriver_error"
        
    except Exception as e:
        print_status(f"Unexpected error on {clutch_url}: {str(e)}", "error")
        return f"ERROR_{type(e).__name__}", "error"

def main():
    # Check if input file exists
    if not os.path.exists(INPUT_CSV):
        print_status(f"Input file not found: {INPUT_CSV}", "error")
        sys.exit(1)
    
    # Load input data
    try:
        df = pd.read_csv(INPUT_CSV)
        print_status(f"Loaded {len(df)} companies from {INPUT_CSV}", "success")
    except Exception as e:
        print_status(f"Failed to load {INPUT_CSV}: {str(e)}", "error")
        sys.exit(1)
    
    # Initialize results DataFrame
    if os.path.exists(OUTPUT_CSV):
        try:
            # Read existing output to get the last processed row
            existing_df = pd.read_csv(OUTPUT_CSV)
            print_status(f"Found existing output file with {len(existing_df)} rows", "info")
            
            # If we already have all rows, exit
            if len(existing_df) >= len(df):
                print_status("Output file already contains all results. Exiting.", "info")
                return
                
            # Start from the next row after the last one in the output file
            start_row = len(existing_df)
        except Exception as e:
            print_status(f"Error reading existing output: {str(e)}. Starting from scratch.", "warning")
            start_row = 0
    else:
        start_row = 0
    
    # Ensure we start from at least START_ROW
    start_row = max(start_row, START_ROW)
    
    # If we've already processed all rows, exit
    if start_row >= len(df):
        print_status(f"Already processed all rows up to {len(df)}. Exiting.", "info")
        return
    
    print_status(f"Starting from row {start_row + 1} of {len(df)}")
    
    # Initialize WebDriver
    try:
        driver = setup_driver()
    except ScraperError as e:
        print_status(f"Failed to initialize WebDriver: {str(e)}", "error")
        sys.exit(1)
    
    try:
        # Process each row starting from start_row
        for idx in range(start_row, len(df)):
            row = df.iloc[idx]
            url = row["clutch_profile_url"]
            print_status(f"Processing {idx + 1}/{len(df)}: {url}")
            
            # Scrape the website URL
            result, status = get_company_website(url, driver)
            
            # Create or update the output file
            output_data = {
                'company_name': row.get('company_name', ''),
                'clutch_profile_url': url,
                'company_website_url': result,
                'scrape_status': status,
                'scrape_timestamp': datetime.now().isoformat()
            }
            
            # Append to the output file
            output_df = pd.DataFrame([output_data])
            header = not os.path.exists(OUTPUT_CSV) or os.path.getsize(OUTPUT_CSV) == 0
            output_df.to_csv(OUTPUT_CSV, mode='a', header=header, index=False)
            
            # Random delay between requests
            delay = random.uniform(*SLEEP_BETWEEN)
            print_status(f"Waiting {delay:.1f} seconds before next request...")
            time.sleep(delay)
    
    except KeyboardInterrupt:
        print_status("\nScript interrupted by user. Progress has been saved.", "warning")
    
    except Exception as e:
        print_status(f"Unexpected error: {str(e)}", "error")
    
    finally:
        # Clean up
        try:
            driver.quit()
            print_status("WebDriver closed", "info")
        except:
            pass
        
        print_status("Scraping completed.", "success")

if __name__ == "__main__":
    main()

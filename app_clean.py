#!/usr/bin/env python3
"""
scrape_clutch_sites_uc.py
────────────────────────────────────────────────────────────────────
• Reads  top_10_clutch_companies.csv
    └─ must contain column: clutch_profile_url  (plus any others you like)

• Writes clutch_with_sites.csv
    └─ adds column: company_website_url  (the real site behind Clutch's redirect)

How it works
────────────
1. Spins up an undetected-chromedriver instance (Chromium + stealth patches).
2. Opens each Clutch profile, waits for the JS to finish, and grabs the
   "Visit Website" redirect link.
3. Extracts the actual company URL from the  u=  query parameter.
"""

# Standard library imports
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

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
INPUT_CSV = "top_10_clutch_companies.csv"
OUTPUT_CSV = "clutch_with_sites.csv"
TEMP_CSV = "clutch_temp.csv"  # For saving progress
HEADLESS = True                # set False to watch the browser for debugging
WAIT_SHORT = 20                # seconds to wait for "Visit Website" button
MAX_RETRIES = 2                # Number of retries for failed attempts
SLEEP_BETWEEN = (3, 6)         # polite random delay between pages
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

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
    """Save progress to a temporary file"""
    try:
        temp_file = output_file + ".tmp"
        df.to_csv(temp_file, index=False)
        df.to_csv(output_file, index=False)
        if os.path.exists(temp_file):
            os.remove(temp_file)
        print_status(f"Progress saved to {output_file}", "success")
    except Exception as e:
        print_status(f"Failed to save progress: {str(e)}", "error")

def setup_driver() -> uc.Chrome:
    """Set up and return a configured Chrome WebDriver"""
    try:
        options = uc.ChromeOptions()
        
        # Basic options
        if HEADLESS:
            options.add_argument('--headless=new')
        
        # Disable automation flags that trigger bot detection
        options.add_argument('--disable-blink-features=AutomationScript')
        options.add_argument('--disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={USER_AGENT}')
        
        # Disable automation control
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Disable extensions and automation flags
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--profile-directory=Default')
        options.add_argument('--disable-plugins-discovery')
        options.add_argument('--disable-default-apps')
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        
        print_status("Launching Chrome with undetected-chromedriver...")
        
        # Initialize the driver with options
        driver = uc.Chrome(
            options=options,
            use_subprocess=True
        )
        
        # Additional stealth settings
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    except Exception as e:
        print_status(f"Failed to initialize WebDriver: {str(e)}", "error")
        raise ScraperError("WebDriver initialization failed") from e

def clean_url(url: str) -> str:
    """
    Extract just the base domain from a URL.
    
    Args:
        url: The URL to clean
        
    Returns:
        The base domain (e.g., 'example.com')
    """
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return url
        
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Extract just the netloc (domain) part
        domain = parsed.netloc
        
        # Remove 'www.' if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        return domain
        
    except Exception as e:
        print_status(f"Error cleaning URL {url}: {str(e)}", "error")
        return url

def get_company_website(clutch_url: str, driver: uc.Chrome, attempt: int = 1) -> Tuple[str, str]:
    """
    Returns a tuple of (company_website_url, status)
    """
    try:
        print_status(f"Attempt {attempt}: Scraping {clutch_url}")
        
        # Navigate to the URL
        try:
            driver.get(clutch_url)
            time.sleep(2)  # Initial page load
            
            # Check for Cloudflare or other challenges
            if "challenge" in driver.current_url.lower() or "cloudflare" in driver.page_source.lower():
                print_status("Detected Cloudflare challenge, waiting...", "warning")
                time.sleep(10)  # Wait for Cloudflare to resolve
            
            # Try different selectors for the website button
            selectors = [
                "a.sg-button-v2--primary[href*='r.clutch.co/redirect']",  # Primary button
                "a[href*='r.clutch.co/redirect'][href*='u=']",  # Any redirect link
                "a[href*='website'][class*='button']",  # Generic website button
                "a:contains('Visit Website')"  # Text-based fallback
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
            
            # If no redirect found in buttons, try parsing HTML directly
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
                
            # Extract the actual URL
            parsed = urlparse(redirect_href)
            query_params = parse_qs(parsed.query)
            actual_url = query_params.get("u", [""])[0]
            
            if not actual_url:
                print_status(f"No URL found in redirect: {redirect_href}", "warning")
                return "INVALID_REDIRECT", "invalid_redirect"
                
            decoded_url = unquote(actual_url)
            # Clean the URL to get just the base domain
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

def main() -> None:
    # Check if input file exists
    if not os.path.exists(INPUT_CSV):
        print_status(f"Input file not found: {INPUT_CSV}", "error")
        sys.exit(1)
    
    # Load data
    try:
        df = pd.read_csv(INPUT_CSV)
        print_status(f"Loaded {len(df)} companies from {INPUT_CSV}", "success")
    except Exception as e:
        print_status(f"Failed to load {INPUT_CSV}: {str(e)}", "error")
        sys.exit(1)
    
    # Check if we have previous progress
    if os.path.exists(OUTPUT_CSV):
        print_status(f"Found existing output file: {OUTPUT_CSV}", "warning")
        try:
            existing_df = pd.read_csv(OUTPUT_CSV)
            if "company_website_url" in existing_df.columns and len(existing_df) == len(df):
                print_status("Output file already contains all results. Exiting.", "info")
                return
            elif "company_website_url" in existing_df.columns:
                print_status("Resuming from previous progress...", "info")
                df = existing_df
        except Exception as e:
            print_status(f"Error reading existing output: {str(e)}", "error")
    
    # Initialize results with only the columns we need
    required_columns = ['company_name', 'clutch_profile_url', 'company_website_url']
    
    # Create a new DataFrame with only the required columns
    if all(col in df.columns for col in required_columns):
        df = df[required_columns].copy()
    else:
        # If the required columns don't exist, create them
        df = df.copy()
        if 'clutch_profile_url' not in df.columns and len(df.columns) > 0:
            df['clutch_profile_url'] = df.iloc[:, 0]  # Assume first column is URL if not found
        if 'company_name' not in df.columns:
            df['company_name'] = ''
        if 'company_website_url' not in df.columns:
            df['company_website_url'] = ''
        df = df[['company_name', 'clutch_profile_url', 'company_website_url']]
    
    # Initialize status tracking
    df["scrape_status"] = ""
    df["scrape_attempts"] = 0
    
    # Setup WebDriver
    try:
        driver = setup_driver()
    except ScraperError as e:
        print_status(f"Failed to initialize WebDriver: {str(e)}", "error")
        sys.exit(1)
    
    try:
        total = len(df)
        for idx, row in df.iterrows():
            # Skip already processed rows
            if pd.notna(row.get("company_website_url")) and row.get("company_website_url") != "":
                if row.get("scrape_status") == "success":
                    print_status(f"Skipping already processed ({idx+1}/{total}): {row['clutch_profile_url']}", "info")
                    continue
            
            url = row["clutch_profile_url"]
            print_status(f"Processing {idx+1}/{total}: {url}")
            
            # Retry logic
            max_attempts = row.get("scrape_attempts", 0) + MAX_RETRIES + 1
            result = ""
            status = ""
            
            for attempt in range(1, max_attempts + 1):
                result, status = get_company_website(url, driver, attempt)
                
                # If successful or unrecoverable error, break the retry loop
                if status == "success" or status in ["not_found", "invalid_redirect"]:
                    break
                    
                # Exponential backoff
                wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                print_status(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            
            # Update DataFrame with the scraped URL
            df.at[idx, "company_website_url"] = result
            df.at[idx, "scrape_status"] = status
            df.at[idx, "scrape_attempts"] = attempt
            
            # Prepare output with only the required columns
            output_df = df[['company_name', 'clutch_profile_url', 'company_website_url']].copy()
            
            # Save progress after each successful/failed attempt
            save_progress(output_df, OUTPUT_CSV)
            
            # Random delay between requests
            delay = random.uniform(*SLEEP_BETWEEN)
            print_status(f"Waiting {delay:.1f} seconds before next request...")
            time.sleep(delay)
    
    except KeyboardInterrupt:
        print_status("\nScript interrupted by user. Saving progress...", "warning")
    
    except Exception as e:
        print_status(f"Unexpected error: {str(e)}", "error")
    
    finally:
        # Clean up
        try:
            driver.quit()
            print_status("WebDriver closed", "info")
        except:
            pass
        
        # Final save
        try:
            # Prepare final output with only the required columns
            output_df = df[['company_name', 'clutch_profile_url', 'company_website_url']].copy()
            save_progress(output_df, OUTPUT_CSV)
            print_status(f"Final results saved to {OUTPUT_CSV}", "success")
            
            # Print summary
            success_count = (df["scrape_status"] == "success").sum()
            print_status(f"\nScraping complete! Success: {success_count}/{len(df)}", "success")
            
            # Clean up temp file if it exists
            if os.path.exists(TEMP_CSV):
                os.remove(TEMP_CSV)
                
        except Exception as e:
            print_status(f"Error during final save: {str(e)}", "error")

if __name__ == "__main__":
    main()

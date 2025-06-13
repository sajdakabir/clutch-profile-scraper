# Clutch.co Profile Scraper

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A robust Python-based web scraping tool designed to extract company profile information and website URLs from Clutch.co profiles. This tool is particularly useful for lead generation, market research, and business intelligence gathering.

## ✨ Features

- 🚀 **Efficient Scraping**: Extract company website URLs from Clutch.co profiles
- 🔄 **Resume Capability**: Continue interrupted scraping sessions
- 🛡 **Anti-detection**: Uses undetected-chromedriver to avoid bot detection
- 📊 **CSV Integration**: Easy import/export of data in CSV format
- ⚡ **Fast & Reliable**: Multi-threaded processing for better performance
- 📝 **Detailed Logging**: Comprehensive status updates and error reporting

## 📋 Prerequisites

- Python 3.7 or higher
- Google Chrome browser installed
- ChromeDriver (will be handled automatically by webdriver-manager)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/clutch-profile-scraper.git
   cd clutch-profile-scraper
   ```

2. **Set up a virtual environment** (recommended)
   ```bash
   # For Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # For macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🏃‍♂️ Quick Start

1. **Prepare your input file**
   - Place your CSV file with Clutch.co profile URLs in the `data` directory
   - Ensure the file has a column containing the profile URLs
   - The script will automatically detect URL columns

2. **Run the scraper**
   ```bash
   python app.py
   ```

3. **View results**
   - The script will create a `clutch_with_sites.csv` file with the results
   - Progress is saved automatically, so you can stop and resume anytime

## 🛠 Scripts

- `app.py`: Main scraping script
- `continue_scraping.py`: Resume interrupted scraping sessions
- `merge_csv.py`: Merge multiple CSV files
- `single_url.py`: Test scraping for a single URL
- `update_missing_urls.py`: Update missing URLs in the dataset

## ⚙️ Configuration

Edit the configuration section in `app.py` to customize:

```python
# Input/Output files
INPUT_CSV = "data/extracted_urls_20250604_161856.csv"  # Your input file
OUTPUT_CSV = "clutch_with_sites.csv"  # Output file
TEMP_CSV = "clutch_temp.csv"  # Temporary progress file

# Browser settings
HEADLESS = True  # Set to False to see the browser
WAIT_SHORT = 20  # Seconds to wait for elements
MAX_RETRIES = 2  # Number of retries for failed attempts
SLEEP_BETWEEN = (3, 6)  # Random delay between requests (min, max) seconds
```

## 📂 Project Structure

```
.
├── data/                      # Directory for input/output files
│   └── extracted_urls_20250604_161856.csv  # Example input file
├── app.py                    # Main scraping script
├── app_clean.py              # Cleaned version of the main script
├── continue_scraping.py      # Resume interrupted sessions
├── merge_csv.py              # Merge multiple CSV files
├── single_url.py             # Test script for single URL
├── update_missing_urls.py    # Update missing URLs
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💡 Support

For support, please:
- Open an issue in the GitHub repository
- Or contact the maintainer directly

## 📊 Performance

- Processes approximately 100-200 profiles per hour (varies based on website response times)
- Includes automatic retries and error handling
- Saves progress to prevent data loss

## 🔗 Integration with ContactHarvest

This tool pairs perfectly with [ContactHarvest](https://github.com/sajdakabir/ContactHarvest) to enrich your Clutch.co data with contact information using the Apollo.io API.

### Combined Workflow:

1. **Scrape Company Data** (this tool)
   ```bash
   python app.py
   ```
   Output: `clutch_with_sites.csv` with company names and websites

2. **Enrich with Contact Information**
   ```bash
   # Install ContactHarvest
   pip install git+https://github.com/sajdakabir/ContactHarvest.git
   
   # Run with your Apollo.io API key
   python -m contactharvest input.csv enriched_output.csv --api-key YOUR_APOLLO_API_KEY
   ```

### Enriched Output Includes:
- Company name
- Company website
- Contact person's name
- Job title
- Email address
- LinkedIn profile URL

### Requirements for ContactHarvest:
- Apollo.io API key
- Python 3.7+
- Internet connection

> **Note:** Make sure to comply with Apollo.io's terms of service and data usage policies when using their API.

## ⚠️ Legal Notice

This tool is for educational and research purposes only. Please ensure you comply with Clutch.co's Terms of Service and use this tool responsibly. The developers are not responsible for any misuse or damage caused by this software.

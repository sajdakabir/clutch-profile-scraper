import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote

def get_company_website(clutch_url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    res = requests.get(clutch_url, headers=headers, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    link_tag = soup.find("a", class_="sg-button-v2--primary")
    if not link_tag:
        return "Website not found"

    href = link_tag.get("href", "")
    if not href.startswith("https://r.clutch.co/redirect"):
        return "Unexpected link format"

    parsed = urlparse(href)
    params = parse_qs(parsed.query)
    url_encoded = params.get("u", [""])[0]

    return unquote(url_encoded) if url_encoded else "Website not found"


print(get_company_website("https://clutch.co/profile/andersen"))

"""Scraper settings."""

BASE_URL = "https://www.olx.ua"

# Search URL, not the category URL: the /apple/ category is redirected
# to the general smartphone list and its pagination returns page 1 again.
SEARCH_URL = (
    f"{BASE_URL}/uk/elektronika/telefony-i-aksesuary/"
    "mobilnye-telefony-smartfony/q-iphone/"
)

DB_NAME = "olx_apple.db"

PAGES = 3
DELAY = 2.0
REQUEST_TIMEOUT = 30

APPLE_KEYWORDS = ("iphone", "айфон", "apple")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
}

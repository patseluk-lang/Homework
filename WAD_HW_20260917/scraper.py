"""Downloading OLX pages and parsing listing cards with BeautifulSoup."""

import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from config import (
    APPLE_KEYWORDS,
    BASE_URL,
    DELAY,
    HEADERS,
    PAGES,
    REQUEST_TIMEOUT,
    SEARCH_URL,
)

# OLX blocks the requests library by TLS fingerprint, so curl_cffi is
# preferred. Plain requests is kept as a fallback so the module still
# imports and can parse locally saved pages.
try:
    from curl_cffi import requests as http

    CLIENT_OPTIONS = {"impersonate": "chrome"}
except ImportError:
    import requests as http

    CLIENT_OPTIONS = {}


def get_html(url):
    """Return the HTML of a page or raise RuntimeError."""
    try:
        response = http.get(
            url, headers=HEADERS, timeout=REQUEST_TIMEOUT, **CLIENT_OPTIONS
        )
        response.raise_for_status()
    except Exception as error:
        raise RuntimeError(f"Could not download {url}: {error}")
    return response.text


def page_url(page):
    return SEARCH_URL if page == 1 else f"{SEARCH_URL}?page={page}"


def clean_url(href):
    """Strip query parameters.

    OLX appends search_reason to listing links, so the same ad appears
    under different URLs and the UNIQUE constraint stops working.
    """
    parts = urlsplit(urljoin(BASE_URL, href))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def is_apple(title):
    """OLX mixes promoted ads of other brands into the search results."""
    lowered = title.lower()
    return any(keyword in lowered for keyword in APPLE_KEYWORDS)


def parse_price(price_text):
    """'17 500 грн.' -> 17500; negotiable or foreign currency -> None."""
    if not price_text or "грн" not in price_text.lower():
        return None
    digits = re.sub(r"\D", "", price_text.split("грн")[0])
    return int(digits) if digits else None


def text_of(element):
    return element.get_text(" ", strip=True) if element else ""


def parse_card(card):
    """Return a dict with one listing, or None if the card is not usable."""
    # The title is taken from the heading tag, not from the
    # ad-card-title container, which also holds the price.
    title_element = card.select_one("h4") or card.select_one("h6")
    link_element = card.select_one("a[href]")

    if not title_element or not link_element:
        return None

    title = text_of(title_element)
    if not title or not is_apple(title):
        return None

    price_text = text_of(card.select_one("p[data-testid='ad-price']"))
    location_date = text_of(card.select_one("p[data-testid='location-date']"))

    location, _, published = location_date.partition(" - ")

    return {
        "title": title,
        "price_text": price_text or None,
        "price_uah": parse_price(price_text),
        "location": location.strip() or None,
        "published": published.strip() or None,
        "url": clean_url(link_element["href"]),
    }


def parse_page(html):
    """Parse the HTML of a single listing page."""
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select("div[data-testid='l-card']")
    if not cards:
        cards = soup.select("div[data-cy='l-card']")

    products = []
    for card in cards:
        product = parse_card(card)
        if product:
            products.append(product)
    return products


def scrape(pages=PAGES):
    """Download the given number of pages and return the listings."""
    products = []
    for page in range(1, pages + 1):
        url = page_url(page)
        print(f"[+] Page {page}: {url}")

        try:
            html = get_html(url)
        except RuntimeError as error:
            print(f"[!] {error}")
            break

        page_products = parse_page(html)
        print(f"    Apple listings found: {len(page_products)}")

        if not page_products:
            with open(f"debug_page_{page}.html", "w", encoding="utf-8") as file:
                file.write(html)
            print(f"    HTML saved to debug_page_{page}.html")

        products.extend(page_products)

        if page < pages:
            time.sleep(DELAY)

    return products


def scrape_files(paths):
    """Parse locally saved HTML pages."""
    products = []
    for path in paths:
        with open(path, encoding="utf-8") as file:
            html = file.read()

        page_products = parse_page(html)
        print(f"[+] {path}: Apple listings found: {len(page_products)}")
        products.extend(page_products)
    return products

# OLX Apple Phones Scraper

Web scraping of Apple mobile phone listings from OLX.ua with BeautifulSoup,
storing the collected data in an SQLite database.

## Task

Use Python and the BeautifulSoup library to collect product data (Apple mobile
phones) from the OLX website and save that data into an SQLite database.

## Stack

- Python 3
- BeautifulSoup 4 — HTML parsing
- curl_cffi — HTTP requests (requests as a fallback)
- sqlite3 — storage (Python standard library)

## Project structure

```text
olx_scraper/
├── config.py         # settings: URLs, database name, headers
├── scraper.py        # downloading pages and parsing cards
├── database.py       # SQLite: table, inserts, queries
├── main.py           # entry point
├── requirements.txt
└── README.md
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
```

## Usage

Scrape live pages from OLX:

```bash
python main.py
```

Parse locally saved HTML pages instead (see *Offline re-parsing of saved pages*
below):

```bash
python main.py page1.html page2.html
```

## Collected data

Table `phones` in `olx_apple.db`:

| Field | Description |
| --- | --- |
| `id` | Primary key |
| `title` | Listing title |
| `price_text` | Price as shown on the page |
| `price_uah` | Price as an integer, `NULL` for negotiable or foreign currency |
| `location` | City |
| `published` | Publication date as shown on the page |
| `url` | Listing URL, unique key |
| `created_at` | Insertion timestamp |

## Implementation notes

**curl_cffi instead of requests.** OLX answers `403 Forbidden` to the requests
library regardless of the headers sent — the block is based on the TLS
fingerprint of the client. `curl_cffi` with `impersonate="chrome"` passes.
Parsing is still done with BeautifulSoup. If `curl_cffi` is not installed, the
module falls back to `requests`, so saved pages can still be parsed.

**Search URL instead of the category URL.** The category URL ending in
`/apple/` is redirected by OLX to the general smartphone listing, and its
pagination returns the same first page over and over. The search URL `q-iphone`
paginates correctly.

**Title taken from the heading tag.** The title is read from `h4` / `h6` rather
than from the `ad-card-title` container, which also holds the price and would
glue the two values together.

**Title filter.** Titles are checked against the keywords `iphone`, `айфон` and
`apple` to drop promoted ads of other brands that OLX injects into the results.

**Query parameters stripped from URLs.** OLX appends a `search_reason`
parameter to listing links, so the same ad appears under different URLs. Only
the path is stored, which keeps the `UNIQUE` constraint working across runs.

**Price parsed only for hryvnia.** Prices shown in another currency are kept as
text in `price_text` and left `NULL` in `price_uah` instead of being recorded
as hryvnia amounts.

**Offline re-parsing of saved pages.** When a downloaded page yields no listing
cards, the scraper does not fail silently: it saves the page HTML as
`debug_page_N.html`. After the selectors are adjusted, the same file can be
parsed again with `python main.py debug_page_1.html` — without new requests to
OLX, so repeated debugging runs do not risk a block. This is also why the
`requests` fallback is kept: saved pages can be parsed even where `curl_cffi`
is not installed.

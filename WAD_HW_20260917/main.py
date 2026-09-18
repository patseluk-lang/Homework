"""Entry point: scrape OLX -> store in SQLite.

Usage:
    python main.py                          # download pages from OLX
    python main.py page1.html page2.html    # parse saved pages instead
"""

import sys

from config import DB_NAME
from database import (
    count_products,
    create_table,
    get_connection,
    get_products,
    save_products,
)
from scraper import scrape, scrape_files


def print_products(rows):
    for row in rows:
        product_id, title, price_text, price_uah, location, published, url = row
        print(f"\nID: {product_id}")
        print(f"Title: {title}")
        print(f"Price: {price_text} (UAH: {price_uah})")
        print(f"Location: {location}")
        print(f"Published: {published}")
        print(f"URL: {url}")


def main():
    local_files = sys.argv[1:]

    print("=== OLX: Apple mobile phones ===\n")

    products = scrape_files(local_files) if local_files else scrape()

    if not products:
        print("\nNo listings found. Check debug_page_*.html.")
        return

    connection = get_connection()
    try:
        create_table(connection)
        saved = save_products(connection, products)

        print(f"\nListings collected: {len(products)}")
        print(f"New rows inserted: {saved}")
        print(f"Total rows in {DB_NAME}: {count_products(connection)}")

        print("\n=== First 10 rows from the database ===")
        print_products(get_products(connection))
    finally:
        connection.close()


if __name__ == "__main__":
    main()

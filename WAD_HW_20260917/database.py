"""SQLite storage."""

import sqlite3

from config import DB_NAME

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS phones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price_text TEXT,
    price_uah INTEGER,
    location TEXT,
    published TEXT,
    url TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

INSERT_PRODUCT = """
INSERT OR IGNORE INTO phones
    (title, price_text, price_uah, location, published, url)
VALUES
    (:title, :price_text, :price_uah, :location, :published, :url)
"""


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table(connection):
    connection.execute(CREATE_TABLE)
    connection.commit()


def save_products(connection, products):
    """Insert the listings and return how many rows were actually added.

    INSERT OR IGNORE together with UNIQUE on url prevents duplicates
    both within one run and on repeated runs.
    """
    saved = 0
    for product in products:
        cursor = connection.execute(INSERT_PRODUCT, product)
        saved += cursor.rowcount
    connection.commit()
    return saved


def count_products(connection):
    return connection.execute("SELECT COUNT(*) FROM phones").fetchone()[0]


def get_products(connection, limit=10):
    return connection.execute(
        """
        SELECT id, title, price_text, price_uah, location, published, url
        FROM phones
        ORDER BY id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

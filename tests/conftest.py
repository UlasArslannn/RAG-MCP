"""
Shared test fixtures for RAG-MCP tests
"""
import sqlite3
import os
import sys
import pytest

# Add project root to path so we can import scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


# ─── Sample Data ───
SAMPLE_REVIEWS = [
    ("alice", 5, "Margherita pizza was absolutely perfect!"),
    ("bob", 2, "Pepperoni pizza was way too greasy."),
    ("karen", 1, "Worst pizza ever, crust was burnt."),
    ("leo", 4, "Really good pepperoni slice but needed more cheese."),
    ("maya", 5, "Absolutely loved the vegan option!"),
]


@pytest.fixture
def temp_db(tmp_path):
    """
    Creates a temporary SQLite database with the reviews table.
    Returns the path to the database file.
    """
    db_path = str(tmp_path / "test_reviews.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            text TEXT
        )
    ''')
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def populated_db(temp_db):
    """
    Creates a temporary database pre-populated with sample reviews.
    Returns the path to the database file.
    """
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    for username, rating, text in SAMPLE_REVIEWS:
        cursor.execute(
            'INSERT INTO reviews (username, rating, text) VALUES (?, ?, ?)',
            (username, rating, text)
        )
    conn.commit()
    conn.close()
    return temp_db

"""
database.py
Handles all SQLite connections and initialization for the Library Book Manager.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "library.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    """Return a new SQLite connection with row access by column name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(force=False):
    """
    Create the database and load sample data if it doesn't exist yet.
    Set force=True to wipe and recreate from scratch.
    """
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    if not os.path.exists(DB_PATH):
        conn = get_connection()
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()
        print("Database initialized with sample data at", DB_PATH)
    else:
        print("Database already exists at", DB_PATH)


if __name__ == "__main__":
    # Run `python database.py` to (re)initialize the database.
    init_db(force=True)

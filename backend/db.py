import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).with_name("US_recipes.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS US_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cuisine TEXT,
                title TEXT,
                rating REAL,
                prep_time INTEGER,
                cook_time INTEGER,
                total_time INTEGER,
                description TEXT,
                nutrients TEXT,   -- JSON string
                serves TEXT
            );
        """)
        
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_rating ON US_recipes(rating);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_title ON US_recipes(title);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON US_recipes(cuisine);")

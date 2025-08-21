import json
from pathlib import Path
from db import get_conn, init_db

THIS_DIR = Path(__file__).parent
JSON_PATH = THIS_DIR / "US_recipes.json"

def to_null_if_nan(val):
    """
    Convert numeric-like fields. Treat 'NaN' or invalid numbers as None.
    Accepts numbers, numeric strings, 'NaN', None.
    """
    if val is None:
        return None
    if isinstance(val, str):
        if val.strip().lower() == "nan" or not val.strip():
            return None
        try:
            if "." in val:
                return float(val)
            return int(val)
        except:
            return None
    if isinstance(val, (int, float)):
        if isinstance(val, float) and (val != val):  # NaN check
            return None
        return val
    return None

def load_and_seed():
    init_db()
    with get_conn() as conn, conn:
        cur = conn.cursor()
        # Clear previous data
        cur.execute("DELETE FROM US_recipes;")

        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

        # Handle numeric-keyed dicts and other formats
        if isinstance(data, dict):
            if all(k.isdigit() for k in data.keys()):
                items = list(data.values())
            else:
                items = data.get("US_recipes") or data.get("items") or []
        else:
            items = data

        if not items:
            print("No recipe items found in JSON!")
            return

        for rec in items:
            cuisine = rec.get("cuisine")
            title = rec.get("title")
            rating = to_null_if_nan(rec.get("rating"))
            prep_time = to_null_if_nan(rec.get("prep_time"))
            cook_time = to_null_if_nan(rec.get("cook_time"))
            total_time = to_null_if_nan(rec.get("total_time"))
            description = rec.get("description")
            nutrients = rec.get("nutrients") or {}
            nutrients_json = json.dumps(nutrients, ensure_ascii=False)
            serves = rec.get("serves")

            cur.execute("""
                INSERT INTO US_recipes
                (cuisine, title, rating, prep_time, cook_time, total_time, description, nutrients, serves)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cuisine, title, rating, prep_time, cook_time, total_time, description, nutrients_json, serves))

    print("Database seeded with", len(items), "US_recipes.")

if __name__ == "__main__":
    load_and_seed()

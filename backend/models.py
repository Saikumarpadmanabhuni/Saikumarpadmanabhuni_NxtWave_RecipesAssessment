import json
import re
from typing import Dict, Any, List, Tuple
from db import get_conn

# Parse operators like '>=4.5', '<=400', '==120', '<30', '>3'
OP_RE = re.compile(r"^(<=|>=|==|<|>){0,1}\s*([\d.]+)$")

def parse_op_val(expr: str) -> Tuple[str, float] | None:
    if not expr:
        return None
    expr = expr.strip()
    m = OP_RE.match(expr)
    if not m:
        # if only number provided, treat as == number
        try:
            val = float(expr)
            return "==", val
        except:
            return None
    op, num = m.groups()
    op = op or "=="
    return op, float(num)

def paginate_sorted_by_rating(page: int, limit: int) -> Dict[str, Any]:
    page = max(page, 1)
    limit = max(limit, 1)
    offset = (page - 1) * limit

    with get_conn() as conn:
        cur = conn.cursor()
        # NULLS LAST trick: order first by rating IS NULL (False first), then rating DESC
        cur.execute(f"""
            SELECT COUNT(*) as c FROM US_recipes
        """)
        total = cur.fetchone()["c"]

        cur.execute(f"""
            SELECT id, cuisine, title, rating, prep_time, cook_time, total_time, description, nutrients, serves
            FROM US_recipes
            ORDER BY rating IS NULL ASC, rating DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cur.fetchall()

    data = []
    for r in rows:
        data.append({
            "id": r["id"],
            "cuisine": r["cuisine"],
            "title": r["title"],
            "rating": r["rating"],
            "prep_time": r["prep_time"],
            "cook_time": r["cook_time"],
            "total_time": r["total_time"],
            "description": r["description"],
            "nutrients": json.loads(r["nutrients"] or "{}"),
            "serves": r["serves"]
        })
    return {"page": page, "limit": limit, "total": total, "data": data}

def search(filters: Dict[str, str]) -> List[Dict[str, Any]]:
    title = (filters.get("title") or "").strip()
    cuisine = (filters.get("cuisine") or "").strip()
    total_time_expr = (filters.get("total_time") or "").strip()
    rating_expr = (filters.get("rating") or "").strip()
    calories_expr = (filters.get("calories") or "").strip()

    where = []
    params = []

    if title:
        where.append("LOWER(title) LIKE ?")
        params.append(f"%{title.lower()}%")

    if cuisine:
        # exact match; change to LIKE for partials if desired
        where.append("LOWER(cuisine) = ?")
        params.append(cuisine.lower())

    if total_time_expr:
        parsed = parse_op_val(total_time_expr)
        if parsed:
            op, val = parsed
            where.append(f"total_time {op} ?")
            params.append(val)

    if rating_expr:
        parsed = parse_op_val(rating_expr)
        if parsed:
            op, val = parsed
            where.append(f"rating {op} ?")
            params.append(val)

    # calories are inside nutrients JSON string like "389 kcal"
    # We'll extract the first number on the app side and compare.
    cal_filter_sql = ""
    cal_val = None
    if calories_expr:
        parsed = parse_op_val(calories_expr)
        if parsed:
            op, val = parsed
            # Extract numeric calories using SQLite regexp-like approach:
            # Simpler: pull all rows and filter in Python; but that’s inefficient.
            # Instead, use SUBSTR trick to strip non-digits. We'll do app-side filter to keep it robust.
            cal_filter_sql = f"__CAL_FILTER__{op}{val}"
            cal_val = (op, val)

    base_sql = """
        SELECT id, cuisine, title, rating, prep_time, cook_time, total_time, description, nutrients, serves
        FROM US_recipes
    """
    if where:
        base_sql += " WHERE " + " AND ".join(where)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(base_sql, params)
        rows = cur.fetchall()

    # Apply calories filter in Python (robust for any nutrients format)
    def extract_calories(nut_json: str) -> float | None:
        try:
            d = json.loads(nut_json or "{}")
            raw = (d.get("calories") or "").strip()
            # pull first number in the string
            m = re.search(r"([\d.]+)", raw)
            return float(m.group(1)) if m else None
        except:
            return None

    data = []
    for r in rows:
        item = {
            "id": r["id"],
            "cuisine": r["cuisine"],
            "title": r["title"],
            "rating": r["rating"],
            "prep_time": r["prep_time"],
            "cook_time": r["cook_time"],
            "total_time": r["total_time"],
            "description": r["description"],
            "nutrients": {},
            "serves": r["serves"]
        }
        nut_json = r["nutrients"]
        nut = {}
        try:
            nut = json.loads(nut_json or "{}")
        except:
            nut = {}
        item["nutrients"] = nut

        if cal_val:
            cals = extract_calories(nut_json)
            if cals is None:
                continue
            op, v = cal_val
            ok = (
                (op == "==" and cals == v) or
                (op == ">=" and cals >= v) or
                (op == "<=" and cals <= v) or
                (op == ">" and cals > v) or
                (op == "<" and cals < v)
            )
            if not ok:
                continue

        data.append(item)

    return data

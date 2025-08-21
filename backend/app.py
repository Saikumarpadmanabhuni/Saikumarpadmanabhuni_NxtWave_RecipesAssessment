from flask import Flask, request, jsonify
from flask_cors import CORS
from db import init_db
from models import paginate_sorted_by_rating, search

app = Flask(__name__)
CORS(app)

init_db()

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/US_recipes")
def get_US_recipes():
    # Defaults per spec
    try:
        page = int(request.args.get("page", "1"))
    except:
        page = 1
    try:
        limit = int(request.args.get("limit", "10"))
    except:
        limit = 10

    payload = paginate_sorted_by_rating(page=page, limit=limit)
    return jsonify(payload)

@app.get("/api/US_recipes/search")
def search_US_recipes():
    filters = {
        "calories": request.args.get("calories"),
        "title": request.args.get("title"),
        "cuisine": request.args.get("cuisine"),
        "total_time": request.args.get("total_time"),
        "rating": request.args.get("rating"),
    }
    data = search(filters)
    return jsonify({"data": data})

if __name__ == "__main__":
    # For local dev
    app.run(host="0.0.0.0", port=5678, debug=True)

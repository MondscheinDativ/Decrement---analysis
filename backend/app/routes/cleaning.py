import hashlib, json
from flask import Blueprint, request, jsonify
from ..extensions import cache

bp = Blueprint("cleaning", __name__)

@bp.post("/clean-data")
def clean_data():
    payload = request.get_json() or {}
    data = payload.get("data", [])
    opts = payload.get("options", {})
    key = "clean:" + hashlib.sha256(json.dumps({"data": data, "opts": opts}, default=str).encode()).hexdigest()
    if cache is not None and (cached := cache.get(key)):
        return jsonify(json.loads(cached))

    # simple cleaner: drop null-only rows
    cleaned = [r for r in data if any(v not in (None, "", "NA") for v in r.values())]
    result = {"rows": len(cleaned), "data": cleaned[:200]}
    if cache is not None:
        cache.setex(key, 3600, json.dumps(result))
    return jsonify(result)

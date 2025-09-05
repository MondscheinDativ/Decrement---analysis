import os, csv, io, json
from uuid import uuid4
from flask import Blueprint, current_app, jsonify, request
import pandas as pd
from ..utils.audit import audit_log

bp = Blueprint("datasets", __name__)

_DATASETS = {}

@bp.get("/datasets")
def list_datasets():
    items = []
    for k, v in _DATASETS.items():
        items.append({"id": k, "name": v.get("name"), "size": f"{len(v['data'])} rows"})
    # also scan folder
    folder = current_app.config["DATASETS_DIR"]
    for fname in os.listdir(folder):
        if fname.lower().endswith((".csv", ".parquet")):
            items.append({"id": f"file::{fname}", "name": fname, "size": "on disk"})
    return jsonify({"datasets": items})

@bp.post("/upload-custom-data")
def upload_custom():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["file"]
    df = pd.read_csv(f) if f.filename.lower().endswith(".csv") else pd.DataFrame()
    dsid = str(uuid4())
    _DATASETS[dsid] = {"name": f.filename, "data": df.to_dict(orient="records")}
    audit_log("CUSTOM_DATA_UPLOAD", {"rows": len(_DATASETS[dsid]["data"])})
    return jsonify({
        "id": dsid,
        "data": _DATASETS[dsid]["data"][:200],
        "tables": [{"value": "main", "label": "Main Table"}],
        "metadata": {"source": "custom"}
    })

@bp.post("/apply-filters")
def apply_filters():
    body = request.get_json() or {}
    table = body.get("table")
    fields = body.get("fields", [])
    start_year = int(body.get("startYear", 0) or 0)
    end_year = int(body.get("endYear", 9999) or 9999)

    # choose first in-memory dataset if table == 'main'
    ds = next(iter(_DATASETS.values()), None)
    rows = ds["data"] if ds else []

    # filter basic year column if present
    def in_range(r):
        y = r.get("year") or r.get("Year") or r.get("YEAR")
        try:
            y = int(y)
        except Exception:
            return True
        return start_year <= y <= end_year

    filtered = [ {k:v for k,v in r.items() if (not fields or k in fields)} for r in rows if in_range(r) ]
    return jsonify({"filteredData": filtered})

@bp.post("/get-table-fields")
def get_table_fields():
    ds = next(iter(_DATASETS.values()), None)
    if not ds:
        return jsonify({"fields": []})
    headers = list((ds["data"][0] or {}).keys()) if ds["data"] else []
    return jsonify({"fields": [{"value": h, "label": h} for h in headers]})

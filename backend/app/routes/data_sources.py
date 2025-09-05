from flask import Blueprint, jsonify, request
from ..utils.sas_runner import run_sas_or_mock
from ..utils.audit import audit_log

bp = Blueprint("sources", __name__)

@bp.post("/fetch-data")
def fetch_data():
    body = request.get_json() or {}
    source = (body.get("source") or "HMD").upper()
    if source == "HMD":
        # In MOCK, just return a tiny frame
        data = [{"year": y, "age": a, "mortality": 0.001 + 0.0001*a} for y in range(2015, 2020) for a in range(30, 35)]
        audit_log("HMD_DATA_FETCH", {"rows": len(data)})
        return jsonify({
            "data": data,
            "tables": [{"value": "mortality", "label": "Mortality Table"}],
            "metadata": {"source": "HMD"}
        })
    elif source == "CDC":
        run_sas_or_mock("/* pretend to query CDC */")
        return jsonify({"data": [], "tables": [], "metadata": {"source": "CDC"}})
    return jsonify({"error": "Unsupported source"}), 400

from flask import Blueprint, jsonify, request
from ..utils.sas_runner import run_sas_or_mock
from ..utils.audit import audit_log
import os, csv

bp = Blueprint("sources", __name__)

@bp.post("/fetch-data")
def fetch_data():
    body = request.get_json() or {}
    source = (body.get("source") or "HMD").upper()

    if source == "HMD":
        # In MOCK, just return a tiny frame
        data = [{"year": y, "age": a, "mortality": 0.001 + 0.0001*a}
                for y in range(2015, 2020) for a in range(30, 35)]
        audit_log("HMD_DATA_FETCH", {"rows": len(data)})
        return jsonify({
            "data": data,
            "tables": [{"value": "mortality", "label": "Mortality Table"}],
            "metadata": {"source": "HMD"}
        })

    elif source == "CDC":
        run_sas_or_mock("/* pretend to query CDC */")
        return jsonify({"data": [], "tables": [], "metadata": {"source": "CDC"}})

    elif source == "SOA_CASE":
        # Example: load a demo dataset shipped in datasets/soa_case.csv
        path = os.path.join(os.getcwd(), "datasets", "soa_case.csv")
        if not os.path.exists(path):
            return jsonify({"error": "SOA case dataset not found"}), 404

        rows = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)

        audit_log("SOA_CASE_FETCH", {"rows": len(rows)})
        return jsonify({
            "data": rows[:500],  # limit preview
            "tables": [{"value": "soa_case", "label": "SOA Case Dataset"}],
            "metadata": {"source": "SOA"}
        })

    return jsonify({"error": "Unsupported source"}), 400

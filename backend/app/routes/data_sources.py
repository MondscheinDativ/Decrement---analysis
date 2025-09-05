from flask import Blueprint, jsonify, request
from ..utils.sas_runner import run_sas_or_mock
from ..utils.audit import audit_log
import os, csv

bp = Blueprint("sources", __name__)

@bp.post("/fetch-data")
def fetch_data():
    body = request.get_json() or {}
    source = (body.get("source") or "HMD").upper()

    # ------------------------------
    # 1. MOCK HMD data (small demo)
    # ------------------------------
    if source == "HMD":
        data = [
            {"year": y, "age": a, "mortality": 0.001 + 0.0001 * a}
            for y in range(2015, 2020)
            for a in range(30, 35)
        ]
        audit_log("HMD_DATA_FETCH", {"rows": len(data)})
        return jsonify({
            "data": data,
            "tables": [{"value": "mortality", "label": "Mortality Table"}],
            "metadata": {"source": "HMD (mock)"}
        })

    # ------------------------------
    # 2. MOCK CDC placeholder
    # ------------------------------
    elif source == "CDC":
        run_sas_or_mock("/* pretend to query CDC */")
        return jsonify({
            "data": [],
            "tables": [],
            "metadata": {"source": "CDC (mock)"}
        })

    # ------------------------------
    # 3. SOA case (demo → CDC raw)
    # ------------------------------
    elif source == "SOA_CASE":
        path = os.path.join(os.getcwd(), "data", "CDC_raw_data.csv")
        if not os.path.exists(path):
            return jsonify({"error": "SOA case dataset not found"}), 404

        rows = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)

        audit_log("SOA_CASE_FETCH", {"rows": len(rows)})
        return jsonify({
            "data": rows[:500],
            "tables": [{"value": "soa_case", "label": "SOA Case (CDC raw)"}],
            "metadata": {"source": "SOA_CASE"}
        })

    # ------------------------------
    # 4. CDC raw data (official)
    # ------------------------------
    elif source == "CDC_RAW":
        path = os.path.join(os.getcwd(), "data", "CDC_raw_data.csv")
        if not os.path.exists(path):
            return jsonify({"error": "CDC raw dataset not found"}), 404

        rows = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)

        audit_log("CDC_RAW_FETCH", {"rows": len(rows)})
        return jsonify({
            "data": rows[:500],
            "tables": [{"value": "cdc_raw", "label": "CDC Raw Dataset"}],
            "metadata": {"source": "CDC_RAW"}
        })

    # ------------------------------
    # 5. HMD raw data (official)
    # ------------------------------
    elif source == "HMD_RAW":
        path = os.path.join(os.getcwd(), "data", "HMD_raw_data.txt")
        if not os.path.exists(path):
            return jsonify({"error": "HMD raw dataset not found"}), 404

        rows = []
        with open(path, "r", encoding="utf-8") as f:
            headers = None
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                # first non-comment line = headers
                if headers is None:
                    headers = parts
                    continue
                rows.append(dict(zip(headers, parts)))

        audit_log("HMD_RAW_FETCH", {"rows": len(rows)})
        return jsonify({
            "data": rows[:500],
            "tables": [{"value": "hmd_raw", "label": "HMD Raw Dataset"}],
            "metadata": {"source": "HMD_RAW"}
        })

    # ------------------------------
    # Unsupported
    # ------------------------------
    return jsonify({"error": f"Unsupported source {source}"}), 400

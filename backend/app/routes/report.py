from flask import Blueprint, request, jsonify

bp = Blueprint("report", __name__)

@bp.post("/generate-report")
def generate_report():
    payload = request.get_json() or {}
    data = payload.get("data", [])
    # very small synthetic diagnostics
    summary = []
    if data:
        keys = list(data[0].keys())
        summary = [{"field": k, "nonNull": sum(1 for r in data if r.get(k) is not None)} for k in keys]
    report = {
        "summaryStats": summary,
        "missingValueReport": [],
        "outlierReport": [],
        "dataDistribution": [],
        "timeSeriesAnalysis": []
    }
    return jsonify({"report": report})

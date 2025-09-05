import numpy as np, io, zipfile, json
import pandas as pd
from flask import Blueprint, request, jsonify, send_file

bp = Blueprint("compare", __name__)

_RESULTS = {}

@bp.post("/compare")
def compare():
    body = request.get_json() or {}
    items = body.get("items", [])
    metrics = body.get("metrics", ["AIC","BIC","Residual"])

    res = {"items": [], "metrics": {m: [] for m in metrics}, "details": [], "visualizations": []}
    for idx, it in enumerate(items or ["Model A","Model B","Model C"]):
        name = it.get("name") if isinstance(it, dict) else str(it)
        res["items"].append({"id": idx, "name": name, "type": "Model"})
        for m in metrics:
            res["metrics"][m].append(float(np.random.uniform(0, 1)))
        res["details"].append({"itemId": idx, "itemName": name, "itemType": "Model", "data": {"note": "mock"}})

    for m in metrics:
        res["visualizations"].append({
            "title": f"{m} Comparison",
            "data": [{"x": [i["name"] for i in res["items"]], "y": res["metrics"][m], "type": "bar", "name": m}],
            "layout": {"title": f"{m} Values Across Items", "xaxis": {"title": "Items"}, "yaxis": {"title": m}}
        })

    rid = f"result_{len(_RESULTS)}"
    _RESULTS[rid] = res
    return jsonify({"resultId": rid, "results": res})

@bp.post("/export-comparison")
def export_comparison():
    rid = (request.get_json() or {}).get("resultId")
    if not rid or rid not in _RESULTS:
        return jsonify({"error": "Invalid result ID"}), 400
    results = _RESULTS[rid]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        summary_df = pd.DataFrame({"Item": [x['name'] for x in results['items']], **{m: v for m, v in results['metrics'].items()}})
        z.writestr("summary.csv", summary_df.to_csv(index=False))
        z.writestr("details.json", json.dumps(results['details'], indent=2))
        for i, viz in enumerate(results['visualizations']):
            html = f"""
            <!DOCTYPE html><html><head>
            <script src='https://cdn.plot.ly/plotly-2.24.1.min.js'></script>
            </head><body><div id='c' style='width:800px;height:600px;'></div>
            <script>Plotly.newPlot('c', {json.dumps(viz['data'])}, {json.dumps(viz['layout'])});</script>
            </body></html>"""
            z.writestr(f"chart_{i+1}.html", html)
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"comparison_{rid}.zip")

@bp.post("/save-comparison")
def save_comparison():
    payload = (request.get_json() or {}).get("results")
    if not payload:
        return jsonify({"error": "No results provided"}), 400
    rid = f"saved_{len(_RESULTS)}"
    _RESULTS[rid] = payload
    return jsonify({"status": "success", "resultId": rid})

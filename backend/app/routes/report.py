from flask import Blueprint, request, jsonify
import numpy as np
import pandas as pd

bp = Blueprint("report", __name__)

@bp.post("/generate-report")
def generate_report():
    payload = request.get_json() or {}
    data = payload.get("data", [])
    if not data:
        return jsonify({"report": {"error": "No data provided"}}), 400

    df = pd.DataFrame(data)

    report = {}

    # ----------------------------
    # Summary statistics
    # ----------------------------
    summary_stats = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            desc = df[col].describe()
            summary_stats.append({
                "field": col,
                "count": int(desc["count"]),
                "mean": float(desc["mean"]) if not np.isnan(desc["mean"]) else None,
                "std": float(desc["std"]) if not np.isnan(desc["std"]) else None,
                "min": float(desc["min"]),
                "max": float(desc["max"])
            })
    report["summaryStats"] = summary_stats

    # ----------------------------
    # Missing value report
    # ----------------------------
    missing_report = []
    for col in df.columns:
        n_missing = df[col].isna().sum()
        if n_missing > 0:
            missing_report.append({
                "field": col,
                "missing": int(n_missing),
                "percent": round(n_missing / len(df) * 100, 2)
            })
    report["missingValueReport"] = missing_report

    # ----------------------------
    # Outlier detection (Z-score)
    # ----------------------------
    outlier_report = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            vals = df[col].dropna().astype(float)
            if len(vals) > 0:
                z_scores = (vals - vals.mean()) / (vals.std() if vals.std() != 0 else 1)
                n_outliers = int((np.abs(z_scores) > 3).sum())
                if n_outliers > 0:
                    outlier_report.append({
                        "field": col,
                        "outliers": n_outliers,
                        "percent": round(n_outliers / len(vals) * 100, 2)
                    })
    report["outlierReport"] = outlier_report

    # ----------------------------
    # Distribution (histogram)
    # ----------------------------
    dist_report = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            counts, bins = np.histogram(df[col].dropna(), bins=10)
            dist_report.append({
                "field": col,
                "bins": bins.tolist(),
                "counts": counts.tolist()
            })
    report["dataDistribution"] = dist_report

    # ----------------------------
    # Time series analysis (by year)
    # ----------------------------
    ts_report = []
    year_col = None
    for candidate in ["year", "Year", "YEAR"]:
        if candidate in df.columns:
            year_col = candidate
            break
    if year_col:
        grouped = df.groupby(year_col).size().reset_index(name="count")
        ts_report = grouped.to_dict(orient="records")
    report["timeSeriesAnalysis"] = ts_report

    return jsonify({"report": report})

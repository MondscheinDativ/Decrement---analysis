from flask import Blueprint, jsonify

bp = Blueprint("models", __name__)

_MODELS = [
    {"id": "lee-carter", "name": "Lee-Carter", "type": "Mortality", "description": "ln(m_x)=a_x+b_x*k_t+e_x"},
    {"id": "cbd", "name": "CBD", "type": "Mortality", "description": "logit(q_x)=k_t^(1)+(x-x̄)k_t^(2)"},
    {"id": "gompertz", "name": "Gompertz", "type": "Mortality", "description": "μ(x)=B*c^x"}
]

@bp.get("/models")
def models():
    return jsonify({"models": _MODELS})

@bp.get("/model/<mid>")
def model_detail(mid):
    m = next((m for m in _MODELS if m["id"] == mid), None)
    if not m:
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "id": m["id"],
        "name": m["name"],
        "formula": m["description"],
        "parameters": [{"name": "alpha", "description": "level"}, {"name": "beta", "description": "trend"}],
        "applicability": "Mortality improvement / forecasting",
        "soaReference": "SOA 2023"
    })

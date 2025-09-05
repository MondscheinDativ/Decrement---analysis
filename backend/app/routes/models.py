from flask import Blueprint, jsonify

bp = Blueprint("models", __name__)

_MODELS = [
    {
        "id": "lee-carter",
        "name": "Lee-Carter",
        "type": "Mortality",
        "description": "ln(m_x)=a_x+b_x*k_t+e_x"
    },
    {
        "id": "cbd",
        "name": "CBD",
        "type": "Mortality",
        "description": "logit(q_x)=k_t^(1)+(x-x̄)k_t^(2)"
    },
    {
        "id": "gompertz",
        "name": "Gompertz",
        "type": "Mortality",
        "description": "μ(x)=B*c^x"
    },
    {
        "id": "apc",
        "name": "Age-Period-Cohort (APC)",
        "type": "Mortality",
        "description": "μ(x,t)=α_x+β_t+γ_{t−x}"
    },
    {
        "id": "soa-calibration",
        "name": "SOA 标准校准器",
        "type": "Calibration",
        "description": "校准预测结果以符合 SOA 教育/监管标准"
    }
]

@bp.get("/models")
def models():
    return jsonify({"models": _MODELS})

@bp.get("/model/<mid>")
def model_detail(mid):
    m = next((m for m in _MODELS if m["id"] == mid), None)
    if not m:
        return jsonify({"error": "not found"}), 404

    details = {
        "id": m["id"],
        "name": m["name"],
        "formula": m["description"],
        "parameters": [],
        "applicability": "",
        "soaReference": "SOA 2023"
    }

    if mid == "lee-carter":
        details["parameters"] = [
            {"name": "a_x", "description": "年龄特定截距"},
            {"name": "b_x", "description": "年龄特定斜率"},
            {"name": "k_t", "description": "时间因子"}
        ]
        details["applicability"] = "死亡率长期趋势预测"
    elif mid == "cbd":
        details["parameters"] = [
            {"name": "k_t^(1)", "description": "截距"},
            {"name": "k_t^(2)", "description": "斜率"}
        ]
        details["applicability"] = "高龄死亡率建模"
    elif mid == "gompertz":
        details["parameters"] = [
            {"name": "B", "description": "尺度参数"},
            {"name": "c", "description": "形状参数"}
        ]
        details["applicability"] = "适用于中老年区间"
    elif mid == "apc":
        details["parameters"] = [
            {"name": "α_x", "description": "年龄效应"},
            {"name": "β_t", "description": "时间效应"},
            {"name": "γ_{t−x}", "description": "队列效应"}
        ]
        details["applicability"] = "死亡率改进与队列分析"
    elif mid == "soa-calibration":
        details["parameters"] = [
            {"name": "scaling", "description": "缩放因子"},
            {"name": "shift", "description": "偏移调整"}
        ]
        details["applicability"] = "结果校准 / 合规性检查"

    return jsonify(details)

import json, os, uuid, hashlib
from datetime import datetime

def track_lineage(input_data, operation, params, output_data):
    rec = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "parameters": params,
        "input_hash": hashlib.sha256(json.dumps(input_data, default=str).encode()).hexdigest(),
        "output_hash": hashlib.sha256(json.dumps(output_data, default=str).encode()).hexdigest(),
    }
    path = os.path.abspath(".logs/lineage")
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, f"{rec['id']}.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    return rec["id"]

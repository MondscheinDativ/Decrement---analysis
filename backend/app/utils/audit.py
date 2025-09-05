import json, os, uuid
from datetime import datetime
from flask import request, session

def audit_log(action: str, details: dict):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "details": details,
        "user": getattr(session, "get", lambda *_: None)("user_id") or "SYSTEM",
        "ip": getattr(request, "remote_addr", None) or "0.0.0.0",
        "session_id": getattr(session, "get", lambda *_: str(uuid.uuid4()))("sid") or str(uuid.uuid4()),
    }
    path = os.environ.get("AUDIT_LOG_PATH", os.path.abspath(".logs/audit.log"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

import json, tempfile, subprocess, time
from flask import current_app
from .audit import audit_log

class DataProcessingError(Exception):
    pass


def run_sas_or_mock(script: str, input_json: dict | None = None) -> dict:
    """Runs SAS code if MOCK_MODE is False, otherwise returns a mock result.
    Keeps interface simple for routes to use in CI/Pages.
    """
    if current_app.config.get("MOCK_MODE", True):
        audit_log("SAS_MOCK_EXEC", {"length": len(script)})
        # Return minimal mock so downstream can proceed
        return {"status": "MOCKED", "rows": 100}

    # Real execution example (omitted heavy details)
    try:
        with tempfile.NamedTemporaryFile(suffix=".sas", delete=False) as sf:
            sf.write(script.encode("utf-8"))
            path = sf.name
        # Example: call a containerized SAS
        subprocess.run(["docker","run","--rm","-v",f"{path}:/script.sas","sas-grid","sas","/script.sas"], check=True, timeout=600)
        # Collect outputs…
        audit_log("SAS_EXEC", {"script": script[:200]})
        return {"status": "OK"}
    except subprocess.CalledProcessError as e:
        raise DataProcessingError(str(e))

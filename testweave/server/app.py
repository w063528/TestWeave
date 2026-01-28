from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from testweave.storage.workspace_store import load_workspace, save_workspace

app = FastAPI(
    title="TestWeave",
    description="Local-first test management server",
    version="0.1.0",
)

# localhost 전용 MVP: 전부 허용(추후 127.0.0.1로 묶을 수도 있음)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# In-memory state (MVP)
# ---------------------------------------------------------------------
_SERVER_ROOT = Path.cwd().resolve()  # 서버를 실행한 위치
_workspace: Path = load_workspace(_SERVER_ROOT)
_last_scan: dict[str, Any] | None = None


def _jsonify(obj: Any) -> Any:
    """
    Make common objects JSON serializable (dataclass, Path, set, etc.)
    """
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, list):
        return [_jsonify(x) for x in obj]
    if isinstance(obj, tuple):
        return [_jsonify(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, set):
        return sorted([_jsonify(x) for x in obj])
    if is_dataclass(obj):
        return _jsonify(asdict(obj))
    # fallback: try best-effort string
    return str(obj)


def _run_scan(workspace: Path, globs: list[str] | None = None) -> dict[str, Any]:
    """
    Call core scanner. We try to be compatible with existing code by
    probing function names.
    """
    from testweave.core import scanner as scanner_mod  # local import

    # 1) Preferred: scan_workspace(workspace, globs=?)
    if hasattr(scanner_mod, "scan_workspace"):
        fn = getattr(scanner_mod, "scan_workspace")
        try:
            res = fn(workspace, globs=globs)  # type: ignore[misc]
        except TypeError:
            # older signature: scan_workspace(workspace)
            res = fn(workspace)  # type: ignore[misc]
        return {"workspace": str(workspace), "result": _jsonify(res)}

    # 2) Alternative: scan(workspace, globs=?)
    if hasattr(scanner_mod, "scan"):
        fn = getattr(scanner_mod, "scan")
        try:
            res = fn(workspace, globs=globs)  # type: ignore[misc]
        except TypeError:
            res = fn(workspace)  # type: ignore[misc]
        return {"workspace": str(workspace), "result": _jsonify(res)}

    raise RuntimeError("No scan function found in testweave.core.scanner")


class WorkspaceSetRequest(BaseModel):
    path: str


class ScanRequest(BaseModel):
    globs: list[str] | None = None


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "product": "testweave",
        "mode": "local",
        "serverRoot": str(_SERVER_ROOT),
    }


@app.get("/api/workspace")
def get_workspace():
    return {
        "workspace": str(_workspace),
        "serverRoot": str(_SERVER_ROOT),
        "storedAt": str((_SERVER_ROOT / ".qa" / "workspace.json").resolve()),
    }


@app.post("/api/workspace")
def set_workspace(req: WorkspaceSetRequest):
    global _workspace
    p = Path(req.path).expanduser().resolve()
    if not p.exists() or not p.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid workspace path: {p}")

    _workspace = p
    save_workspace(_SERVER_ROOT, _workspace)
    return {"workspace": str(_workspace)}


@app.post("/api/scan")
def scan(req: ScanRequest):
    global _last_scan
    try:
        payload = _run_scan(_workspace, globs=req.globs)
        _last_scan = payload
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/testcases")
def get_testcases():
    if _last_scan is None:
        return {
            "workspace": str(_workspace),
            "result": None,
            "message": "No scan result yet. Call POST /api/scan first.",
        }
    return _last_scan


@app.get("/", response_class=HTMLResponse)
def index():
    return f"""
    <!doctype html>
    <html>
      <head>
        <title>TestWeave</title>
        <style>
          body {{ font-family: system-ui, -apple-system, sans-serif; margin: 40px; }}
          h1 {{ margin-bottom: 0.2em; }}
          code {{ background: #f5f5f5; padding: 2px 6px; border-radius: 4px; }}
          .box {{ padding: 12px 14px; border: 1px solid #ddd; border-radius: 10px; margin: 12px 0; }}
          button {{ padding: 8px 12px; }}
          input {{ padding: 8px 10px; width: 520px; max-width: 100%; }}
          pre {{ background: #111; color: #eee; padding: 12px; border-radius: 10px; overflow: auto; }}
        </style>
      </head>
      <body>
        <h1>TestWeave</h1>
        <p>Local-first Test Management Tool</p>

        <div class="box">
          <div><strong>Server Root</strong>: <code>{_SERVER_ROOT}</code></div>
          <div style="margin-top:6px;"><strong>Workspace</strong>: <code id="ws">{_workspace}</code></div>
        </div>

        <div class="box">
          <h3>Workspace</h3>
          <input id="wsInput" placeholder="Enter workspace path" />
          <button onclick="setWs()">Set</button>
          <button onclick="refreshWs()">Refresh</button>
        </div>

        <div class="box">
          <h3>Scan</h3>
          <button onclick="runScan()">POST /api/scan</button>
          <button onclick="getCases()">GET /api/testcases</button>
          <pre id="out">(output)</pre>
        </div>

        <script>
          async function refreshWs() {{
            const r = await fetch('/api/workspace');
            const j = await r.json();
            document.getElementById('ws').innerText = j.workspace;
            document.getElementById('out').innerText = JSON.stringify(j, null, 2);
          }}

          async function setWs() {{
            const path = document.getElementById('wsInput').value;
            const r = await fetch('/api/workspace', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ path }})
            }});
            const j = await r.json();
            document.getElementById('out').innerText = JSON.stringify(j, null, 2);
            await refreshWs();
          }}

          async function runScan() {{
            const r = await fetch('/api/scan', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{}})
            }});
            const j = await r.json();
            document.getElementById('out').innerText = JSON.stringify(j, null, 2);
          }}

          async function getCases() {{
            const r = await fetch('/api/testcases');
            const j = await r.json();
            document.getElementById('out').innerText = JSON.stringify(j, null, 2);
          }}
        </script>
      </body>
    </html>
    """
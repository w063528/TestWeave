from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from testweave.storage.workspace import load_workspace, save_workspace
from testweave.storage.cycles import (
    CycleMember,
    cycles_file_path,
    ensure_cycle,
    list_cycles,
    get_cycle,
    add_members,
    remove_members,
)

app = FastAPI(
    title="TestWeave",
    description="Local-first test management server",
    version="0.1.0",
)

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
    return str(obj)


def _run_scan(workspace: Path, globs: list[str] | None = None) -> dict[str, Any]:
    from testweave.core import scanner as scanner_mod  # local import

    if hasattr(scanner_mod, "scan_workspace"):
        fn = getattr(scanner_mod, "scan_workspace")
        try:
            res = fn(workspace, globs=globs)  # type: ignore[misc]
        except TypeError:
            res = fn(workspace)  # type: ignore[misc]
        return {"workspace": str(workspace), "result": _jsonify(res)}

    if hasattr(scanner_mod, "scan"):
        fn = getattr(scanner_mod, "scan")
        try:
            res = fn(workspace, globs=globs)  # type: ignore[misc]
        except TypeError:
            res = fn(workspace)  # type: ignore[misc]
        return {"workspace": str(workspace), "result": _jsonify(res)}

    raise RuntimeError("No scan function found in testweave.core.scanner")


# ---------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------
class WorkspaceSetRequest(BaseModel):
    path: str


class ScanRequest(BaseModel):
    globs: list[str] | None = None


class CycleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    # cycle이 0개일 때 "생성하면서 추가"를 지원
    members: list["MemberIn"] | None = None


class MemberIn(BaseModel):
    tc_id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(default="")
    uri: str = Field(..., min_length=1)
    line1: int | None = None
    feature: str | None = None


class AddMembersRequest(BaseModel):
    # 1개 이상 cycle에 동시에 추가
    cycleNames: list[str] = Field(..., min_length=1)
    members: list[MemberIn] = Field(..., min_length=1)


class RemoveMembersRequest(BaseModel):
    cycleName: str
    memberKeys: list[str] = Field(..., min_length=1)


# ---------------------------------------------------------------------
# Health / Workspace / Scan
# ---------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "product": "testweave",
        "mode": "local",
        "serverRoot": str(_SERVER_ROOT),
        "workspace": str(_workspace),
        "cyclesFile": str(cycles_file_path(_SERVER_ROOT)),
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


# ---------------------------------------------------------------------
# Cycle API (Step 4)
# ---------------------------------------------------------------------
@app.get("/api/cycles")
def api_list_cycles():
    """
    Cycle 목록: UI에서 multi-select로 cycle 선택할 수 있게 name + count 제공
    """
    try:
        return {
            "cycles": list_cycles(_SERVER_ROOT),
            "storedAt": str(cycles_file_path(_SERVER_ROOT)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cycles")
def api_create_cycle(req: CycleCreateRequest):
    """
    시나리오 3: cycle이 0개일 때, 생성하면서 선택 TC를 함께 추가 가능
    """
    try:
        c = ensure_cycle(_SERVER_ROOT, req.name)

        added_info = None
        if req.members:
            members = [
                CycleMember(
                    tc_id=m.tc_id,
                    title=m.title or m.tc_id,
                    uri=m.uri,
                    line1=m.line1,
                    feature=m.feature,
                )
                for m in req.members
            ]
            added_info = add_members(_SERVER_ROOT, [c.name], members)

        # fresh cycle detail
        c2 = get_cycle(_SERVER_ROOT, c.name)
        return {
            "cycle": _jsonify(c2),
            "membersCount": len(c2.members) if c2 else 0,
            "added": added_info,
            "storedAt": str(cycles_file_path(_SERVER_ROOT)),
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cycles/{cycle_name}")
def api_get_cycle(cycle_name: str):
    try:
        c = get_cycle(_SERVER_ROOT, cycle_name)
        if c is None:
            raise HTTPException(status_code=404, detail=f"Cycle not found: {cycle_name}")
        return {"cycle": _jsonify(c), "storedAt": str(cycles_file_path(_SERVER_ROOT))}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cycles/members:add")
def api_add_members(req: AddMembersRequest):
    """
    시나리오 1,2,2-2:
    - 선택한 TC를 1개 이상 cycle에 동시에 추가
    - UI는 응답 받은 뒤 선택 상태만 clear, scan 결과는 그대로 유지
    """
    try:
        members = [
            CycleMember(
                tc_id=m.tc_id,
                title=m.title or m.tc_id,
                uri=m.uri,
                line1=m.line1,
                feature=m.feature,
            )
            for m in req.members
        ]
        res = add_members(_SERVER_ROOT, req.cycleNames, members)
        return {
            "result": res,
            "cycles": list_cycles(_SERVER_ROOT),
            "storedAt": str(cycles_file_path(_SERVER_ROOT)),
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cycles/members:remove")
def api_remove_members(req: RemoveMembersRequest):
    try:
        res = remove_members(_SERVER_ROOT, req.cycleName, req.memberKeys)
        return {
            "result": res,
            "cycle": _jsonify(get_cycle(_SERVER_ROOT, req.cycleName)),
            "storedAt": str(cycles_file_path(_SERVER_ROOT)),
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------
# Minimal UI shell (for now)
# ---------------------------------------------------------------------
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
          button {{ padding: 8px 12px; margin-right: 6px; }}
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
          <div style="margin-top:6px;"><strong>Cycles File</strong>: <code>{cycles_file_path(_SERVER_ROOT)}</code></div>
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
        </div>

        <div class="box">
          <h3>Cycles</h3>
          <button onclick="listCycles()">GET /api/cycles</button>
          <div style="margin-top:8px;">
            <input id="cycleName" placeholder="New cycle name" />
            <button onclick="createCycle()">POST /api/cycles</button>
          </div>
          <p style="color:#666; margin-top:8px;">
            (UI/UX는 Step 4 후반에 checkbox+multi-select로 구성합니다. 지금은 API 확인용.)
          </p>
        </div>

        <pre id="out">(output)</pre>

        <script>
          async function show(res) {{
            document.getElementById('out').innerText = JSON.stringify(res, null, 2);
          }}

          async function refreshWs() {{
            const r = await fetch('/api/workspace');
            await show(await r.json());
            const j = await (await fetch('/api/workspace')).json();
            document.getElementById('ws').innerText = j.workspace;
          }}

          async function setWs() {{
            const path = document.getElementById('wsInput').value;
            const r = await fetch('/api/workspace', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ path }})
            }});
            await show(await r.json());
            await refreshWs();
          }}

          async function runScan() {{
            const r = await fetch('/api/scan', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{}})
            }});
            await show(await r.json());
          }}

          async function getCases() {{
            const r = await fetch('/api/testcases');
            await show(await r.json());
          }}

          async function listCycles() {{
            const r = await fetch('/api/cycles');
            await show(await r.json());
          }}

          async function createCycle() {{
            const name = document.getElementById('cycleName').value;
            const r = await fetch('/api/cycles', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ name }})
            }});
            await show(await r.json());
          }}
        </script>
      </body>
    </html>
    """
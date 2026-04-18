"""Mobile Companion API for NexusAgent.

REST API + simple web UI for mobile access, with JWT auth and WebSocket updates.
"""

from __future__ import annotations

import json
import os
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MobileConfig:
    host: str = "0.0.0.0"
    port: int = 8430
    jwt_secret: str = "nexus-mobile-secret-change-me"
    jwt_expiry_hours: int = 24
    enable_websocket: bool = True


@dataclass
class TaskStatus:
    id: str
    prompt: str
    status: str = "pending"  # pending, running, completed, failed
    result: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0


def _hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _generate_jwt(payload: dict, secret: str) -> str:
    """Simple JWT-like token generation."""
    try:
        import jwt
        return jwt.encode(payload, secret, algorithm="HS256")
    except ImportError:
        # Fallback: base64-encoded JSON payload
        import base64
        header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
        body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        sig = base64.urlsafe_b64encode(hashlib.sha256(f"{header}.{body}.{secret}".encode()).hexdigest().encode()).decode().rstrip("=")
        return f"{header}.{body}.{sig}"


def _verify_jwt(token: str, secret: str) -> Optional[dict]:
    try:
        import jwt
        return jwt.decode(token, secret, algorithms=["HS256"])
    except ImportError:
        parts = token.split(".")
        if len(parts) == 3:
            import base64
            body = parts[1] + "=" * (4 - len(parts[1]) % 4)
            try:
                return json.loads(base64.urlsafe_b64decode(body))
            except Exception:
                return None
        return None
    except Exception:
        return None


MOBILE_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NexusAgent Mobile</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;max-width:480px;margin:0 auto;padding:16px}
h1{font-size:1.5rem;margin-bottom:8px}.status{color:#22d3ee;font-size:.85rem;margin-bottom:16px}
input,textarea{width:100%;padding:10px;border-radius:8px;border:1px solid #334155;background:#1e293b;color:#e2e8f0;margin-bottom:8px;font-size:.95rem}
button{background:#06b6d4;color:#fff;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;font-size:1rem;width:100%}
button:hover{background:#0891b2}.card{background:#1e293b;border-radius:12px;padding:16px;margin-bottom:12px}
.tasks{margin-top:16px}.task{padding:8px;border-bottom:1px solid #334155;font-size:.85rem}
.task:last-child{border:none}.badge{display:inline-block;padding:2px 8px;border-radius:9999px;font-size:.75rem;margin-left:8px}
.badge-ok{background:#065f46;color:#6ee7b7}.badge-run{background:#1e3a5f;color:#7dd3fc}.badge-fail{background:#7f1d1d;color:#fca5a5}
</style></head><body>
<h1>⚡ NexusAgent</h1><div class="status" id="status">Connecting...</div>
<div class="card"><textarea id="prompt" rows="3" placeholder="Ask Nexus anything..."></textarea>
<button onclick="submit()">Submit Task</button></div>
<div class="card tasks"><h3 style="margin-bottom:8px">Tasks</h3><div id="tasks"></div></div>
<script>
const API = location.origin;
async function submit(){const p=document.getElementById('prompt');if(!p.value.trim())return;
const r=await fetch(API+'/api/tasks',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+localStorage.token},body:JSON.stringify({prompt:p.value})});
const d=await r.json();p.value='';loadTasks();}
async function loadTasks(){const r=await fetch(API+'/api/tasks',{headers:{'Authorization':'Bearer '+localStorage.token}});
const tasks=await r.json();const el=document.getElementById('tasks');
el.innerHTML=tasks.map(t=>`<div class="task">${t.prompt.substring(0,50)}<span class="badge badge-${t.status==='completed'?'ok':t.status==='failed'?'fail':'run'}">${t.status}</span></div>`).join('');}
fetch(API+'/api/status').then(r=>r.json()).then(d=>{document.getElementById('status').textContent=`Online · ${d.model||'mock'} · ${d.tasks} tasks`});
loadTasks();
</script></body></html>"""


class MobileAPI:
    """Mobile companion REST API."""

    def __init__(self, config: Optional[MobileConfig] = None):
        self.config = config or MobileConfig()
        self._tasks: dict[str, TaskStatus] = {}
        self._users: dict[str, dict] = {}  # username -> {password_hash}
        self._api = None  # FastAPI app, built lazily

    def add_user(self, username: str, password: str):
        self._users[username] = {"password_hash": _hash_password(password)}

    def authenticate(self, username: str, password: str) -> Optional[str]:
        user = self._users.get(username)
        if user and user["password_hash"] == _hash_password(password):
            payload = {"sub": username, "exp": time.time() + self.config.jwt_expiry_hours * 3600}
            return _generate_jwt(payload, self.config.jwt_secret)
        return None

    def verify_token(self, token: str) -> Optional[str]:
        data = _verify_jwt(token, self.config.jwt_secret)
        if data and data.get("exp", 0) > time.time():
            return data.get("sub")
        return None

    def submit_task(self, prompt: str) -> TaskStatus:
        import uuid
        task = TaskStatus(id=uuid.uuid4().hex[:8], prompt=prompt, status="pending", created_at=time.time())
        self._tasks[task.id] = task
        return task

    def get_tasks(self) -> list[dict]:
        return [{"id": t.id, "prompt": t.prompt, "status": t.status, "result": t.result, "created_at": t.created_at} for t in self._tasks.values()]

    def get_status(self) -> dict:
        try:
            from .agent import NexusAgent
            agent = NexusAgent()
            mem = agent.memory.get_stats()
            return {"status": "online", "model": agent.model, "nodes": mem["nodes"], "edges": mem["edges"], "tasks": len(self._tasks)}
        except Exception:
            return {"status": "online", "model": "unknown", "nodes": 0, "edges": 0, "tasks": len(self._tasks)}

    def build_app(self):
        """Build the FastAPI application."""
        try:
            from fastapi import FastAPI, HTTPException, Depends
            from fastapi.responses import HTMLResponse
            from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        except ImportError:
            raise ImportError("Install fastapi and uvicorn: pip install fastapi uvicorn")

        app = FastAPI(title="NexusAgent Mobile API", version="1.0.0")
        security = HTTPBearer()
        api = self

        def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
            user = api.verify_token(credentials.credentials)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid token")
            return user

        @app.get("/", response_class=HTMLResponse)
        async def web_ui():
            return MOBILE_HTML

        @app.post("/api/auth/login")
        async def login(username: str, password: str):
            token = api.authenticate(username, password)
            if not token:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            return {"token": token}

        @app.get("/api/status")
        async def status():
            return api.get_status()

        @app.get("/api/tasks")
        async def list_tasks(user: str = Depends(get_current_user)):
            return api.get_tasks()

        @app.post("/api/tasks")
        async def create_task(body: dict, user: str = Depends(get_current_user)):
            task = api.submit_task(body.get("prompt", ""))
            return {"id": task.id, "status": task.status}

        @app.get("/api/skills")
        async def list_skills(user: str = Depends(get_current_user)):
            try:
                from .agent import NexusAgent
                agent = NexusAgent()
                return {"skills": agent.skill_tree.list_skills()}
            except Exception:
                return {"skills": ""}

        @app.get("/api/memory/stats")
        async def memory_stats(user: str = Depends(get_current_user)):
            try:
                from .agent import NexusAgent
                agent = NexusAgent()
                return agent.memory.get_stats()
            except Exception:
                return {"nodes": 0, "edges": 0}

        self._api = app
        return app

    def serve(self):
        """Start the mobile API server."""
        app = self.build_app()
        try:
            import uvicorn
            uvicorn.run(app, host=self.config.host, port=self.config.port)
        except ImportError:
            raise ImportError("Install uvicorn: pip install uvicorn")

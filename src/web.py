"""
NexusAgent Web Dashboard
Optional Flask/FastAPI-based UI for monitoring skills, memory graph stats, and task history.
"""

import json
from pathlib import Path
from typing import Optional

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import HTMLResponse
    import uvicorn
    HAS_WEB = True
except ImportError:
    HAS_WEB = False

from .config import get_config
from .agent import NexusAgent
from .plugins import PluginManager


def create_app() -> "Optional[FastAPI]":
    if not HAS_WEB:
        return None

    app = FastAPI(title="NexusAgent Dashboard", version="0.2.0")
    config = get_config()

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        return DASHBOARD_HTML

    @app.get("/api/status")
    async def status():
        agent = NexusAgent()
        mem = agent.memory.get_stats()
        skills = agent.skill_tree.get_stats()
        return {"memory": mem, "skills": skills, "model": config.model.default}

    @app.get("/api/skills")
    async def skills_list():
        agent = NexusAgent()
        return {"skills": agent.skill_tree.list_skills()}

    @app.get("/api/memory/graph")
    async def memory_graph():
        agent = NexusAgent()
        mem = agent.memory
        nodes = [{"id": n, "data": mem.graph.nodes[n]} for n in mem.graph.nodes()]
        edges = [{"source": u, "target": v} for u, v in mem.graph.edges()]
        return {"nodes": nodes, "edges": edges}

    @app.get("/api/plugins")
    async def plugins_list():
        pm = PluginManager()
        pm.load_all()
        return {"plugins": pm.list_plugins()}

    @app.get("/api/config")
    async def get_config_api():
        return config.model_dump()

    return app


def run_web(host: Optional[str] = None, port: Optional[int] = None):
    """Start the web dashboard."""
    if not HAS_WEB:
        print("Install fastapi and uvicorn: pip install fastapi uvicorn")
        return

    config = get_config()
    app = create_app()
    if app:
        uvicorn.run(app, host=host or config.web.host, port=port or config.web.port)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexusAgent Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-950 text-white min-h-screen">
    <nav class="border-b border-gray-800 px-6 py-4 flex items-center gap-3">
        <span class="text-2xl font-bold text-cyan-400">⚡ NexusAgent</span>
        <span class="text-sm text-gray-500">Dashboard</span>
    </nav>
    <main class="max-w-6xl mx-auto p-6 grid gap-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4" id="stats"></div>
        <div class="bg-gray-900 rounded-xl p-6">
            <h2 class="text-lg font-semibold mb-4">Memory Graph</h2>
            <div id="graph-info" class="text-gray-400">Loading...</div>
        </div>
        <div class="bg-gray-900 rounded-xl p-6">
            <h2 class="text-lg font-semibold mb-4">Skills</h2>
            <div id="skills-info" class="text-gray-400">Loading...</div>
        </div>
    </main>
    <script>
        fetch('/api/status').then(r=>r.json()).then(d=>{
            document.getElementById('stats').innerHTML = `
                <div class="bg-gray-900 rounded-xl p-5"><p class="text-gray-500 text-sm">Model</p><p class="text-xl font-bold text-cyan-400">${d.model}</p></div>
                <div class="bg-gray-900 rounded-xl p-5"><p class="text-gray-500 text-sm">Graph Nodes</p><p class="text-xl font-bold text-green-400">${d.memory.nodes}</p></div>
                <div class="bg-gray-900 rounded-xl p-5"><p class="text-gray-500 text-sm">Skills</p><p class="text-xl font-bold text-purple-400">${d.skills.total_skills}</p></div>`;
        });
        fetch('/api/skills').then(r=>r.json()).then(d=>{
            document.getElementById('skills-info').innerHTML = d.skills ? `<pre class="text-sm whitespace-pre-wrap">${d.skills}</pre>` : 'No skills yet.';
        });
    </script>
</body>
</html>"""

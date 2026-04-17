"""
NexusAgent Export
Export skills, graph data, and reports in JSON, Markdown, and shareable skill packs.
"""

import json
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from .agent import NexusAgent


def export_skills_json(agent: NexusAgent, output: Optional[str] = None) -> str:
    """Export skills as JSON."""
    data = []
    for name, skill in agent.skill_tree.skills.items():
        data.append({"name": name, **skill})
    result = json.dumps(data, indent=2, default=str)
    if output:
        Path(output).write_text(result, encoding="utf-8")
    return result


def export_memory_graph(agent: NexusAgent, output: Optional[str] = None) -> str:
    """Export memory graph as JSON."""
    graph = agent.memory.graph
    data = {
        "nodes": [{"id": n, **dict(graph.nodes[n])} for n in graph.nodes()],
        "edges": [{"source": u, "target": v} for u, v in graph.edges()],
    }
    result = json.dumps(data, indent=2, default=str)
    if output:
        Path(output).write_text(result, encoding="utf-8")
    return result


def export_markdown_report(agent: NexusAgent, output: Optional[str] = None) -> str:
    """Export a full Markdown report of NexusAgent state."""
    mem = agent.memory.get_stats()
    skill_list = agent.skill_tree.list_skills() or "No skills yet."
    graph_data = agent.memory.graph

    report = f"""# NexusAgent Report

**Generated:** {datetime.now().isoformat()}
**Model:** {agent.model}

## Memory Graph
- **Nodes:** {mem['nodes']}
- **Edges:** {mem['edges']}

## Top Nodes
"""
    for node in list(graph_data.nodes())[:10]:
        report += f"- `{node}`\n"

    report += f"\n## Skills\n\n{skill_list}\n"

    if output:
        Path(output).write_text(report, encoding="utf-8")
    return report


def export_skill_pack(agent: NexusAgent, output: str = "nexus-skillpack.zip"):
    """Export all skills as a shareable ZIP pack."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest = {"version": "1.0", "exported": datetime.now().isoformat(), "skills": []}
        for name, skill in agent.skill_tree.skills.items():
            code = skill.get("code_snippet", "")
            zf.writestr(f"skills/{name}.py", code)
            manifest["skills"].append({"name": name, "description": skill.get("description", "")})
        zf.writestr("manifest.json", json.dumps(manifest, indent=2))
        zf.writestr("README.md", f"# NexusAgent Skill Pack\n\nExported {datetime.now().isoformat()}\n")

    Path(output).write_bytes(buf.getvalue())
    return output

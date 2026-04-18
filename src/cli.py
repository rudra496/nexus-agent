import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from .agent import NexusAgent
from .config import load_config, save_config, get_config, NexusConfig
from .plugins import PluginManager
from .export import export_skills_json, export_memory_graph, export_markdown_report, export_skill_pack
from .updater import check_version, update_skills, self_update

app = typer.Typer(help="NexusAgent: The Zero-Config, Self-Evolving Local AI Agent.", no_args_is_help=True)
console = Console()


@app.command()
def run(
    prompt: str = typer.Argument(..., help="The task you want Nexus to perform."),
    model: str = typer.Option(None, "--model", "-m", help="The local model to use via LiteLLM."),
):
    """Run the Nexus Agent with a given task."""
    config = get_config()
    model = model or config.model.default
    console.print(Panel.fit(f"[bold blue]NexusAgent[/bold blue] initialized.\nModel: [green]{model}[/green]", title="Nexus"))
    agent = NexusAgent(model=model)
    with console.status("[bold cyan]Nexus is thinking and consulting GraphRAG memory...[/bold cyan]", spinner="dots"):
        response = agent.execute(prompt)
    console.print("\n[bold green]Agent Response:[/bold green]")
    console.print(Markdown(response))


@app.command()
def evolve():
    """Trigger the self-evolution protocol. Scans the workspace to build GraphRAG memory."""
    console.print("[bold yellow]Initiating self-evolution sequence...[/bold yellow]")
    agent = NexusAgent()
    with console.status("Scanning local workspace and optimizing memory graph...", spinner="earth"):
        stats = agent.evolve()
    console.print("[bold green]Evolution complete![/bold green]")
    console.print(f"Memory Graph updated: {stats['nodes']} nodes, {stats['edges']} edges.")


@app.command()
def status():
    """View the current status of Nexus memory, skills, and plugins."""
    agent = NexusAgent()
    mem = agent.memory.get_stats()
    skill_stats = agent.skill_tree.get_stats()
    pm = PluginManager()
    pm.load_all()
    table = Table(title="⚡ Nexus Diagnostics")
    table.add_column("Component", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Model", get_config().model.default)
    table.add_row("Graph Nodes", str(mem["nodes"]))
    table.add_row("Graph Edges", str(mem["edges"]))
    table.add_row("Custom Skills", str(skill_stats["total_skills"]))
    table.add_row("Plugins", str(len(pm.plugins)))
    console.print(table)


@app.command()
def skills():
    """List all dynamically generated skills."""
    agent = NexusAgent()
    console.print("[bold blue]Nexus Skill Tree:[/bold blue]")
    console.print(Markdown(agent.skill_tree.list_skills() or "No skills yet."))


# ── Config ──────────────────────────────────────────────────────────
@app.group()
def config():
    """Manage NexusAgent configuration."""
    pass


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = get_config()
    console.print(Markdown(f"```json\n{cfg.model_dump_json(indent=2)}\n```"))


@config.command("set")
def config_set(key: str = typer.Argument(..., help="Config key (e.g. model.default)"), value: str = typer.Argument(..., help="Config value")):
    """Set a configuration value."""
    cfg = get_config()
    parts = key.split(".")
    obj = cfg
    for part in parts[:-1]:
        obj = getattr(obj, part, None)
        if obj is None:
            console.print(f"[red]Key not found: {key}[/red]")
            raise typer.Exit(1)
    attr = parts[-1]
    old_val = getattr(obj, attr, None)
    if isinstance(old_val, bool):
        value = value.lower() in ("true", "1", "yes")
    elif isinstance(old_val, int):
        value = int(value)
    elif isinstance(old_val, float):
        value = float(value)
    setattr(obj, attr, value)
    save_config(cfg)
    console.print(f"[green]Set {key} = {value}[/green]")


@config.command("reset")
def config_reset():
    """Reset configuration to defaults."""
    from .config import DEFAULT_CONFIG_FILE
    if DEFAULT_CONFIG_FILE.exists():
        DEFAULT_CONFIG_FILE.unlink()
    console.print("[green]Configuration reset to defaults.[/green]")


# ── Web ─────────────────────────────────────────────────────────────
@app.command("web")
def web_dashboard(
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    port: int = typer.Option(8420, help="Port to bind"),
):
    """Start the web dashboard."""
    console.print(f"[bold cyan]Starting NexusAgent Dashboard on http://{host}:{port}[/bold cyan]")
    try:
        from .web import run_web
        run_web(host, port)
    except ImportError:
        console.print("[red]Install dependencies: pip install fastapi uvicorn[/red]")
        raise typer.Exit(1)


# ── Export ──────────────────────────────────────────────────────────
@app.command("export")
def export_data(
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, markdown, skillpack"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
    kind: str = typer.Option("skills", "--kind", "-k", help="What to export: skills, memory, report, all"),
):
    """Export skills, memory, or reports."""
    agent = NexusAgent()
    if format == "json":
        if kind == "memory":
            result = export_memory_graph(agent, output)
        else:
            result = export_skills_json(agent, output)
        console.print(Markdown(f"```json\n{result[:2000]}\n```"))
    elif format == "markdown":
        result = export_markdown_report(agent, output)
        console.print(Markdown(result[:3000]))
    elif format == "skillpack":
        path = export_skill_pack(agent, output or "nexus-skillpack.zip")
        console.print(f"[green]Skill pack exported to {path}[/green]")
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
        raise typer.Exit(1)


# ── Plugin ──────────────────────────────────────────────────────────
@app.group()
def plugin():
    """Manage NexusAgent plugins."""
    pass


@plugin.command("list")
def plugin_list():
    """List installed plugins."""
    pm = PluginManager()
    pm.load_all()
    plugins = pm.list_plugins()
    if not plugins:
        console.print("[yellow]No plugins installed.[/yellow]")
        return
    table = Table(title="Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Hooks", style="green")
    table.add_column("Path", style="dim")
    for p in plugins:
        table.add_row(p["name"], ", ".join(p["hooks"]) or "none", p["path"])
    console.print(table)


@plugin.command("reload")
def plugin_reload():
    """Hot-reload all plugins."""
    pm = PluginManager()
    pm.load_all()
    reloaded = pm.hot_reload()
    if reloaded:
        console.print(f"[green]Reloaded: {', '.join(reloaded)}[/green]")
    else:
        console.print("[yellow]No plugins changed.[/yellow]")


# ── Update ──────────────────────────────────────────────────────────
@app.command("update")
def update_cmd(
    skills_only: bool = typer.Option(False, "--skills", "-s", help="Only update skills from registry"),
):
    """Check for updates and optionally self-update."""
    ver = check_version()
    console.print(f"Current: [cyan]{ver['current']}[/cyan] | Latest: [cyan]{ver.get('latest', '?')}[/cyan]")
    if ver.get("update_available"):
        console.print("[yellow]A new version is available![/yellow]")
    if not skills_only:
        result = self_update()
        if result.get("success"):
            console.print("[green]Updated successfully![/green]")
        else:
            console.print(f"[red]Update failed: {result.get('error', 'unknown')}[/red]")
    skill_result = update_skills()
    if skill_result["updated"]:
        console.print(f"[green]Skills updated: {', '.join(skill_result['updated'])}[/green]")
    else:
        console.print("[dim]No skill updates available.[/dim]")


if __name__ == "__main__":
    app()


# ── Multi-Agent ────────────────────────────────────────────────────
@app.group()
def agents():
    """Multi-agent orchestration commands."""
    pass


@agents.command("register")
def agents_register(
    name: str = typer.Argument(..., help="Agent name"),
    role: str = typer.Option("general", "--role", "-r", help="Agent role: coder, reviewer, tester, planner, researcher, general"),
    model: str = typer.Option(None, "--model", "-m", help="Model override"),
):
    """Register a new agent."""
    from .multi_agent import AgentOrchestrator, AgentConfig, AgentRole
    orch = AgentOrchestrator()
    role_enum = AgentRole(role)
    config = AgentConfig(role=role_enum, model=model or get_config().model.default)
    agent = orch.register_agent(name, config)
    console.print(f"[green]Agent '{name}' registered with role '{role_enum.value}'[/green]")


@agents.command("status")
def agents_status():
    """Show multi-agent system status."""
    from .multi_agent import AgentOrchestrator
    orch = AgentOrchestrator()
    # Load any existing agents from config if needed
    status = orch.get_status()
    table = Table(title="🤖 Multi-Agent System")
    table.add_column("Agent", style="cyan")
    table.add_column("Role", style="green")
    table.add_column("Tasks Done", style="magenta")
    for name, info in status["agents"].items():
        table.add_row(name, info["role"], str(info["tasks_completed"]))
    table.add_row("Tasks", f"{status['tasks']['total']} total", f"{status['tasks']['completed']} done")
    console.print(table)

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from .agent import NexusAgent

app = typer.Typer(help="NexusAgent: The Zero-Config, Self-Evolving Local AI Agent.")
console = Console()

@app.command()
def run(
    prompt: str = typer.Argument(..., help="The task you want Nexus to perform."),
    model: str = typer.Option("ollama/llama3", help="The local model to use via LiteLLM."),
):
    """
    Run the Nexus Agent with a given task.
    """
    console.print(Panel.fit(f"[bold blue]NexusAgent[/bold blue] initialized.\nModel: [green]{model}[/green]", title="Nexus"))
    
    agent = NexusAgent(model=model)
    with console.status("[bold cyan]Nexus is thinking and consulting GraphRAG memory...[/bold cyan]", spinner="dots"):
        response = agent.execute(prompt)
    
    console.print("\n[bold green]Agent Response:[/bold green]")
    console.print(Markdown(response))

@app.command()
def evolve():
    """
    Trigger the self-evolution protocol. Scans the workspace to build GraphRAG memory.
    """
    console.print("[bold yellow]Initiating self-evolution sequence...[/bold yellow]")
    agent = NexusAgent()
    with console.status("Scanning local workspace and optimizing memory graph...", spinner="earth"):
        stats = agent.evolve()
        
    console.print("[bold green]Evolution complete![/bold green]")
    console.print(f"Memory Graph updated: {stats['nodes']} nodes, {stats['edges']} edges.")

@app.command()
def status():
    """
    View the current status of Nexus memory and skills.
    """
    agent = NexusAgent()
    memory_stats = agent.memory.get_stats()
    skill_stats = agent.skill_tree.get_stats()
    
    table = Table(title="Nexus Diagnostics")
    table.add_column("Component", style="cyan")
    table.add_column("Count", style="magenta")
    
    table.add_row("Graph Nodes", str(memory_stats["nodes"]))
    table.add_row("Graph Edges", str(memory_stats["edges"]))
    table.add_row("Custom Skills", str(skill_stats["total_skills"]))
    
    console.print(table)

@app.command()
def skills():
    """
    List all dynamically generated skills.
    """
    agent = NexusAgent()
    console.print("[bold blue]Nexus Skill Tree:[/bold blue]")
    console.print(Markdown(agent.skill_tree.list_skills()))

if __name__ == "__main__":
    app()

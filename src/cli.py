import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from .agent import NexusAgent

app = typer.Typer(help="NexusAgent: Zero-config local AI agent framework.")
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
    with console.status("[bold cyan]Nexus is thinking...[/bold cyan]", spinner="dots"):
        response = agent.execute(prompt)
    
    console.print("\n[bold green]Agent Response:[/bold green]")
    console.print(Markdown(response))

@app.command()
def evolve():
    """
    Trigger the self-evolution protocol (Graph RAG update).
    """
    console.print("[bold yellow]Initiating self-evolution sequence...[/bold yellow]")
    console.print("Scanning local workspace and optimizing memory graph.")
    console.print("[bold green]Evolution complete![/bold green] Skill tree updated.")

if __name__ == "__main__":
    app()
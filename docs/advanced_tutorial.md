# Advanced Tutorial

## Table of Contents

1. [Setting Up Multiple Models](#multiple-models)
2. [Building Custom Skills](#custom-skills)
3. [Writing Plugins](#writing-plugins)
4. [GraphRAG Memory Deep Dive](#graphrag-deep-dive)
5. [Web Dashboard](#web-dashboard)
6. [Sandboxed Execution](#sandboxed-execution)
7. [Exporting and Sharing](#exporting)
8. [Docker Deployment](#docker-deployment)
9. [Performance Optimization](#performance)
10. [Troubleshooting](#troubleshooting)

## Multiple Models

Configure different models for different tasks:

```bash
nexus config set model.default ollama/codellama
nexus run "Write a Python sorting algorithm" --model ollama/llama3
```

Or use cloud models:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
nexus run "Explain quantum computing" --model anthropic/claude-3-sonnet
```

## Custom Skills

Skills are auto-generated, but you can also create them manually:

```python
# .nexus/skills/my_calculator.py

def calculate(expression: str) -> float:
    """Evaluate a mathematical expression safely."""
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        raise ValueError("Invalid characters")
    return eval(expression)
```

## Writing Plugins

See [Plugin Guide](plugin-guide.md) for the complete plugin development guide.

## GraphRAG Deep Dive

The memory system uses NetworkX to build a knowledge graph:

- **Nodes** represent files, concepts, and entities
- **Edges** represent relationships between them
- **Retrieval** uses graph traversal to find relevant context

```python
from nexus.agent import NexusAgent

agent = NexusAgent()
agent.memory.add_node("concept:python", {"type": "concept", "importance": 0.9})
agent.memory.add_edge("concept:python", "file:main.py", {"relationship": "used_in"})
context = agent.memory.retrieve_context("How is Python used?")
```

## Web Dashboard

```bash
nexus web --port 8080
# Open http://localhost:8080
```

## Sandboxed Execution

All auto-generated skills run in a sandboxed subprocess:

```python
from nexus.sandbox import Sandbox

sandbox = Sandbox(timeout=10, max_memory_mb=128)
result = sandbox.execute("import time; time.sleep(5)")
print(result.timed_out)  # False (5s < 10s timeout)
```

## Exporting

```bash
nexus export -f json -k skills -o skills.json
nexus export -f markdown -k report -o report.md
nexus export -f skillpack -o my-skills.zip
```

## Docker Deployment

```bash
docker-compose up -d
docker-compose exec nexus-agent nexus run "Hello from Docker!"
```

## Performance Optimization

- Increase `memory.max_nodes` for larger projects
- Use `ollama/codellama` for code tasks (faster)
- Disable web dashboard when not needed
- Use `nexus plugin reload` sparingly

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Could not connect to Ollama" | Run `ollama serve` |
| Model not found | Run `ollama pull llama3` |
| Plugin not loading | Check `.nexus/plugins/` directory |
| Memory full | Increase `memory.max_nodes` |
| Slow responses | Use a smaller model or increase `max_tokens` |

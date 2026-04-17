# Plugin Guide

## Overview

NexusAgent's plugin system lets you extend the agent's behavior without modifying the core codebase. Plugins are Python files placed in `.nexus/plugins/`.

## Creating a Plugin

Create a file at `.nexus/plugins/my_plugin.py`:

```python
# .nexus/plugins/my_plugin.py

def nexus_pre_execute(prompt: str) -> str:
    """Called before the agent processes a prompt."""
    print(f"[MyPlugin] Processing: {prompt[:50]}...")
    return prompt

def nexus_post_execute(response: str) -> str:
    """Called after the agent generates a response."""
    return response

def nexus_on_skill_created(name: str, code: str) -> str:
    """Called when a new skill is created."""
    print(f"[MyPlugin] New skill: {name}")
    return code

def nexus_on_evolve(stats: dict) -> dict:
    """Called after evolution."""
    print(f"[MyPlugin] Evolution: {stats['nodes']} nodes")
    return stats
```

## Available Hooks

| Hook | Parameters | Description |
|------|-----------|-------------|
| `nexus_pre_execute` | `prompt: str` | Before agent execution |
| `nexus_post_execute` | `response: str` | After agent execution |
| `nexus_on_skill_created` | `name: str, code: str` | When a skill is created |
| `nexus_on_evolve` | `stats: dict` | After evolution |

## Managing Plugins

```bash
nexus plugin list    # List loaded plugins and their hooks
nexus plugin reload  # Hot-reload changed plugins
```

## Hot Reload

When `plugins.hot_reload` is `true` (default), NexusAgent automatically detects changes to plugin files and reloads them.

## Plugin Conventions

- Plugin files must have a `.py` extension
- Hook functions must start with `nexus_`
- Return values are passed through (modify to transform data)
- Errors in plugins are caught and logged (won't crash the agent)

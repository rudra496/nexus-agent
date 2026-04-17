# API Reference

## NexusAgent

```python
from nexus.agent import NexusAgent

agent = NexusAgent(model="ollama/llama3")
```

### Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `execute(prompt)` | `prompt: str` | `str` | Execute a task with the agent |
| `evolve()` | — | `dict` | Scan workspace and build memory graph |

## Configuration

```python
from nexus.config import load_config, save_config, NexusConfig

config = load_config()           # Load from ~/.nexus/config.yaml
config.model.default = "ollama/codellama"
save_config(config)              # Save to file
```

### NexusConfig Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `model.default` | `str` | `"ollama/llama3"` | Default model |
| `model.max_tokens` | `int` | `2048` | Max tokens per response |
| `model.temperature` | `float` | `0.7` | Model temperature |
| `memory.max_nodes` | `int` | `10000` | Max graph nodes |
| `memory.max_edges` | `int` | `50000` | Max graph edges |
| `skills.directory` | `str` | `".nexus/skills"` | Skills storage |
| `skills.sandbox_enabled` | `bool` | `True` | Enable sandbox |
| `plugins.directory` | `str` | `".nexus/plugins"` | Plugins storage |
| `plugins.hot_reload` | `bool` | `True` | Auto-reload plugins |
| `web.enabled` | `bool` | `False` | Enable dashboard |
| `web.port` | `int` | `8420` | Dashboard port |

## Plugin Manager

```python
from nexus.plugins import PluginManager

pm = PluginManager()
pm.load_all()
pm.call_hook("nexus_pre_execute", "Hello!")
plugins = pm.list_plugins()
```

## Sandbox

```python
from nexus.sandbox import Sandbox

sandbox = Sandbox(timeout=30, max_memory_mb=256)
result = sandbox.execute("print('Hello!')")
print(result.stdout)       # "Hello!"
print(result.success)      # True
```

## Export

```python
from nexus.export import export_skills_json, export_markdown_report, export_skill_pack

export_skills_json(agent, "skills.json")
export_markdown_report(agent, "report.md")
export_skill_pack(agent, "pack.zip")
```

## Updater

```python
from nexus.updater import check_version, update_skills, self_update

version_info = check_version()
update_skills()
self_update()
```

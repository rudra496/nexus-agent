# Configuration Guide

NexusAgent uses a YAML configuration file at `~/.nexus/config.yaml`, auto-created on first run.

## Default Configuration

```yaml
model:
  default: "ollama/llama3"
  fallback: null
  max_tokens: 2048
  temperature: 0.7
  api_base: "http://localhost:11434"

memory:
  max_nodes: 10000
  max_edges: 50000
  persistence_file: ".nexus/memory/graph.pkl"
  auto_save: true
  context_retrieval_limit: 5

skills:
  directory: ".nexus/skills"
  auto_evolve: true
  sandbox_enabled: true
  timeout_seconds: 30

plugins:
  directory: ".nexus/plugins"
  hot_reload: true
  allowed_extensions: [".py", ".toml"]

web:
  enabled: false
  host: "127.0.0.1"
  port: 8420

system_prompt: null
version: "0.2.0"
```

## CLI Commands

```bash
nexus config show              # View current config
nexus config set model.default ollama/codellama
nexus config set memory.max_nodes 20000
nexus config set web.enabled true
nexus config reset             # Reset to defaults
```

## Model Configuration

NexusAgent supports any model via LiteLLM:

| Provider | Format | Example |
|----------|--------|---------|
| Ollama | `ollama/<model>` | `ollama/llama3` |
| OpenAI | `openai/<model>` | `openai/gpt-4` |
| Anthropic | `anthropic/<model>` | `anthropic/claude-3-sonnet` |
| Local | `<provider>/<model>` | Any LiteLLM format |

For cloud providers, set your API key:
```bash
export OPENAI_API_KEY="sk-..."
```

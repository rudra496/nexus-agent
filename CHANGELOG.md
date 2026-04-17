# Changelog

All notable changes to NexusAgent will be documented in this file.

## [0.2.0] - 2026-04-18

### 🚀 New Features
- **Configuration Management** — YAML/JSON config with Pydantic models, `nexus config show/set/reset`
- **Plugin System** — Load external plugins from `.nexus/plugins/`, hot-reload, hook discovery
- **Web Dashboard** — FastAPI dashboard with REST API (`nexus web`)
- **Sandboxed Execution** — Subprocess isolation with timeout and memory limits
- **Export System** — JSON, Markdown reports, shareable ZIP skill packs (`nexus export`)
- **Self-Updater** — PyPI version checking, skill registry updates (`nexus update`)
- **Docker Support** — Dockerfile and docker-compose.yml

### 🧪 Testing
- Comprehensive test suite with 30+ tests across all modules
- Tests for agent, memory, skills, config, plugins, sandbox, export

### 📦 Assets
- Sample plugin (task logger) in `examples/plugins/`
- 3 starter skills in `.nexus/skills/` (log parser, CSV analyzer, code reviewer)
- Skill registry (`.nexus/registry.json`)

### 📚 Documentation
- Configuration reference (`docs/configuration.md`)
- Plugin guide (`docs/plugin-guide.md`)
- API reference (`docs/api-reference.md`)
- Roadmap (`docs/roadmap.md`)
- Expanded advanced tutorial (`docs/advanced_tutorial.md`)

### 🏗️ Infrastructure
- CI pipeline (pytest on Python 3.10, 3.11, 3.12)
- Release workflow (auto-publish to PyPI)
- CodeQL security scanning
- Dependabot for dependencies and actions
- GitHub issue templates (bug report, feature request)
- FUNDING.yml for sponsors

### 🌐 Website
- Complete rebuild with SEO optimization
- Dark/light theme toggle
- 9 feature cards, FAQ accordion, roadmap timeline, stats section
- JSON-LD structured data, Open Graph, Twitter Card meta tags

## [0.1.0] - 2026-04-17

### 🎉 Initial Release
- Core NexusAgent with GraphRAG memory (NetworkX)
- Auto skill generation from LLM responses
- CLI commands: `run`, `evolve`, `status`, `skills`
- LiteLLM multi-model support with Ollama integration
- Graceful offline fallback mode
- Basic documentation

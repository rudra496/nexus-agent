# Changelog

All notable changes to NexusAgent will be documented in this file.

## [0.2.0] - 2024-12-01

### Added
- **Plugin System** — Load external plugins from `.nexus/plugins/` with hot-reload support
- **Web Dashboard** — Optional FastAPI dashboard for monitoring skills, memory, and task history
- **Sandboxed Execution** — Isolated skill execution with subprocess isolation, timeout, and memory limits
- **Export System** — Export skills, graphs, and reports as JSON, Markdown, or shareable skill packs
- **Self-Updater** — Check for new versions, auto-update skills from a registry
- **Configuration Management** — YAML/JSON config with `nexus config` CLI commands
- **Docker Support** — Dockerfile and docker-compose.yml
- **CI/CD** — GitHub Actions for CI, release, and CodeQL security scanning
- **Website** — Full modern website with SEO, dark/light theme, and responsive design
- **Comprehensive Docs** — Configuration, plugin guide, API reference, advanced tutorial, roadmap

### Changed
- Overhauled README.md with badges, architecture diagram, comparison table
- Updated CLI with new commands: `config`, `web`, `export`, `plugin`, `update`
- Improved error handling and offline mode

## [0.1.0] - 2024-10-15

### Added
- Core NexusAgent with GraphRAG memory (NetworkX)
- Auto skill generation during runtime
- Basic CLI with `run`, `evolve`, `status`, `skills` commands
- LiteLLM integration for multi-model support
- Ollama integration for local model execution

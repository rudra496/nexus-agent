# Changelog

All notable changes to NexusAgent will be documented in this file.

## [1.0.0] - 2026-04-18

### 🎉 Production Release

### 🚀 New Features
- **Encrypted Cloud Sync** — Fernet encryption, delta sync, multi-target (local/S3/WebDAV), conflict resolution
- **Audit Logging & RBAC** — Structured JSON-lines audit log, role-based access control (admin/user/viewer), log rotation
- **Skill Marketplace** — Search, install, rate, uninstall skills by category (code-quality, data-processing, devops, research, web, security)
- **Performance Benchmark Suite** — Benchmark memory retrieval, skill execution, context building, AST parsing; compare runs across versions
- **Mobile Companion API** — REST API with JWT auth, mobile-optimized web UI, real-time task management, agent status/skills/memory endpoints
- **CLI Commands** — `nexus sync push/pull/status`, `nexus audit log/stats`, `nexus marketplace search/install/list`, `nexus benchmark run/compare`, `nexus mobile`

### 📦 Dependencies
- New optional deps: `cryptography`, `boto3`, `PyJWT`

### 🧪 Testing
- 140+ total tests across all modules
- New test suites for cloud_sync, audit, marketplace, benchmarks, mobile

### 📚 Documentation
- Updated roadmap (v1.0 all ✅)
- Added v1.1 future roadmap
- Updated website with v1.0 features
- 50 GitHub topics

## [0.4.0] - 2026-04-18

### 🚀 New Features
- **Voice Interface** — STT (Whisper local/API) + TTS (pyttsx3, edge-tts), voice conversation loop
- **AST-Aware Code Memory** — Parse functions, classes, imports, dependencies, symbol search
- **Context Window Manager** — Token budgeting, priority-based context selection, conversation truncation
- **IDE Integration** — JSON-RPC server, IDEClient for completions/diagnostics/code actions
- **VS Code Extension Template** — Manifest generator for VS Code extension
- **CLI Commands** — `nexus voice`, `nexus analyze`

### 🧪 Testing
- 90+ total tests across all modules

## [0.3.0] - 2026-04-18

### 🚀 New Features
- **Multi-Agent Orchestration** — AgentOrchestrator for managing multiple specialized agents
- **Task Delegation & Routing** — Role-based, priority-based, and load-balanced task routing
- **Collaborative Memory** — Shared graph and state accessible by all agents
- **Agent Communication** — Broadcast and direct messaging via message bus
- **Agent Roles** — Coder, reviewer, tester, planner, researcher, general
- **Priority Task Queue** — Sortable queue with configurable priorities
- **CLI Commands** — `nexus agents register`, `nexus agents status`

### 🧪 Testing
- 50+ comprehensive tests across all modules including multi-agent

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

# 🗺️ Roadmap

## v0.1 — Core Agent ✅ (Released)
- [x] GraphRAG memory with NetworkX
- [x] Auto skill generation from LLM responses
- [x] Basic CLI (`run`, `evolve`, `status`, `skills`)
- [x] LiteLLM multi-model support
- [x] Ollama integration
- [x] Graceful offline fallback mode

## v0.2 — Plugins & Dashboard ✅ (Released)
- [x] Configuration management (YAML/JSON, Pydantic models)
- [x] Plugin system with hot-reload & hook discovery
- [x] Web dashboard (FastAPI + REST API)
- [x] Sandboxed skill execution (subprocess isolation, timeout, memory limits)
- [x] Export system (JSON, Markdown reports, shareable ZIP skill packs)
- [x] Self-updater (PyPI version check, skill registry)
- [x] Docker support (Dockerfile + docker-compose)
- [x] CI/CD pipelines (test, release, CodeQL)
- [x] Comprehensive test suite (30+ tests)
- [x] Sample plugin (task logger)
- [x] Skill registry with 3 starter skills
- [x] Full documentation (config, plugins, API, tutorials)
- [x] GitHub templates (issues, PRs, funding, dependabot)

## v0.3 — Multi-Agent ✅ (Released)
- [x] Multi-agent orchestration engine (AgentOrchestrator)
- [x] Task delegation and intelligent routing (role-based, priority-based, load-balanced)
- [x] Collaborative shared memory (CollaborativeMemory with shared graph + state)
- [x] Agent communication protocol (broadcast + direct messaging via message bus)
- [x] Agent roles (coder, reviewer, tester, planner, researcher, general)
- [x] Priority-based task queue with retries
- [x] 20+ multi-agent tests

## v0.4 — Voice & IDE ✅ (Released)
- [x] Voice interface (Whisper STT + TTS with pyttsx3/edge-tts)
- [x] IDE integration base (JSON-RPC server, VS Code manifest generator)
- [x] AST-aware code memory (parse functions, classes, imports, dependencies)
- [x] Enhanced context window management (token budgeting, priority selection)
- [x] Inline code suggestions (IDEClient completion/diagnostic API)
- [x] Voice CLI command (`nexus voice`)
- [x] Code analysis CLI command (`nexus analyze`)
- [x] 40+ new tests (voice, AST, context, IDE)

## v1.0 — Production 🎯 (Target)
- [ ] Optional encrypted cloud sync
- [ ] Mobile companion app
- [ ] Enterprise features (SSO, audit logs, RBAC)
- [ ] Performance benchmarks suite
- [ ] Skill marketplace
- [ ] Comprehensive testing (>90% coverage)
- [ ] Multi-language skill support
- [ ] Plugin marketplace

## Long-term Vision 🔮
- [ ] GPU-accelerated inference integration
- [ ] Federated learning across agents
- [ ] Natural language skill creation
- [ ] Autonomous project management
- [ ] Research paper integration
- [ ] Custom fine-tuned Nexus models

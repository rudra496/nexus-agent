<div align="center">

# 🧠 NexusAgent 
### The Zero-Config, Self-Evolving Local AI Agent Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Ollama Supported](https://img.shields.io/badge/Ollama-Supported-purple.svg)](https://ollama.ai/)
[![LiteLLM Powered](https://img.shields.io/badge/LiteLLM-Powered-blue.svg)](https://github.com/BerriAI/litellm)
[![GraphRAG Memory](https://img.shields.io/badge/Memory-GraphRAG-red.svg)](#)

**[Website](https://your-username.github.io/nexus-agent)** • **[Documentation](docs/)** • **[Discord Community](#)** 

---

NexusAgent is a privacy-first, on-device AI coding agent that lives in your terminal. It understands your codebase, automates tasks, and **writes its own skills** as you use it. 

</div>

## 🌟 Why NexusAgent?

In 2026, you shouldn't have to send your proprietary code to the cloud just to get a good autonomous agent. **NexusAgent runs 100% locally**. 

- **🔒 Absolute Privacy**: No API keys, no data leaves your machine. Powered by [Ollama](https://ollama.ai) and [LiteLLM](https://github.com/BerriAI/litellm).
- **🧬 Self-Evolving (Skill Tree)**: If Nexus doesn't know how to do something, it writes the code to do it, and saves it permanently as a new custom "Skill" inside your `.nexus/skills` directory.
- **🧠 GraphRAG Memory**: Nexus doesn't just read files; it maps the relationships between them using a local `NetworkX` graph, allowing for deep contextual understanding of your workspace.
- **⚡ Zero-Config**: Drop it into any directory, type `nexus run "fix my bugs"`, and watch it work.
- **🖥️ Terminal Native**: Beautiful, rich CLI interface built with `Typer` and `Rich`.

## 🚀 Quick Start

### 1. Install Nexus
```bash
pip install nexus-agent
```

### 2. Start Ollama
Ensure you have [Ollama](https://ollama.ai/) installed and running locally with your favorite model:
```bash
ollama run llama3
```

### 3. Initialize Memory & Evolve
Let Nexus scan your current workspace and build its internal GraphRAG memory map:
```bash
nexus evolve
```

### 4. Run Your First Task
```bash
nexus run "Analyze this repository and write unit tests for the core logic"
```

## 🛠️ CLI Commands

- `nexus run "<prompt>"`: Execute a task using GraphRAG context.
- `nexus evolve`: Scan the current directory to build/update the local knowledge graph.
- `nexus status`: View diagnostics, including total memory nodes and acquired skills.
- `nexus skills`: List all the dynamic tools Nexus has written for itself.

## 🏗️ Architecture

```mermaid
graph TD
    User[User CLI] --> Nexus[Nexus Core Agent]
    Nexus --> GraphRAG[(Local NetworkX Graph Memory)]
    Nexus --> Skills[{Skill Tree Engine}]
    GraphRAG -.->|Context Injection| LiteLLM[LiteLLM Router]
    Skills -.->|Available Tools| LiteLLM
    LiteLLM --> LocalModels[Ollama / Llama3 / Phi3]
    LocalModels -.->|Code Generation| Nexus
    Nexus -.->|Saves New Skills| Skills
```

## 🤝 Contributing

We are building the future of open-source, on-device AI. We'd love your help! Check out our [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## 🛡️ Security

Your code is your code. Nexus runs locally. Read our [SECURITY.md](SECURITY.md) for more details on our sandboxing techniques.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
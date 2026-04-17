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

NexusAgent is a privacy-first, on-device AI coding agent that lives in your terminal. It understands your codebase, automates complex tasks, and **writes its own skills** as you use it. 

</div>

## 🌟 Why NexusAgent?

In 2026, you shouldn't have to send your proprietary code to the cloud just to get a good autonomous agent. **NexusAgent runs 100% locally**. 

- **🔒 Absolute Privacy**: No API keys, no telemetry, no data leaves your machine. Powered by [Ollama](https://ollama.ai) and [LiteLLM](https://github.com/BerriAI/litellm).
- **🧬 Self-Evolving (Skill Tree)**: If Nexus doesn't know how to do something, it writes the code to do it, and saves it permanently as a new custom "Skill" inside your `.nexus/skills` directory.
- **🧠 GraphRAG Memory**: Nexus doesn't just read files; it maps the relationships between them using a local `NetworkX` graph, allowing for deep contextual understanding of your workspace.
- **⚡ Zero-Config**: Drop it into any directory, type `nexus run "fix my bugs"`, and watch it work.
- **🖥️ Terminal Native**: Beautiful, rich CLI interface built with `Typer` and `Rich`.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10 or higher
- [Ollama](https://ollama.ai/) installed and running locally

### 2. Install Nexus
```bash
pip install nexus-agent
```

### 3. Start Ollama
Ensure you have Ollama running locally with your favorite model (we recommend `llama3` or `phi3` for coding tasks):
```bash
ollama run llama3
```
*Note: Nexus connects to `http://localhost:11434` by default.*

### 4. Initialize Memory & Evolve
Navigate to any project directory and let Nexus scan your workspace to build its internal GraphRAG memory map:
```bash
cd my-awesome-project
nexus evolve
```

### 5. Run Your First Task
```bash
nexus run "Analyze this repository and write unit tests for the core logic"
```

---

## 🛠️ CLI Commands & Usage

Nexus provides a suite of CLI commands to manage your AI agent.

### `nexus run "<prompt>"`
Execute a task using the current context and available skills.
```bash
# Example: Refactoring code
nexus run "Refactor src/auth.py to use async/await and update all dependent files."

# Example: Generating documentation
nexus run "Read the current workspace and generate a comprehensive API reference in Markdown."
```

### `nexus evolve`
Scans the current directory (ignoring `.git`, `.nexus`, etc.) to build or update the local knowledge graph. Run this whenever you make significant structural changes to your codebase.
```bash
nexus evolve
```

### `nexus status`
View diagnostics, including total memory nodes mapped by GraphRAG and the number of acquired skills.
```bash
nexus status
```

### `nexus skills`
List all the dynamic tools Nexus has written for itself in the `.nexus/skills` directory.
```bash
nexus skills
```

---

## 🧠 Core Features Deep Dive

### 1. GraphRAG Memory
Traditional agents just grep for files. Nexus builds a semantic graph of your project. When you ask a question, it retrieves not just the target file, but its dependencies, imports, and logical connections. This keeps the LLM context window small, fast, and highly relevant.

### 2. The Skill Tree Engine
When Nexus encounters a task it lacks a tool for, it generates one on the fly. For instance, if you ask it to "parse system logs," and it doesn't have a parser, it writes a robust Python script, tags it `[NEW SKILL: parse_logs]`, and saves it permanently. Next time you ask, it uses the optimized tool instead of re-writing code.

### 3. Model Agnostic via LiteLLM
While optimized for local Ollama models, Nexus uses LiteLLM under the hood. You can seamlessly switch to other local providers (like vLLM, LM Studio) or even cloud providers if you choose to override the local-only default.

---

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

---

## 💡 Best Practices

1. **Be Specific**: While Nexus is smart, specific prompts like "Create a Python script that parses CSV files in data/ and outputs a JSON summary" work better than "Summarize data".
2. **Evolve Often**: Run `nexus evolve` after adding new dependencies or major structural changes so the GraphRAG memory stays fresh.
3. **Review Skills**: Occasionally check your `.nexus/skills` folder. You can manually edit the Python files Nexus generates to refine its capabilities!

---

## 🤝 Contributing

We are building the future of open-source, on-device AI. We'd love your help! Check out our [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

### Development Setup
```bash
git clone https://github.com/your-username/nexus-agent.git
cd nexus-agent
pip install -r requirements.txt
python setup.py develop
```

## 🛡️ Security

Your code is your code. Nexus runs locally. Read our [SECURITY.md](SECURITY.md) for more details on our sandboxing techniques.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

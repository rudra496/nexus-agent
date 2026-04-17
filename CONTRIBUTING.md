# Contributing to NexusAgent

Thank you for your interest in contributing! This guide will help you get started.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/<your-username>/nexus-agent.git`
3. **Install** in dev mode: `pip install -e ".[dev]"`
4. **Run tests**: `pytest tests/ -v`

## Development Setup

```bash
git clone https://github.com/rudra496/nexus-agent.git
cd nexus-agent
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Code Style

- **Formatter**: Black (`black src/ tests/`)
- **Linter**: Ruff (`ruff check src/ tests/`)
- **Types**: mypy (`mypy src/`)
- **Line length**: 100 characters
- **Python**: 3.10+

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with tests
3. Run the full check suite: `ruff check src/ && mypy src/ && pytest`
4. Commit with conventional commits: `feat: add new plugin hook`
5. Push and open a PR against `main`

### PR Template

```markdown
## Description
Brief description of changes.

## Type
- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Refactor

## Testing
- [ ] Unit tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows project style
- [ ] Self-review completed
- [ ] Documentation updated
```

## Reporting Issues

Please use the [issue templates](.github/ISSUE_TEMPLATE/) when reporting bugs or requesting features.

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help others when you can
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

## Questions?

Open a [discussion](https://github.com/rudra496/nexus-agent/discussions) or reach out to [@Rudra496](https://x.com/Rudra496).

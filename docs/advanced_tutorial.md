# Advanced NexusAgent Tutorials

## 1. The Skill Tree Ecosystem

By default, Nexus has no hard-coded tools. Instead, it generates Python snippets at runtime and stores them in `.nexus/skills/`.

### Example Scenario
You ask Nexus: `"Create a script to parse my system logs and find error rates."`

1. Nexus searches its GraphRAG memory and realizes it has no `log_parser` skill.
2. It writes a robust `log_parser.py` snippet and outputs it with the tag `[NEW SKILL: parse_logs]`.
3. Nexus intercepts this tag, saves the code into `.nexus/skills/parse_logs.json`.
4. The next time you ask about logs, Nexus injects this custom skill into its context window, executing your proprietary code perfectly.

## 2. GraphRAG Memory Architecture

When you run `nexus evolve`, the agent walks your entire directory structure. It builds a `NetworkX` graph:
- **Nodes**: Represent files, classes, and functions.
- **Edges**: Represent imports, dependencies, and logical connections.

This means if you ask `"Why is the auth module failing?"`, Nexus retrieves the exact file, *plus* the 3 other files that import it, giving the local LLM the perfect context window without blowing up your token limits.

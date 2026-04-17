# Advanced NexusAgent Tutorials

Welcome to the advanced tutorials for NexusAgent! This guide goes beyond basic setup and dives deep into the inner workings of Nexus's core features: **The Skill Tree Ecosystem** and **GraphRAG Memory Architecture**. By mastering these, you can extend Nexus to perform highly complex and proprietary tasks without ever leaving your terminal.

---

## 1. The Skill Tree Ecosystem

By default, Nexus is born with a minimal set of tools. It relies on its **Skill Tree Engine** to generate Python snippets dynamically at runtime and stores them permanently in your local workspace under `.nexus/skills/`.

### How It Works

1. **Task Analysis**: When you issue a prompt, Nexus evaluates if it currently possesses the tools to execute the task efficiently.
2. **Code Generation**: If a tool is missing, Nexus uses the local LLM to write a robust Python script to accomplish the task.
3. **Skill Registration**: The agent tags its output with `[NEW SKILL: skill_name]`. The internal parser intercepts this tag and saves the code snippet into `.nexus/skills/<skill_name>.json`.
4. **Future Execution**: On subsequent requests requiring similar functionality, Nexus retrieves the skill from the tree, drastically reducing response time and avoiding redundant code generation.

### Example Scenario

You ask Nexus: 
> *"Create a script to parse my Nginx system logs and find the top 5 error rates by IP."*

1. Nexus searches its GraphRAG memory and realizes it has no `nginx_log_parser` skill.
2. It writes a robust `nginx_log_parser.py` snippet and outputs it with the tag `[NEW SKILL: parse_nginx_logs]`.
3. Nexus intercepts this tag and saves the code into `.nexus/skills/parse_nginx_logs.json`.
4. The next time you ask, *"Analyze yesterday's Nginx logs"*, Nexus injects this custom skill into its context window, executing your proprietary code perfectly.

### Manually Managing Skills

Because skills are just JSON files containing Python code, you can easily version control, share, or edit them:

- **Edit a Skill**: Open `.nexus/skills/parse_nginx_logs.json` and tweak the Python snippet to improve performance. Nexus will use the updated code on the next run.
- **Share Skills**: You can commit the `.nexus/skills` directory to your repository, allowing your entire team to benefit from the custom tools Nexus has developed for your specific project.

---

## 2. GraphRAG Memory Architecture

When you run `nexus evolve`, the agent doesn't just do a simple string search across your files. It builds a complex **NetworkX graph** to understand the semantic relationships within your codebase.

### Graph Components

- **Nodes**: Represent individual files, classes, functions, and key data structures.
- **Edges**: Represent relationships like `IMPORTS`, `INHERITS_FROM`, `CALLS`, and `DEPENDS_ON`.

### Why GraphRAG beats Traditional RAG

Traditional Retrieval-Augmented Generation (RAG) relies on vector embeddings and chunking, which often loses context across file boundaries. 

If you ask: *"Why is the user authentication module failing?"*

- **Traditional RAG** might retrieve `auth.py` and maybe a random file that mentions "authentication", missing the actual root cause.
- **GraphRAG (Nexus)** retrieves `auth.py`, traverses the graph to find that `auth.py` depends on `database.py` (which recently had a schema change), and pulls both files into the LLM context.

This targeted retrieval gives the local LLM the perfect context window without blowing up token limits or confusing the model with irrelevant files.

### Forcing a Memory Update

Nexus updates its memory incrementally, but if you've done a massive refactor (e.g., renaming directories, changing architectural patterns), you should force a clean rebuild:

```bash
# Clear the existing graph database
rm -rf .nexus/memory/

# Rebuild the graph from scratch
nexus evolve
```

---

## 3. Customizing the Local LLM (LiteLLM Integration)

Nexus is powered by [LiteLLM](https://github.com/BerriAI/litellm) under the hood. While it defaults to `ollama/llama3`, you can configure it to use any model.

To switch models, you can export the following environment variable before running Nexus:

```bash
# Use a different local Ollama model
export NEXUS_MODEL="ollama/phi3"

# Or, if you want to use a cloud provider (requires API keys)
export NEXUS_MODEL="gpt-4o"
export OPENAI_API_KEY="sk-..."
```

*Note: While cloud models are supported, we highly recommend using local models to maintain the absolute privacy guarantees of NexusAgent.*

---

## Next Steps

- Explore the [API Documentation](index.html) for detailed class and function references.
- Join the community to share your custom Skill Trees!
